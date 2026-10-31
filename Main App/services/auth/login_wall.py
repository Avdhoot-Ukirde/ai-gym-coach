import streamlit as st

from services.persistence.exercise_repository import get_or_create_user


def render_login_wall():
    if st.session_state.get("user_id") is not None:
        return True

    st.title("🏋️ AI Gym Coach")
    st.markdown("### Create or reopen a local workout profile.")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input(
            "Username",
            max_chars=32,
            placeholder="Enter a username",
        )
        submit_button = st.form_submit_button(
            "Start Session",
            width="stretch",
        )

    if submit_button:
        normalized_username = (username or "").strip()
        if not normalized_username:
            st.error("Please enter a username.")
            return False

        try:
            user = get_or_create_user(normalized_username)
        except Exception:
            st.error("Could not open this workout profile. Please try again.")
            return False

        st.session_state["user_id"] = user["id"]
        st.session_state["username"] = user["username"]
        st.rerun()

    st.caption(
        "This is a simple local profile selector, not password-protected authentication."
    )
    return False
