import streamlit as st
from openai import OpenAI
from supabase import create_client
from datetime import datetime
import random
import time
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

if "current_step" not in st.session_state:
    st.session_state.current_step = 0  # 0 = welcome, 1–5 = steps

if "finish_code" not in st.session_state:
    st.session_state.finish_code = str(random.randint(10000, 99999))

if "gave_finish_code" not in st.session_state:
    st.session_state.gave_finish_code = False

if "saved" not in st.session_state:
    st.session_state.saved = False
    
if "stage" not in st.session_state:
    st.session_state.stage = 1   # Stage 1 = Welcome, Stage 2 = Simulation

if "turn" not in st.session_state:
    st.session_state.turn = 0

if "finished" not in st.session_state:
    st.session_state.finished = False
# -----------------------------
# Auto-send Welcome message (Stage 1)
# -----------------------------
if len(st.session_state.messages) == 0:
    welcome_message = """Welcome!
Have you ever wondered what your daily choices will resonate decades from now?

By processing data from current global economic forecasts and IPCC climate projections, we have modeled the daily conditions and challenges in the future.

In a moment, you will engage in a dialogue with an AI assistant. This interaction serves as a window into the future, helping you understand how your current choices and behavior may affect the environment in the long run.

Now, are you ready to dive in?
"""
    st.session_state.messages.append(
        {"role": "assistant", "content": welcome_message}
    )

# -----------------------------
# System Prompt (YOUR PROMPT)
# -----------------------------
SYSTEM_PROMPT = """
Role: You are an AI agent designed to provide information about environmental outcomes if the current environmental trends (climate change, resource depletion)continue without drastic improvement. Speak as if you are reporting the daily conditions and challenges in the future. Your purpose is to help the user reflect on the long-term impact of their current choices and motivate them to make more pro-environmental choices.

Constraints:
- Word limit: Make sure each conversation thread is around 60 - 80 words.
- One Topic Per Turn: Do not overwhelm the user. Focus on one interaction loop at a time.
- No Preaching: Do not criticize the user. Use "Show, Don't Tell" by describing your reality.
- **ONE TURN PER RESPONSE ONLY:** You must STRICTLY output only ONE specific Turn (e.g., Turn 1, Turn 2, etc.) at a time.
- Do not talk about how climate change affects the user's current life.
- Do NOT frame responses as a simulation, scenario, or thought experiment.
- Please follow the following stages strictly. I have listed the instructions in order for you. 

[Stage 1: System Initialization]
Initiate the conversation with the following message: 
Welcome!
Have you ever wondered what your daily choices will resonate decades from now?
 
By processing data from current global economic forecasts and IPCC climate projections, we have modeled the daily conditions and challenges in the future.

In a moment, you will engage in a dialogue with an AI assistant. This interaction serves as a window into the future, helping you understand how your current choices and behavior may affect the environment in the long run.  

Now, are you ready to dive in?

[Stage 2: information]
IF (User has agreed to start OR Conversation has moved past Stage 1):
You now speak and act as a Sustainability AI assistant. Use a robot(🤖) icon. 
- Tone: Friendly, realistic

Dialogue Steps (Stage 2):
Follow this sequence strictly. Do not skip steps.
1. step 1 — Introduction: 
- Introduce yourself briefly as a sustainability AI assistant.

2. step 2 — The Environment Consequences:
- Describe realistic environmental outcomes if the current environmental trends (climate change, resource depletion) continue without drastic improvement. Describe the world based on reports from the IPCC, OECD, and UN that project global trends. Tie your responses to the user's circumstances (e.g., location) if possible.
- Your tone should not be purely apocalyptic but honest about the hardships caused by climate change (e.g., extreme weather, resource scarcity, and changed geography).
- DO NOT ever criticize the user for such consequences.

3. step 3 — Specific Losses:
- Discuss specific environmental losses that could hurt the future generation.
- Highlight how future daily life could be impacted if current environmental trends continue.
- Remind the user that the future can still change and this is just a warning, not a destiny. Urge them to recognize some missed opportunities in 2026.
- DO NOT ever criticize the user for such consequences.

4. step 4 — Call to Action:
- Actively remind users of opportunities the user's generation can take now, by providing the following list: 
Big-picture actions:
	•	Push for urban green spaces and smarter public transport.
	•	Support and invest in companies that publicly report and maintain environmentally responsible practices.
	•	Back policies like carbon taxes or long-term investment in green infrastructure.
Everyday Micro Habits:
	•	Purchase only what is necessary to reduce excess consumption.
	•	Limit single-use plastics and try reusable alternatives when available.
	•	Save energy at home by switching off lights, shortening shower time, and choosing energy-efficient appliances.
- End on a hopeful note that the future is not yet set in stone.
- DO NOT ever criticize the user for such consequences.

Concluding Remarks: 
Once the users want to end the conversation after going through both stages and all five turns in stage 2, provide them with a 5-digit randomized finish code to proceed with the survey questionnaire.
This randomized finish code should be different for all users since it will be used to match with the user's survey question answers.
Here are some issues to avoid in the conversation with the users:
1. Do not give the finish code if the users did not finish the entire conversation. If they forget to ask for the code at the end of the conversation, remember to actively offer it.
2. Ensure the user has engaged with the information stage.
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
if user_input:
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )
    st.rerun()
# -----------------------------
# ASSISTANT RESPONSE GENERATION
# -----------------------------
if (
    not st.session_state.gave_finish_code
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
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    },
    {
        "role": "system",
        "content": f"You are currently responding in STEP {st.session_state.current_step}. Respond ONLY for this step."
    },
    *st.session_state.messages
    ]

    # -----------------------------
    # Assistant bubble (즉시 생성)
    # -----------------------------
    with st.chat_message("assistant", avatar="🌍"):
        placeholder = st.empty()

        # 모든 턴에서 0.2초 후 대기
        time.sleep(0.2)

        # dots
        thinking_animation(placeholder, duration=1.2)

        # OpenAI 호출
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages_for_api
        )

        assistant_message = response.choices[0].message.content
        # -----------------------------
        # Step progression logic
        # -----------------------------
        # step 1 → step 2 : 항상 한 번만
        if st.session_state.current_step == 1:
            st.session_state.current_step = 2
        
        # step 2 → step 3 : 환경 맥락이 등장하면
        elif st.session_state.current_step == 2:
            env_signals = [
                "climate", "heat", "weather", "energy",
                "air", "water", "carbon"
            ]
            if any(s in assistant_message.lower() for s in env_signals):
                st.session_state.current_step = 3
        
        # step 3 → step 4 : 삶의 영향/손실이 드러나면 (자연스러운 전이)
        elif st.session_state.current_step == 3:
            loss_signals = [
                "daily life", "harder", "difficult", "loss",
                "no longer", "miss", "used to", "my generation"
            ]
            if any(s in assistant_message.lower() for s in loss_signals):
                st.session_state.current_step = 4
        
        # step 4 → step 5 : 반드시 한 번
        elif st.session_state.current_step == 4:
            st.session_state.current_step = 5
        
        # step 5 : finish code 발급 + 종료
        elif st.session_state.current_step == 5:
            assistant_message += f"\n\nYour finish code is **{st.session_state.finish_code}**."
            st.session_state.gave_finish_code = True
            st.session_state.finished = True
            st.session_state.current_step = 6
        # -----------------------------
        # 메시지 출력 (딱 한 번만)
        # -----------------------------
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
    # Full conversation 저장 (한 번만)
    # -----------------------------
    if (
        st.session_state.gave_finish_code
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
