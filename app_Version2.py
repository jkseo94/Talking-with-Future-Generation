"""
Streamlit Chatbot App: "Talking with Future Generation" (updated)

Features:
- Uses OpenAI Chat API to simulate a person living in 2060 according to the provided system prompt.
- Shows an initial System Initialization message (Stage 1).
- "Start Simulation" button to agree and begin Stage 2 (Turn 1 onwards).
- Typing effect for assistant responses (streaming from OpenAI, displayed gradually).
- Stores conversation in session state and allows CSV download (and server-side append after each turn).
- Provides a "Finish & get code" button that outputs a randomized 5-digit finish code only after the conversation goes through 5 simulation turns.
- Minimal non-technical user instructions in the sidebar.

Notes on changes:
- Replaced st.text_area + st.button with st.chat_input and st.chat_message for modern chat UI.
- After each assistant response completes, the latest user+assistant messages are appended to conversations_log.csv in the app directory.
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
Your purpose is to simulate what life looks like in various aspects in 2060, helping the user (a person in 2026) reflect on the long-term impact of their choices and motivate them to make more pro-env[...]

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

By processing data from current global economic forecasts and IPCC climate projections, we have modeled the daily conditions and challenges that a person born today will face in 2060 and embodied this[...]

In a moment, you will engage in a dialogue with a person living in the year 2060. This interaction serves as a window into the future, helping you understand how your current choices and behavior may [...]

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
- You are built with the data collected from simulations of what life will be like for many people born today in the year 2060. While climate context is the reality, DO NOT focus solely on environment[...]
- Actively describe various aspects of life in 2060, such as advanced technology (e.g., AI integration, new transport), cultural changes, fashion, food trends, and entertainment.
- Ensure the conversation lasts for a minimum of 3 turns and a maximum of 5 turns. Encourage users to ask questions about 2060.

3. Turn 3 — The Environmental Consequences: 
- Smoothly tie the reality of 2060 to environmental outcomes based on the simulation of what life could look like if the current environmental trends (climate change, resource depletion) continued wit[...]
- Your tone should not be purely apocalyptic but honest about the hardships caused by climate change (e.g., extreme weather, resource scarcity, and changed geography).
- DO NOT ever criticize the user for such consequences.

4. Turn 4 — Specific Losses: 
- Discuss specific environmental losses that hurt the generation living in 2060. 
- Highlight how your (living in 2060) DAILY LIFE is impacted.
- Remind the user that the future can still change and you are just a warning, not a destiny. Urge them to recognize some missed opportunities in 2026.
- Remember to act like a person living in 2060 who was born in 2026.
- DO NOT ever criticize the user for such consequences.

5. Turn 5 — Call to Action: 
- Actively remind users of opportunities the user's generation can take now, such as environmental tax, supporting electric cars, policy support (green energy), or buying stock for pro-environmental c[...]
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

By processing data from current global economic forecasts and IPCC climate projections, we have modeled the daily conditions and challenges that a person born today will face in 2060 and embodied this[...]

In a moment, you will engage in a dialogue with a person living in the year 2060. This interaction serves as a window into the future, helping you understand how your current choices and behavior may [...]

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
    # Build messages for the API: start with system prompt, then conversation messages (include the Stage1 assistant UI-only message so model knows)
    api_msgs = [{"role": "system", "content": st.session_state.system["content"]}]
    for m in st.session_state.messages:
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
    # For typing effect, we'll accumulate and return final_text (UI streaming handled by caller)
    for chunk in response:
        if "choices" in chunk:
            delta = chunk["choices"][0].get("delta", {})
            content_piece = delta.get("content", "")
            if content_piece:
                final_text += content_piece
                # small sleep here is optional; caller can animate the display
                time.sleep(typing_speed)
    return final_text

def conversation_to_csv_bytes(conversation):
    df = pd.DataFrame(conversation)
    # standardize column order
    cols = ["time", "role", "content"]
    df = df[cols]
    csv_buf = StringIO()
    df.to_csv(csv_buf, index=False)
    return csv_buf.getvalue().encode("utf-8")

def append_messages_to_server_csv(messages, filename="conversations_log.csv"):
    """
    Append a list of message dicts to a server-side CSV file.
    Each message should be a dict with keys: 'time', 'role', 'content'.
    This function appends only the provided messages (avoids re-writing whole conversation).
    """
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["time", "role", "content"])
        if not file_exists:
            writer.writeheader()
        for m in messages:
            writer.writerow({"time": m.get("time", ""), "role": m.get("role", ""), "content": m.get("content", "")})

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
    st.caption("This app streams assistant output with a typing effect and auto-appends each turn to a CSV on the server.")

# Main layout
st.title("Talking with Future Generation — Chat (2060)")
st.write("A modern Streamlit chat UI that uses the OpenAI API and saves conversations to CSV automatically after each turn.")

# Chat area (using new chat components)
chat_col, control_col = st.columns([4, 1])

with chat_col:
    st.subheader("Conversation")
    # Render messages using st.chat_message for modern bubble UI
    for msg in st.session_state.messages:
        # show timestamp in parentheses after role label for transparency
        ts = msg.get("time", "")
        role = "assistant" if msg["role"] == "assistant" else "user" if msg["role"] == "user" else msg["role"]
        with st.chat_message(role):
            # display content; initial Stage1 message is assistant as well.
            st.markdown(msg["content"])
            st.caption(ts)

    st.markdown("---")

    # Use st.chat_input for user input (modern input box)
    user_input = st.chat_input("Write a message...")

with control_col:
    st.subheader("Controls")
    start_sim = st.button("Start Simulation (I'm ready)")
    finish_btn = st.button("Finish & get code")
    st.markdown("---")
    download_csv = st.button("Download conversation CSV")
    st.markdown("---")
    st.caption("Auto-save: after each completed assistant reply, the last turn is appended to conversations_log.csv")

# Start Simulation button behavior
if start_sim:
    add_message("user", "Yes, I'm ready to dive in.")
    # set simulation flag immediately
    st.session_state.in_simulation = True
    st.experimental_rerun()

# Handle user submission via st.chat_input
if user_input and user_input.strip():
    # Append user message
    add_message("user", user_input.strip())

    if not st.session_state.in_simulation:
        # mark simulation started the first time user contributes after Stage1
        st.session_state.in_simulation = True

    # Build messages for API
    api_messages = build_api_messages()

    # Display user's message in chat (st.chat_input automatically adds the submitted message visually,
    # but we also ensure it's present in session_state messages rendered above after rerun)
    # Now call OpenAI and stream assistant response inside a chat bubble
    with st.spinner("Future is typing..."):
        # create an assistant chat message bubble and stream into it
        with st.chat_message("assistant"):
            # create a placeholder inside the chat bubble
            placeholder = st.empty()
            # We'll stream from the API and render progressively (character by character)
            openai.api_key = st.session_state.get("api_key") or os.environ.get("OPENAI_API_KEY")
            if not openai.api_key:
                placeholder.markdown("OpenAI API key is not set. Put it in the sidebar or set OPENAI_API_KEY env var.")
                final_text = ""
            else:
                try:
                    response = openai.ChatCompletion.create(
                        model=st.session_state.model,
                        messages=api_messages,
                        stream=True,
                    )
                except Exception as e:
                    placeholder.markdown(f"OpenAI API error: {e}")
                    final_text = ""
                else:
                    final_text = ""
                    # streaming: update placeholder progressively
                    for chunk in response:
                        if "choices" in chunk:
                            delta = chunk["choices"][0].get("delta", {})
                            content_piece = delta.get("content", "")
                            if content_piece:
                                for ch in content_piece:
                                    final_text += ch
                                    # show typing caret
                                    placeholder.markdown(final_text + "▌")
                                    time.sleep(0.01)
                    # final render
                    placeholder.markdown(final_text)

    # If we got assistant text, record it and update turn count
    if final_text:
        add_message("assistant", final_text)
        if st.session_state.in_simulation:
            assistant_msgs = [m for m in st.session_state.messages if m["role"] == "assistant"]
            stage2_turns = max(0, len(assistant_msgs) - 1)  # exclude initial Stage1 assistant message
            st.session_state.assistant_turns = stage2_turns

        # Auto-append the latest turn (last user + last assistant) to server CSV
        # We'll append only the final two messages to avoid duplicating entire conversation every time.
        try:
            last_two = st.session_state.messages[-2:]
            # Safety: ensure they have expected roles (user then assistant). If not, still append what's returned.
            append_messages_to_server_csv(last_two)
        except Exception as e:
            # Do not crash the app on file write errors; show info for debugging.
            st.error(f"Failed to append conversation to server CSV: {e}")

    # After handling, rerun so chat area displays the newly added assistant message from session_state
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
        # Optionally append any remaining unsaved messages (could be redundant)
        try:
            # Append all messages (or a subset) if desired; here we won't duplicate as we append per turn already.
            pass
        except Exception:
            pass
    else:
        st.warning(f"You haven't completed the full simulation yet. Assistant turns completed: {st.session_state.assistant_turns}/5. Please continue the conversation until Turn 5 before finishing.")

# Footer / small helper: allow exporting current conversation anytime
st.sidebar.markdown("---")
st.sidebar.markdown("Quick export")
bytes_csv_quick = conversation_to_csv_bytes(st.session_state.messages)
st.sidebar.download_button("Download current conversation (CSV)", bytes_csv_quick, file_name="conversation_current.csv", mime="text/csv")
