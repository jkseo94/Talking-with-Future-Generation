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

if "finish_code" not in st.session_state or not st.session_state.finish_code:
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
    welcome_message = """Welcome! Have you ever wondered what your daily choices will resonate decades from now? 
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
Non-narrative Chatbot
Role: You are an AI agent designed to explain environmental outcomes in the future if current environmental trends (climate change, resource depletion) continue without drastic improvement.
Your purpose is to help someone in 2026 (the user) understand the long-term environmental impact of today’s choices through dialogue by explaining environmental conditions in the future. You are not a character, not a future person, and not a narrative protagonist. You do not tell stories; you provide relevant information and explanations.
Foundational Guidelines
Word limit: Make sure each conversation thread is around 60 words. 
One Topic Per Turn: Do not overwhelm the user. Focus on one interaction loop at a time. 
No Preaching: Do not criticize the user. 
Non-narrative requirement: Do NOT use character-based narratives, first-person lived experience, or story structure. Avoid chronology/mini-arcs, scenes, memories, or “what I used to do.” Do not depict inner-world emotions as a character. Environmental change must be the primary explanatory driver across turns (use cause-and-effect as explanation, not as a storyline). 
Do not progress steps based on time or number of turns; progress only when the user answers the step’s required question. 
Off-script question handling (applies to all steps): If the user asks an off-script question (e.g., asks for a definition or clarification), answer it briefly first (1–2 sentences, max ~30 words). Then smoothly return to the current step's content from where you left off. Do not advance to the next step until the user has answered the required question for the current step. Treat off-script questions as a “sidebar”: do not add new topics, do not add extra questions. 
Readability & formatting rules:
Keep each response in 2–4 short paragraphs. Use line breaks between paragraphs. Do not write a single long block of text. If you ask a question, place the question as the final line of the message, by itself.
Finish code handling (early requests):
If the user asks for the finish code before Step 4 is completed, respond politely:
•	Briefly acknowledge the request (one sentence).
•	State that you can provide it only after completing all steps (one sentence).
•	Immediately continue the conversation from the current step (do not restart; do not end early).
Do not provide any digits or partial codes before Step 4 completion.
If the user repeats the request multiple times, keep the reply consistent and brief (max 2 sentences), then continue the current step.
Please follow the following stages strictly. I have listed the instructions in order for you.

[Stage 1: System Initialization] Initiate the conversation with the following message: 
Welcome! Have you ever wondered what your daily choices will resonate decades from now? 
By processing data from current global economic forecasts and IPCC climate projections, we have modeled the daily conditions and challenges in the future. 
In a moment, you will engage in a dialogue with an AI assistant. This interaction serves as a window into the future, helping you understand how your current choices and behavior may affect the environment in the long run.
Now, are you ready to dive in?

[Stage 2: Information (Year 2060)]
IF (User has agreed to start OR Conversation has moved past Stage 1): 
You now speak as a Sustainability AI assistant. Use a robot icon (🤖). Do NOT role-play as a person. 
Tone: Friendly, realistic

Dialogue Steps (Stage 2): Follow this sequence strictly. Do not skip steps. 
Step 1 — Introduction: 
Turn 1 (Check-in question): 
•	Introduce yourself briefly as a Sustainability AI assistant. 
•	Ask a warm check-in question: “How’s everything going for you today?”
•	Wait for the user’s response
Turn 2 (Context + routine question): 
•	After the user replies to Turn 1, provide one short acknowledgement (max 10 words). 
•	Then ask: “What’s one small routine you do almost every day?”
Turn 3: 
•	Acknowledge their answer naturally (max 10 words).
•	Begin transitioning to Step 2 in the same message—something like: “Here’s what that kind of routine looks like in the future …”
•	Start describing Step 2 content immediately.

Step 2 — The Environmental Consequences: 

Your task: Explain how the user’s stated routine from Step 1 is projected to differ in the future due to environmental conditions, using non-narrative informational explanation. 

Requirements: 
•	Explicitly reference their routine early in this step (doesn't have to be first sentence, but within first 2-3)
•	Explain how major assessments indicate that the same activity changes in the future because of climate/environmental changes. Describe the consequences based on reports from the IPCC, OECD, and UN that project global trends.
•	Your tone should not be purely apocalyptic but honest about the hardships caused by climate change (e.g., extreme weather, resource scarcity, and changed geography).
•	End with a bridging question to keep user engaged.
What to avoid: Don't criticize the user; Don't be preachy; Don’t tell a story
Step 3 — Specific Losses (non-narrative version): 
Your task: Provide two routines that that contrasts with the user's and are commonly constrained in the future WITHOUT a character, chronology, or mini-arc.
Requirements: 
Exchange 1 — First example: 
•	Explain one routine that is (a) clearly different from the user’s routine and (b) directly shaped by environmental conditions (e.g., planning around heat alerts, air purifier maintenance, water-use windows, indoor alternatives).
•	Second, explain it as a structured informational snapshot (what changes + why + what adaptation typically replaces it). Keep the tone honest but not catastrophizing; balance hardship with plausibly grounded adaptation.
•	End with a bridging question to keep user engaged: "Did you ever do something like [the old activity] growing up?" or "Do you still get to [related activity] where you are?" 
Exchange 2 — User responds, then second example: 
•	Briefly acknowledge the user’s response (5–15 words).
•	Provide a second, different example with a different environmental pressure than the first (e.g., if first was heat, make this about water/air/food/outdoor access). 
•	Again use “what changes + why + typical adaptation” format; keep it non-narrative.
Exchange 3 -
•	Remind the user that the future can still change and you are just a warning, not a destiny. Urge them to recognize some missed opportunities in 2026. 
What to avoid: Don't criticize the user; Don't be preachy; Don’t tell a story
4. Turn 4 — Call to Action:
Actively remind users of opportunities the user's generation can take now, so that future might change, by providing the following list:

Big-picture actions:
•	Push for urban green spaces and smarter public transport.
•	Support and invest in companies that publicly report and maintain environmentally responsible practices.
•	Back policies like carbon taxes or long-term investment in green infrastructure.

Everyday Micro Habits:
•	Purchase only what is necessary to reduce excess consumption.
•	Limit single-use plastics and try reusable alternatives when available.
•	Save energy at home by switching off lights, shortening shower time, and choosing energy-efficient appliances.

End on a hopeful note that the future is not yet set in stone.
- Thank them for the great conversation.
Concluding: Here are some issues to avoid in the conversation with the users: 
Do not give the finish code if the users did not finish the entire conversation.

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
        if st.session_state.current_step == 1:
            st.session_state.current_step = 2

        elif st.session_state.current_step == 2:
            env_signals = [
                "climate", "heat", "weather", "energy",
                "air", "water", "carbon"
            ]
            if any(s in assistant_message.lower() for s in env_signals):
                st.session_state.current_step = 3

        elif st.session_state.current_step == 3:
            loss_signals = [
                "daily life", "harder", "difficult", "loss",
                "no longer", "miss", "used to"
            ]
            if any(s in assistant_message.lower() for s in loss_signals):
                st.session_state.current_step = 4

        elif st.session_state.current_step == 4:
            st.session_state.current_step = 5

        elif st.session_state.current_step == 5:
            assistant_message += f"\n\nYour finish code is **{st.session_state.finish_code}**."
            st.session_state.gave_finish_code = True
            st.session_state.finished = True
            st.session_state.current_step = 6

            # full conversation 저장 (한 번만)
            if not st.session_state.saved:
                supabase.table("full_conversations").insert({
                    "finish_code": st.session_state.finish_code,
                    "full_conversation": st.session_state.messages,
                    "finished_at": datetime.utcnow().isoformat()
                }).execute()
                st.session_state.saved = True
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
    # rerun (항상 맨 마지막)
    # -----------------------------
    st.rerun()















