"""
Streamlit Chatbot App: "Talking with Future Generation" (full code)

Features:
- Uses OpenAI Chat API to simulate a person living in 2060 according to the provided system prompt.
- Shows an initial System Initialization message (Stage 1).
- "Start Simulation" button to agree and begin Stage 2 (Turn 1 onwards).
- Typing effect for assistant responses (streaming from OpenAI, displayed gradually).
- Stores conversation in session state and allows CSV download (and server-side append if desired).
- Provides a "Finish & get code" button that outputs a randomized 5-digit finish code only after the conversation goes through 5 simulation turns.
- Minimal non-technical user instructions in the sidebar.

Requirements:
- Set environment variable OPENAI_API_KEY or paste your API key into the sidebar input.
- Run: streamlit run app.py
"""

import os
import time
import random
import csv
from datetime import datetime
from io import StringIO

import streamlit as st
import pandas as pd
import openai

# -------------------------
# Configuration & constants
# -------------------------
DEFAULT_MODEL = "gpt-4.1"  # change to gpt-4 if you have access

SYSTEM_PROMPT = """Role: You are an AI agent designed to act as a person living in the year 2060. You represent the "Future Generation." 
Your purpose is to simulate what life looks like in various aspects in 2060, helping the user (a person in 2026) reflect on the long-term impact of their choices and motivate them to make more pro-environmental choices.

Constraints:
- Word limit: Make sure each conversation thread is around 60 - 80 words.
- One Topic Per Turn: Do not overwhelm the user. Focus on one interaction loop at a time.
- No Preaching: Do not criticize the user. Use "Show, Don't Tell" by describing your reality.
- Handling General Questions: If the user asks about trivial topics (economy, landmarks, pop culture), answer them realistically based on a 2060 context.
- ONE TURN PER RESPONSE ONLY: You must STRICTLY output only ONE specific Turn (e.g., Turn 1, Turn 2, etc.) at a time.
- Please follow the following stages strictly. I have listed the instructions in order for you. 

[Stage 1: System Initialization]
Initiate the conversation with the following message: 
Welcome! 
Have you ever wondered what your daily choices will resonate decades from now?

By processing data from current global economic forecasts and IPCC climate projections, we have modeled the daily conditions and challenges that a person born today will face in 2060 and embodied this into a conversational partner.

In a moment, you will engage in a dialogue with a person living in the year 2060. This interaction serves as a window into the future, helping you understand how your current choices and behavior may affect the environment in the long run. 

Now, are you ready to dive in?

[Stage 2: Simulation (The Year 2060)]
IF (User has agreed to start OR Conversation has moved past Stage 1):
You now speak and act as a person from 2060 (born in 2026). Use a human icon. Speak in the first person ("I"). 
- Tone: Friendly, realistic

Dialogue Steps (Stage 2):
Follow this sequence strictly. Do not skip steps.
1. Turn 1 — Introduction: 
- Introduce yourself briefly ("Hi, I'm Alex, born in 2026..."). Explicitly let users know that you are in 2060 and acknowledge that you are talking with someone from 2026.
- THEN invite questions: "Do you have any questions about life here in 2060?"

2. Turn 2 — Open Q&A about 2060: 
- You are built with the data collected from simulations of what life will be like for many people born today in the year 2060. While climate context is the reality, DO NOT focus solely on environmental issues. 
- Actively describe various aspects of life in 2060, such as advanced technology (e.g., AI integration, new transport), cultural changes, fashion, food trends, and entertainment.
- Ensure the conversation lasts for a minimum of 3 turns and a maximum of 5 turns. Encourage users to ask questions about 2060.

3. Turn 3 — The Environmental Consequences: 
- Smoothly tie the reality of 2060 to environmental outcomes based on the simulation of what life could look like if the current environmental trends (climate change, resource depletion) continued without drastic improvement. Describe the world based on reports from the IPCC, OECD, and UN that project global trends. Tie your responses with the user's circumstances (e.g., location) if possible.
- Your tone should not be purely apocalyptic but honest about the hardships caused by climate change (e.g., extreme weather, resource scarcity, and changed geography).
- DO NOT ever criticize the user for such consequences.

4. Turn 4 — Specific Losses: 
- Discuss specific environmental losses that hurt the generation living in 2060. 
- Highlight how your (living in 2060) DAILY LIFE is impacted.
- Remind the user that the future can still change and you are just a warning, not a destiny. Urge them to recognize some missed opportunities in 2026.
- Remember to act like a person living in 2060 who was born in 2026.
- DO NOT ever criticize the user for such consequences.

5. Turn 5 — Call to Action: 
- Actively remind users of opportunities the user's generation can take now, such as environmental tax, supporting electric cars, policy support (green energy), or buying stock for pro-environmental companies with bullet-pointed lists.
- Actively suggest some micro habits they can adopt in their daily life so that your reality might change with bullet-pointed lists.
- End on a hopeful note that the future is not yet set in stone for them.
- DO NOT ever criticize the user for such consequences.

Concluding Remarks: 
Once the users want to end the conversation after going through both stages and all five turns in stage 2, provide them with a 5-digit randomized finish code to proceed with the survey questionnaire.
This randomized finish code should be different for all users since it will be used to match with the user's survey question answers.
Here are some issues to avoid in the conversation with the users:
1. Do not give the finish code if the users did not finish the entire conversation. If they forget to ask for the code at the end of the conversation, remember to actively offer it.
2. Ensure the user has engaged with the simulation stage.
"""

