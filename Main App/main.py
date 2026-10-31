import logging
import os
import time

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from streamlit_webrtc import WebRtcMode, webrtc_streamer

from services.auth.login_wall import render_login_wall
from services.config.workout_config import EXERCISE_OPTIONS
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech
from services.coaching.voice_pipeline import VoicePipeline, autoplay_audio
from services.persistence.exercise_repository import (
    get_users_exercises,
    init_db,
)
from services.state.session_defaults import initial_session_defaults
from services.tracking.metrics import sync_metrics_update
from services.ui.style_loader import (
    inject_local_font,
    inject_webrtc_styles,
    load_css,
)
from services.vision.exercise_video_processor import VideoProcessorClass

logger = logging.getLogger(__name__)


def _get_groq_api_key() -> str:
    """Read the optional Groq key from environment or Streamlit secrets."""
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if key:
        return key

    try:
        return str(st.secrets.get("GROQ_API_KEY", "")).strip()
    except Exception:
        # Missing local secrets.toml is normal when AI coaching is not configured.
        return ""


def _initialize_voice_pipeline() -> None:
    """Initialize optional AI coaching without blocking the core workout app."""
    if "voice_pipeline" in st.session_state:
        return

    api_key = _get_groq_api_key()
    if not api_key:
        st.session_state.voice_pipeline = None
        return

    try:
        client = Groq(api_key=api_key)
        st.session_state.voice_pipeline = VoicePipeline(
            LLMCoach(client),
            TextToSpeech(),
        )
    except Exception:
        logger.exception("Could not initialize the optional AI voice coach.")
        st.session_state.voice_pipeline = None


