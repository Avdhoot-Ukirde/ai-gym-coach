import logging
import time

import streamlit as st

logger = logging.getLogger(__name__)


class VoicePipeline:
    def __init__(self, llm, tts):
        self.llm = llm
        self.tts = tts
        self.last_spoken_at = 0

    def _find_form_issue(self, exercise, metrics):
        if "issue" in metrics:
            return metrics["issue"]

        if exercise == "Squats":
            depth = metrics.get("depth_status", "")
            back_angle = metrics.get("back_angle", 180)
            if depth == "TOO HIGH":
                return "Your squat is not deep enough; bend your knees further."
            if isinstance(back_angle, (int, float)) and back_angle < 130:
                return "You are leaning too far forward during the squat."

        elif exercise == "Push-ups":
            alignment = metrics.get("body_alignment", "")
            hip_status = metrics.get("hip_status", "")
            if alignment == "Poor Form":
                return "Keep your body aligned in a straight line during the push-up."
            if hip_status == "SAGGING":
                return "Your hips are sagging; engage your core and keep them level."
            if hip_status == "PIKED UP":
                return "Lower your hips to maintain a straight body line."

        elif exercise == "Biceps Curls (Dumbbell)":
            if metrics.get("swing_status") == "SWINGING":
                return "Avoid swinging your torso; keep the movement controlled."
            if metrics.get("shoulder_status") == "ELBOW DRIFTING":
                return "Keep your elbow closer to your side during the curl."

        elif exercise == "Shoulder Press":
            back_arch = metrics.get("back_arch_status", "")
            if back_arch == "Excessive Arch":
                return "Brace your core and avoid arching your lower back."
            if back_arch == "Slight Arch":
                return "Brace your core to keep your back in a neutral position."

        elif exercise == "Lunges":
            if metrics.get("balance_status") == "OFF BALANCE":
                return "Slow down and regain your balance before the next lunge."

        return None

    def process_event(self, event, exercise, metrics):
        issue = self._find_form_issue(exercise, metrics)
        now = time.time()

        major_events = {
            "workout_started",
            "set_completed",
            "workout_completed",
        }

        if event not in major_events:
            if not issue or now - self.last_spoken_at < 5:
                return None

        try:
            feedback = self.llm.give_feedback(event, issue)
        except Exception:
            logger.exception("Groq coaching request failed.")
            return None

        if not feedback:
            return None

        try:
            audio = self.tts.speak(feedback)
        except Exception:
            logger.exception("Text-to-speech request failed.")
            audio = None

        self.last_spoken_at = now
        return audio, feedback


def autoplay_audio(audio_bytes):
    if not audio_bytes:
        return

    st.markdown(
        "<style>[data-testid='stAudio'] {display: none;}</style>",
        unsafe_allow_html=True,
    )
    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