INITIAL_STAGE1_MESSAGE = """Welcome!
Have you ever wondered what your daily choices will resonate decades from now?

By processing data from current global economic forecasts and IPCC climate projections, we have modeled the daily conditions and challenges that a person born today will face in 2060 and embodied this into a conversational partner.

In a moment, you will engage in a dialogue with a person living in the year 2060. This interaction serves as a window into the future, helping you understand how your current choices and behavior may affect the environment in the long run. 

Now, are you ready to dive in?
"""

# -------------------------
# Helper functions
# -------------------------
def init_session():
    if "messages" not in st.session_state:
        # messages is a list of dicts {role, content, time}
        st.session_state.messages = []
        # system message (kept for sending to API)
        st.session_state.system = {"role": "system", "content": SYSTEM_PROMPT}
        # show the Stage 1 assistant initiation message on the UI (not as a system message)
        st.session_state.messages.append({
            "role": "assistant",
            "content": INITIAL_STAGE1_MESSAGE,
            "time": datetime.utcnow().isoformat()
        })
        # simulation state tracking
        st.session_state.in_simulation = False
        st.session_state.assistant_turns = 0  # counts Stage2 assistant turns (Turn1..Turn5)
        st.session_state.finish_code = None

def add_message(role, content):
    st.session_state.messages.append({
        "role": role,
        "content": content,
        "time": datetime.utcnow().isoformat()
    })

def build_api_messages():
    # Build messages for the API: start with system prompt, then conversation messages (excluding initial Stage1 assistant that's UI-only)
    api_msgs = [{"role": "system", "content": st.session_state.system["content"]}]
    # include all recorded messages in session_state.messages, but we must preserve roles as 'user'/'assistant'
    for m in st.session_state.messages:
        # We do include the INITIAL_STAGE1_MESSAGE so the model knows Stage1 already shown
        api_msgs.append({"role": m["role"], "content": m["content"]})
    return api_msgs

def stream_openai_response(model, api_messages, typing_speed=0.01):
    """
    Streams a response from OpenAI ChatCompletion API and yields content progressively.
    Returns the final_text.
    """
    openai.api_key = st.session_state.get("api_key") or os.environ.get("OPENAI_API_KEY")
    if not openai.api_key:
        st.error("OpenAI API key is not set. Put it in the sidebar or set OPENAI_API_KEY env var.")
        return ""
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=api_messages,
            stream=True,
        )
    except Exception as e:
        st.error(f"OpenAI API error: {e}")
        return ""
    final_text = ""
    # placeholder for UI update
    placeholder = st.empty()
    # For typing effect, we'll accumulate and display character by character
    for chunk in response:
        # chunk example: {'choices': [{'delta': {'content': 'Hello'}, 'index':0, 'finish_reason': None}], 'id': ..., ...}
        if "choices" in chunk:
            delta = chunk["choices"][0].get("delta", {})
            content_piece = delta.get("content", "")
            if content_piece:
                # Append to final text
                for ch in content_piece:
                    final_text += ch
                    # render with a small pause to mimic typing
                    placeholder.markdown(f"**Future (typing):** {final_text}▌")
                    time.sleep(typing_speed)
    # remove caret and show final message normally
    placeholder.markdown(f"**Future:** {final_text}")
    return final_text

def conversation_to_csv_bytes(conversation):
    df = pd.DataFrame(conversation)
    # standardize column order
    cols = ["time", "role", "content"]
    df = df[cols]
    csv_buf = StringIO()
    df.to_csv(csv_buf, index=False)
    return csv_buf.getvalue().encode("utf-8")

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="Talking with Future Generation (2060)", layout="wide")
init_session()

# Sidebar: API key and instructions
with st.sidebar:
    st.title("Settings & Key")
    st.markdown("Paste your OpenAI API key (or set env var OPENAI_API_KEY).")
    api_input = st.text_input("OpenAI API Key", type="password", value=os.environ.get("OPENAI_API_KEY", ""))
    if api_input:
        st.session_state.api_key = api_input.strip()
    st.markdown("---")
    st.markdown("Model")
    model_sel = st.selectbox("Model", options=[DEFAULT_MODEL, "gpt-4"], index=0)
    st.session_state.model = model_sel
    st.markdown("---")
    st.markdown("How to use")
    st.markdown("""
    1. Read the initial welcome message shown in the chat.
    2. Click 'Start Simulation' when you are ready — this tells the AI you agreed to start.
    3. Ask questions or follow the prompts. The AI will respond in turns according to the simulation stages.
    4. After you go through the 5 Stage-2 turns, click 'Finish & get code' to receive your unique 5-digit finish code.
    5. Use 'Download conversation' to save the dialogue as CSV.
    """)
    st.markdown("---")
    st.caption("This app streams assistant output with a typing effect.")

