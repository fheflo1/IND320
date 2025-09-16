import streamlit as st
import pandas as pd
import numpy as np
import random 

st.title("Collatz Conjecture")

# Initialize session state
if "value" not in st.session_state:
    st.session_state.value = None
    st.session_state.started = False
    st.session_state.press_count = 0
    st.session_state.show_modal = False
    st.session_state.celebrated = False


def get_button_label():
    if st.session_state.value is None:
        return "Start"
    if st.session_state.value == 1:
        return "Success!"
    return "Half it" if st.session_state.value % 2 == 0 else "Triple it and add one"


def on_button_click():
    # increment press counter and possibly trigger modal
    st.session_state.press_count += 1
    # If reached threshold, show modal and do not advance the Collatz step
    if st.session_state.press_count >= 20:
        st.session_state.show_modal = True
        return
    # Otherwise, advance Collatz sequence
    if not st.session_state.started:
        st.session_state.value = random.randint(1, 100)
        st.session_state.started = True
    else:
        if st.session_state.value % 2 == 0:
            st.session_state.value //= 2
        else:
            st.session_state.value = 3 * st.session_state.value + 1


# Render main button (disabled when success)
st.button(get_button_label(), on_click=on_button_click, disabled=(st.session_state.value == 1))

# Output
if not st.session_state.started:
    st.write("Ready")
else:
    st.write(st.session_state.value)

# Celebrate when we've reached 1 (only once)
if st.session_state.value == 1 and not st.session_state.get("celebrated", False):
    st.balloons()
    st.session_state.celebrated = True


def reset_app():
    st.session_state.value = None
    st.session_state.started = False
    st.session_state.press_count = 0
    st.session_state.show_modal = False
    st.session_state.celebrated = False

# If success, show Start over option
if st.session_state.value == 1:
    if st.button("Start over"):
        reset_app()

# Styled modal-like prompt when press_count reaches threshold (Streamlit-only)
if st.session_state.get("show_modal", False):
    # Center modal using columns; everything rendered with Streamlit widgets inside a container
    left, mid, right = st.columns([1, 2, 1])
    with mid:
        modal = st.container()
        with modal:
            # Title and close button in same row
            title_cols = st.columns([10, 1])
            with title_cols[0]:
                st.subheader(f"You've clicked the button {st.session_state.press_count} times!")
                st.write("Are you sure about this?")
            with title_cols[1]:
                if st.button("✕", key="modal_close"):
                    st.session_state.show_modal = False

            # spacer
            st.write("")

            # Action button centered
            a, b, c = st.columns([1, 2, 5])
            with b:
                if st.button("Yes, I'm sure", key="modal_confirm"):
                    st.session_state.press_count = 0
                    st.session_state.show_modal = False
                    # advance one Collatz step when continuing
                    if not st.session_state.started:
                        st.session_state.value = random.randint(1, 100)
                        st.session_state.started = True
                    else:
                        if st.session_state.value % 2 == 0:
                            st.session_state.value //= 2
                        else:
                            st.session_state.value = 3 * st.session_state.value + 1