def main() -> None:
    # Load Main App/.env when Streamlit is launched from this directory.
    load_dotenv()

    st.set_page_config(
        page_icon="🏋️",
        page_title="AI Gym Coach | Avdhoot Ukirde",
        initial_sidebar_state="expanded",
        layout="centered",
    )

    app_dir = os.path.dirname(os.path.abspath(__file__))
    load_css(os.path.join(app_dir, "static", "style.css"))
    inject_local_font(
        os.path.join(app_dir, "static", "AdobeClean.otf"),
        "AdobeClean",
    )

    init_db()

    if not render_login_wall():
        return

    initial_session_defaults()
    _initialize_voice_pipeline()

    workout_started = st.session_state.get("workout_started", False)

    with st.sidebar:
        st.title("🏋️ Apna AI Coach")

        username = st.session_state.get("username")
        if username:
            st.caption(f"👤 Workout profile: {username}")

        st.divider()
        st.subheader("Workout Plan")

        if not workout_started:
            plan_exercise = st.selectbox(
                "Exercise",
                options=EXERCISE_OPTIONS,
                key="plan_exercise",
            )
            plan_sets = st.number_input(
                "Sets",
                min_value=1,
                max_value=50,
                key="plan_sets",
                step=1,
            )
            plan_reps = st.number_input(
                "Reps per Set",
                min_value=1,
                max_value=50,
                key="plan_reps",
                step=1,
            )

            if st.button(
                "Start Workout",
                width="stretch",
                key="start_session_button",
            ):
                st.session_state.exercise_type = plan_exercise
                st.session_state.target_sets = int(plan_sets)
                st.session_state.reps_per_set = int(plan_reps)
                st.session_state.reps = 0
                st.session_state.sets_completed = 0
                st.session_state.current_set_reps = 0
                st.session_state.workout_complete = False
                st.session_state.workout_started = True
                st.session_state.set_cycle_started_at = time.time()
                st.session_state.last_saved_sets_completed = 0
                st.session_state.last_notified_workout_complete = False

                pipeline = st.session_state.get("voice_pipeline")
                if pipeline:
                    result = pipeline.process_event(
                        event="workout_started",
                        exercise=plan_exercise,
                        metrics={},
                    )
                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result

                st.rerun()
        else:
            exercise = st.session_state.get("exercise_type", "Workout")
            sets = st.session_state.get("target_sets", 0)
            reps_per_set = st.session_state.get("reps_per_set", 0)
            st.info(f"**{exercise}** — {sets} sets × {reps_per_set} reps")

            if st.button("End Workout", key="end_session_button", width="stretch"):
                pipeline = st.session_state.get("voice_pipeline")
                if pipeline:
                    result = pipeline.process_event(
                        event="workout_completed",
                        exercise=exercise,
                        metrics={},
                    )
                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result

                st.session_state.workout_started = False
                st.rerun()

        if workout_started:
            st.divider()
            exercise = st.session_state.get("exercise_type")
            st.subheader("Progress")
            st.metric("Total Reps", st.session_state.get("reps", 0))
            st.metric(
                "Current Set Reps",
                f"{st.session_state.get('current_set_reps', 0)} / "
                f"{st.session_state.get('reps_per_set', 0)}",
            )
            st.metric(
                "Sets Completed",
                f"{st.session_state.get('sets_completed', 0)} / "
                f"{st.session_state.get('target_sets', 0)}",
            )

            metric_labels = {
                "Squats": [
                    ("Knee Angle", "knee_angle", "°"),
                    ("Back Angle", "back_angle", "°"),
                    ("Depth Status", "depth_status", ""),
                ],
                "Push-ups": [
                    ("Elbow Angle", "elbow_angle", "°"),
                    ("Body Alignment", "body_alignment", ""),
                    ("Hip Position", "hip_status", ""),
                ],
                "Biceps Curls (Dumbbell)": [
                    ("Elbow Angle", "elbow_angle", "°"),
                    ("Shoulder Stability", "shoulder_status", ""),
                    ("Swing Detection", "swing_status", ""),
                ],
                "Shoulder Press": [
                    ("Elbow Angle", "elbow_angle", "°"),
                    ("Arm Extension", "extension_status", ""),
                    ("Back Arch", "back_arch_status", ""),
                ],
                "Lunges": [
                    ("Front Knee Angle", "front_knee_angle", "°"),
                    ("Torso Angle", "torso_angle", "°"),
                    ("Balance Status", "balance_status", ""),
                ],
            }

            for label, key, suffix in metric_labels.get(exercise, []):
                st.metric(label, f"{st.session_state.get(key, 'N/A')}{suffix}")

    st.title("AI Gym Coach")
    st.markdown(
        "#### Real-time exercise tracking with MediaPipe pose estimation"
    )
    st.caption(
        "Maintained by Avdhoot Ukirde · Streamlit · MediaPipe · OpenCV"
    )

    if not _get_groq_api_key():
        st.info(
            "AI voice coaching is optional and currently disabled. "
            "Set GROQ_API_KEY to enable generated coaching and speech. "
            "Exercise tracking works without it."
        )

    if st.session_state.get("audio_to_play"):
        autoplay_audio(st.session_state.audio_to_play)

    if st.session_state.get("coach_feedback"):
        st.success(f"🤖 **Coach:** {st.session_state.coach_feedback}")

    if not workout_started:
        st.markdown(
            """
            <div style="
                border: 1px dashed #777;
                padding: 40px 28px;
                text-align: center;
                color: #aaa;
                margin: 28px 0;
            ">
                <h2 style="color:#eee; margin-bottom:8px;">
                    Plan your workout in the sidebar
                </h2>
                <p>
                    Choose an exercise, set a target, and start the session
                    to activate live camera-based pose analysis.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        context = webrtc_streamer(
            key="exercise-analysis",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=VideoProcessorClass,
            rtc_configuration={
                "iceServers": [
                    {"urls": ["stun:stun.l.google.com:19302"]}
                ]
            },
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

        sync_metrics_update(context)

        if context.state.playing:
            time.sleep(0.25)
            st.rerun()

        inject_webrtc_styles()

    st.divider()
    st.markdown("#### Workout History")

    user_id = st.session_state.get("user_id")
    if isinstance(user_id, int):
        history_rows = get_users_exercises(user_id)
        history = [
            {
                "Exercise": row["exercise_name"],
                "Reps": row["reps"],
                "Sets": row["sets"],
                "Time (sec)": row["time"],
                "Date": row["created_at"],
            }
            for row in history_rows
        ]
        history_df = pd.DataFrame(history)

        if not history_df.empty:
            history_df["Date"] = pd.to_datetime(
                history_df["Date"]
            ).dt.date
            summary = (
                history_df.groupby(["Exercise", "Date"])
                .agg(
                    {
                        "Reps": "sum",
                        "Sets": "sum",
                        "Time (sec)": "sum",
                    }
                )
                .reset_index()
                .sort_values("Date", ascending=False)
            )
            st.dataframe(summary, use_container_width=True, hide_index=True)
        else:
            st.info("No workout history yet. Complete a set to save progress.")


if __name__ == "__main__":
    main()