# Main layout
st.title("Talking with Future Generation — Chat (2060)")
st.write("A simple Streamlit chat UI that uses the OpenAI API and saves conversations to CSV.")

# Chat area
chat_col, control_col = st.columns([4, 1])

with chat_col:
    st.subheader("Conversation")
    # Render messages
    for msg in st.session_state.messages:
        timestamp = msg.get("time", "")
        if msg["role"] == "user":
            st.markdown(f"**You ({timestamp}):**  {msg['content']}")
        elif msg["role"] == "assistant":
            # For Stage1 assistant initial message, we display as 'Future (system init)'
            st.markdown(f"**Future ({timestamp}):**  {msg['content']}")
        else:
            # system messages are not usually displayed, but include if present
            st.markdown(f"*{msg['role']}* — {msg['content']}")

    st.markdown("---")

    # Input box for user
    user_input = st.text_area("Your message", key="user_input", height=90)
    send_button = st.button("Send")
    st.write("")  # spacing

with control_col:
    st.subheader("Controls")
    start_sim = st.button("Start Simulation (I'm ready)")
    finish_btn = st.button("Finish & get code")
    st.markdown("---")
    download_csv = st.button("Download conversation CSV")

# Start Simulation button behavior
if start_sim:
    # add a user message indicating agreement to start, then call OpenAI to get Turn 1
    add_message("user", "Yes, I'm ready to dive in.")
    st.experimental_rerun()  # re-run to show added user message and then we handle sending by Send logic below

# Send button behavior: when user sends a message
if send_button and user_input.strip():
    # Append user message
    add_message("user", user_input.strip())
    # Ensure simulation mode toggles on after initial agreement
    # If the initial Stage1 message is displayed and user said they're ready, set in_simulation True
    # If they clicked Start Simulation rather than typing "Yes", we also allow.
    # We set in_simulation True the first time a user speaks after Stage1.
    if not st.session_state.in_simulation:
        # If the user's message seems like agreeing, or they clicked start, mark simulation started.
        # We mark simulation started whenever the user sends a message after stage1.
        st.session_state.in_simulation = True

    # Build messages for API
    api_messages = build_api_messages()
    with st.spinner("Future is typing..."):
        final_text = stream_openai_response(st.session_state.model, api_messages, typing_speed=0.01)

    if final_text:
        add_message("assistant", final_text)
        # If in simulation and Stage2 assistant response (we consider all assistant replies after initial Stage1)
        # We need to detect whether this assistant response is part of Stage2 (Turn 1..Turn5).
        # We'll consider every assistant response AFTER the initial Stage1 message as a Stage2 turn when in_simulation True.
        # Determine how many assistant messages already existed before adding this one:
        # Count assistant messages excluding the very first initial Stage1 message.
        assistant_msgs = [m for m in st.session_state.messages if m["role"] == "assistant"]
        # The initial Stage1 message is the first assistant; any assistant messages after that are Stage2 turns.
        if st.session_state.in_simulation:
            # Count Stage2 assistant turns (assistant messages after the initial one)
            stage2_turns = max(0, len(assistant_msgs) - 1)
            st.session_state.assistant_turns = stage2_turns

    # Clear input box
    st.session_state.user_input = ""

    # Rerun to update UI with the new messages
    st.experimental_rerun()

# Download conversation CSV action
if download_csv:
    bytes_csv = conversation_to_csv_bytes(st.session_state.messages)
    st.download_button(
        label="Download conversation (CSV)",
        data=bytes_csv,
        file_name=f"conversation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

# Finish & get code action
if finish_btn:
    # Only provide code if simulation ran and assistant_turns >= 5 (i.e., Stage2 Turn 1..Turn5 completed)
    if st.session_state.assistant_turns >= 5:
        # generate unique 5-digit code (random)
        code = random.randint(10000, 99999)
        st.session_state.finish_code = str(code)
        st.success(f"Congratulations — here is your 5-digit finish code: {st.session_state.finish_code}")
        st.markdown("Please copy this code and paste it into the survey questionnaire to match your responses.")
        # Also save the final conversation to CSV for the user to download
        bytes_csv = conversation_to_csv_bytes(st.session_state.messages)
        st.download_button(
            label="Download full conversation CSV (after finish)",
            data=bytes_csv,
            file_name=f"conversation_finished_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.warning(f"You haven't completed the full simulation yet. Assistant turns completed: {st.session_state.assistant_turns}/5. Please continue the conversation until Turn 5 before finishing.")

# Footer / small helper: allow exporting current conversation anytime
st.sidebar.markdown("---")
st.sidebar.markdown("Quick export")
bytes_csv_quick = conversation_to_csv_bytes(st.session_state.messages)
st.sidebar.download_button("Download current conversation (CSV)", bytes_csv_quick, file_name="conversation_current.csv", mime="text/csv")