import streamlit as st
import pandas as pd
import numpy as np
import random 

st.title("Collatz Conjecture")

# Initialize session state 
if "value" not in st.session_state:
    st.session_state.value = None
    st.session_state.started = False
    button_label = "Start"
else:
    if st.session_state.value is 1:
        button_label = "Success!"
    else:
        if st.session_state.value % 2 == 0:
            button_label = "Half it"
        else:
            button_label = "Triple it and add one"
    
# Button label depending on state
st.button(button_label, disabled=st.session_state.value is 1)

# Output
if not st.session_state.started:
    st.write("Ready")
else:
    st.write(st.session_state.value)

if not st.session_state.started:
    st.session_state.value = random.randint(1, 100)
    st.session_state.started = True
else:
    if st.session_state.value % 2 == 0:
        st.session_state.value //= 2
    else:
        st.session_state.value = 3 * st.session_state.value + 1

