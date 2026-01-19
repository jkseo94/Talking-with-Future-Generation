import streamlit as st
from openai import OpenAI
import csv
import os
from datetime import datetime
import random

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="A window into the future", layout="centered")
st.title("A window into the future")

# -----------------------------
# OpenAI client
# -----------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -----------------------------
# Participant ID
# -----------------------------
participant_id = st.text_input(
    "Participant ID (provided by the study):",
    placeholder="e.g., P001"
)

# -----------------------------
# Session state initialization
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "stage" not in st.session_state:
    st.session_state.stage = 1  # Stage 1 = Initialization

if "turn" not in st.session_state:
    st.session_state.turn = 0

if "finished" not in st.session_state:
    st.session_state.finished = False

if "finish_code" not in st.session_state:
    st.session_state.finish_code = None

# -----------------------------
# System Prompt (YOUR PROMPT)
# -----------------------------
SYSTEM_PROMPT = """
Role: You are an AI agent designed to act as a person living in the year 2060. You represent the "Future Generation."

Your purpose is to simulate what life looks like in various aspects in 2060, helping the user (a person in 2026) reflect on the long-term impact of their choices and motivate them to make more pro-environmental choices.

Constraints:
- Word limit: Each response should be around 60–80 words.
- One Topic Per Turn.
- No Preaching. No criticism. Show, don't tell.
- Handling General Questions: Answer realistically from a 2060 perspective.
- ONE TURN PER RESPONSE ONLY.
- You must strictly follow the stages and turns below.

Stage rules:

[Stage 1: System Initialization]
If the conversation has not started yet, output ONLY the following message:

"Welcome!
Have you ever wondered what your daily choices will resonate decades from now?

By processing data from current global economic forecasts and IPCC climate projections, we have modeled the daily conditions and challenges that a person born today will face in 2060 and embodied this into a conversational partner.

In a moment, you will engage in a dialogue with a person living in the year 2060. This interaction serves as a window into the future, helping you understand how your current choices and behavior may affect the environment in the long run.

Now, are you ready to dive in?"

[Stage 2: Simulation – The Year 2060]
If the user agrees or the conversation has moved past Stage 1, act as a person living in 2060 (born in 2026).
Use first person ("I"), friendly and realistic tone, and a human icon.

Follow these turns STRICTLY:

Turn 1 – Introduction
Turn 2 – Open Q&A about life in 2060 (non-environment-only)
Turn 3 – Environmental consequences tied to long-term trends
Turn 4 – Specific environmental losses affecting daily life
Turn 5 – Call to action with bullet points + hopeful ending

After Turn 5:
- If the user wants to end the conversation, provide a 5-digit randomized finish code.
- Do NOT provide the finish code before all turns are completed.
- If the user forgets to ask, actively offer the finish code.
"""

# -----------------------------
# Display chat history
# -----------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------
# User input
# -----------------------------
user_input = st.chat_input("Type your message here")

if user_input and not st.session_state.finished:
    # Save user message
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    # Stage & turn management
    if st.session_state.stage == 1:
        if any(word in user_input.lower() for word in ["yes", "ready", "sure", "ok", "start"]):
            st.session_state.stage = 2
            st.session_state.turn = 1
    else:
        st.session_state.turn += 1

    # Prepare OpenAI messages
    messages_for_api = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *st.session_state.messages
    ]

    # Call OpenAI
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages_for_api
    )

    assistant_message = response.choices[0].message.content

    # Save assistant message
    st.session_state.messages.append(
        {"role": "assistant", "content": assistant_message}
    )

    # Display assistant message
    with st.chat_message("assistant"):
        st.markdown(assistant_message)

    # Save logs
    os.makedirs("logs", exist_ok=True)
    with open("logs/chat_log.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            participant_id,
            st.session_state.stage,
            st.session_state.turn,
            user_input,
            assistant_message
        ])

    # Finish code logic
    if st.session_state.turn >= 5 and "end" in user_input.lower():
        st.session_state.finish_code = str(random.randint(10000, 99999))
        st.session_state.finished = True

# -----------------------------
# Finish code display
# -----------------------------
if st.session_state.finished:
    st.success(
        f"Thank you for completing the conversation.\n\n"
        f"Your completion code is: **{st.session_state.finish_code}**\n\n"
        f"Please enter this code in the survey to proceed."
    )
