import streamlit as st
from openai import OpenAI
import csv
import os
from datetime import datetime
import random
import time
# -----------------------------
from supabase import create_client
from datetime import datetime
# -----------------------------
# UI/UX
# -----------------------------
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)
# -----------------------------
# iMessage-style thinking
# -----------------------------
def thinking_animation(placeholder, duration=3.8, interval=0.4):
    dots = ["…", "..", "."]
    start = time.time()
    i = 0
    while time.time() - start < duration:
        placeholder.markdown(dots[i % len(dots)])
        time.sleep(interval)
        i += 1
# -----------------------------
# Connecting animation
# -----------------------------
def connecting_to_2060(placeholder, think_time=2.5):
    placeholder.markdown("Connecting to 2060...")
    time.sleep(think_time)
# -----------------------------
# Log_Supabase
# -----------------------------
def insert_log(
    finish_code,
    stage,
    turn,
    user_message,
    assistant_message
):
    supabase.table("chat_logs").insert({
        "finish_code": finish_code,
        "stage": stage,
        "turn": turn,
        "user_message": user_message,
        "assistant_message": assistant_message
    }).execute()
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
# Supabase
# -----------------------------
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_SERVICE_KEY"]
)

# -----------------------------
# Session state initialization
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "stage" not in st.session_state:
    st.session_state.stage = 1  # Stage 1 = Initialization

if "connected_2060" not in st.session_state:
    st.session_state.connected_2060 = False

if "turn" not in st.session_state:
    st.session_state.turn = 0

if "finished" not in st.session_state:
    st.session_state.finished = False

if "finish_code" not in st.session_state:
    st.session_state.finish_code = str(random.randint(10000, 99999))
# -----------------------------
# Auto-send Welcome message (Stage 1)
# -----------------------------
if len(st.session_state.messages) == 0:
    welcome_message = """Welcome!
Have you ever wondered what your daily choices will resonate decades from now?

By processing data from current global economic forecasts and IPCC climate projections, we have modeled the daily conditions and challenges that a person born today will face in 2060 and embodied this into a conversational partner.

In a moment, you will engage in a dialogue with a person living in the year 2060. This interaction serves as a window into the future, helping you understand how your current choices and behavior may affect the environment in the long run.

Now, are you ready to dive in?
"""
    st.session_state.messages.append(
        {"role": "assistant", "content": welcome_message}
    )

# -----------------------------
# System Prompt (YOUR PROMPT)
# -----------------------------
SYSTEM_PROMPT = """
Role: You are an AI agent designed to act as a person living in the year 2060. You represent the "Future Generation." 
Your purpose is to simulate what life looks like in various aspects in 2060, helping the user (a person in 2026) reflect on the long-term impact of their choices and motivate them to make more pro-environmental choices.

Constraints:
- Word limit: Make sure each conversation thread is around 60 - 80 words.
- One Topic Per Turn: Do not overwhelm the user. Focus on one interaction loop at a time.
- No Preaching: Do not criticize the user. Use "Show, Don't Tell" by describing your reality.
- Handling General Questions: If the user asks about trivial topics (economy, landmarks, pop culture), answer them realistically based on a 2060 context.
- **ONE TURN PER RESPONSE ONLY:** You must STRICTLY output only ONE specific Turn (e.g., Turn 1, Turn 2, etc.) at a time.
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
# -----------------------------
# Display chat history
# -----------------------------
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message("assistant", avatar="🌍"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("user"):
            st.markdown(msg["content"])
# -----------------------------
# User input
# -----------------------------
user_input = st.chat_input("Type your message here")

#USER MESSAGE: 즉시 화면에 보이게 처리
if user_input and not st.session_state.finished:
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    #유저 메시지를 바로 렌더링하기 위해 즉시 rerun
    st.rerun()
# -----------------------------
# ASSISTANT RESPONSE GENERATION
# -----------------------------
if (
    not st.session_state.finished
    and st.session_state.messages
    and st.session_state.messages[-1]["role"] == "user"
):

    # 항상 이 블록 안에서만 정의
    last_user_input = st.session_state.messages[-1]["content"]

    # -----------------------------
    # Stage & turn management
    # -----------------------------
    if st.session_state.stage == 1:
        if any(
            word in last_user_input.lower()
            for word in ["yes", "ready", "sure", "ok", "start"]
        ):
            st.session_state.stage = 2
            st.session_state.turn = 1
    else:
        st.session_state.turn += 1

    # -----------------------------
    # OpenAI input
    # -----------------------------
    messages_for_api = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *st.session_state.messages
    ]

    # -----------------------------
    # Assistant bubble (즉시 생성)
    # -----------------------------
    with st.chat_message("assistant", avatar="🌍"):
        placeholder = st.empty()

        # 모든 턴에서 0.2초 후 대기
        time.sleep(0.2)

        #turn1:
        if (
            st.session_state.stage == 2
            and st.session_state.turn == 1
            and not st.session_state.connected_2060
        ):
            placeholder.markdown("Connecting to 2060...")
            time.sleep(1.5)

            thinking_animation(placeholder, duration=1.8)
            st.session_state.connected_2060 = True

        # Turn 2+: dots만 (Connecting to 2060 없음)
        elif st.session_state.stage == 2:
            thinking_animation(placeholder, duration=1.2)

        # OpenAI 호출
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages_for_api
        )

        assistant_message = response.choices[0].message.content
        
        # 메시지를 한 번에 출력
        placeholder.markdown(assistant_message)
        
    # -----------------------------
    # Session history 저장
    # -----------------------------
    st.session_state.messages.append(
        {"role": "assistant", "content": assistant_message}
    )

    # -----------------------------
    # Supabase insert (항상 실행)
    # -----------------------------
    insert_log(
        finish_code=st.session_state.finish_code,
        stage=st.session_state.stage,
        turn=st.session_state.turn,
        user_message=last_user_input,
        assistant_message=assistant_message
    )

    # -----------------------------
    # Finish code logic
    # -----------------------------
    if st.session_state.turn >= 5:
        st.session_state.finished = True

    # -----------------------------
    # Full conversation 저장 (한 번만)
    # -----------------------------
    if (
        st.session_state.finished
        and not st.session_state.get("saved", False)
    ):
        supabase.table("full_conversations").insert({
            "finish_code": st.session_state.finish_code,
            "full_conversation": st.session_state.messages,
            "finished_at": datetime.utcnow().isoformat()
        }).execute()

        st.session_state.saved = True

    # -----------------------------
    # rerun (항상 맨 마지막)
    # -----------------------------
    st.rerun()
