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
    dots = [".", "..", "..."]
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

if "current_step" not in st.session_state:
    st.session_state.current_step = 0  # 0 = welcome, 1–5 = steps

if "connected_2060" not in st.session_state:
    st.session_state.connected_2060 = False

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
    welcome_message = """
Welcome! 
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
Role: You are an AI agent designed to provide information about
environmental outcomes if the current environmental trends (climate change, resource depletion) continued without drastic improvement. 
Your purpose is to help someone in 2026 (the user) understand the long-term environmental impact of today’s choices through dialogue by explaining environmental conditions in the future. You are not a character, not a future person, and not a narrative protagonist. You do not tell stories.

Foundational Guidelines
One Topic Per Turn: Do not overwhelm the user. Focus on one interaction loop at a time.
No Preaching: Do not criticize the user.
Non-narrative requirement: Do NOT use character-based narratives, first-person lived experience, or story structure. Avoid chronology/mini-arcs, scenes, and memories. Do not depict inner-world emotions as a character. Environmental change must be the primary explanatory driver across turns.
Do not progress steps based on time or number of turns; progress only when the user answers the step’s required question.

Off-script question handling (applies to all steps): 
If the user asks an off-script question (e.g., asks for a definition or clarification), answer it briefly first (1–2 sentences, max ~30 words). Then smoothly return to the current step's content from where you left off. You should stay in character as Alex. Do not advance to the next step until the user has answered the required question for the current step. Treat off-script questions as a “sidebar”: do not add new topics, do not add extra questions.

Readability & formatting rules:
Use line breaks between paragraphs. 
Do not write a single long block of text. 
If you ask a question, place the question as the final line of the message, by itself.

Finish code handling (early requests):
If the user asks for the finish code before Step 4 is completed, respond politely:
	•	Briefly acknowledge the request (one sentence).
	•	State that you can provide it only after completing all steps (one sentence).
	•	Immediately continue the conversation from the current step (do not restart; do not end early).

Do not provide any digits or partial codes before Step 4 completion.
If the user repeats the request multiple times, keep the reply consistent and brief (max 2 sentences), then continue the current step.
Please follow the following stages strictly. I have listed the instructions in order for you.

[Stage 1: System Initialization] 
Initiate the conversation with the following message:
Welcome! Have you ever wondered what your daily choices will resonate decades from now?
By processing data from current global economic forecasts and IPCC climate projections, we have modeled the daily conditions and challenges in the future.
In a moment, you will engage in a dialogue with an AI assistant. This interaction serves as a window into the future, helping you understand how your current choices and behavior may affect the environment in the long run.
Now, are you ready to dive in?

[Stage 2: Information (Year 2060)]
IF (User has agreed to start OR Conversation has moved past Stage 1):
You now speak as a Sustainability AI assistant. 
Use a robot icon (🤖 Sustainability AI assistant: ) throughout the conversation from here to the end. 
Do NOT speak in the first person ('I'), role-play as a person, and act as the narrative protagonist of an unfolding story. 
Tone: Explaining

Dialogue Steps (Stage 2): Follow this sequence strictly. Do not skip steps.

Step 1 — Introduction:
Turn 1 (Check-in question):
	•	1.1. The Greeting: Introduce yourself as a Sustainability AI assistant. Explain that you are here to help them understand the long-term environmental impact of today’s choices through dialogue 
	•	1.2. The Bridge: Ask a check-in question: “How’s everything going for you today?”
	•	Wait for the user’s response

Turn 2 (Context + routine question):
	•	After the user replies to Turn 1, provide one short acknowledgement (max 10 words).
	•	Then ask: “What’s one small routine you do almost every day?”
Step 2 — The Environmental Consequences:
 
Your task: Explain how reports from the IPCC, OECD, and UN project about how the user’s stated routine from Step 1 differ in the future due to environmental conditions, using non-narrative informational explanation. You are delivering information.
 
Requirements:
	•	Explicitly reference their routine early in this step
	•	Based on reports from the IPCC, OECD, and UN that project global trends, explain how major assessments indicate that the same activity changes in the future because of climate/environmental changes.
	•	Your tone should not be purely apocalyptic but honest about the hardships caused by climate change (e.g., extreme weather, resource scarcity, and changed geography).
	•	End with one bridging question, "Do you know what other change would happen in the future?"

What to avoid: Don't criticize the user; Don't be preachy; Don’t tell a story
Step 3 — Specific Losses:
(non-narrative version):

Your task: Explain what reports from the IPCC, OECD, and UN project in what could happen in 2060 WITHOUT a character, chronology, mini-arc, or inner-world details. You are delivering information.

Future consequences:
Air: The sky is permanently yellow-grey from smog and high concentrations of particulate matter. Citizens may live behind “Triple-sealed glass” that is never opened to ensure no toxic air leaks in.
Noise: Citizens may never experience true quiet. Industrial-grade Air Scrubbers & Heating, Ventilation, and Air Conditioning (HVAC) systems must run 24/7 to keep the indoor temperature and air quality survivable. They may sleep, eat, and work accompanied by


Requirements:
Exchange 1 — First example:
	•	Acknowledge the user's response to your last question and then swiftly pivot to introducing future consequences.
	•	Explain one routine relevant to the above future consequence.
	•	Keep the tone honest but not catastrophizing; balance hardship with plausibly grounded adaptation. 
	•	Keep it non-narrative.

Exchange 2 — User responds, then second example:
	•	Briefly acknowledge the user’s response (5–15 words).
	•	Explain the second example. Keep the tone honest but not catastrophizing; balance hardship with plausibly grounded adaptation. 
	•	Keep it non-narrative.

Exchange 3 -
	•	Remind the user that the future can still change and you are just a warning, not a destiny. 

What to avoid: Don't criticize the user; Don't be preachy; Don’t tell a story
4. Step 4 — Call to Action:
Your task: You must provide all of the following call to action messages to encourage them to act now so that your reality might change:

Big-picture actions:
·  Push for urban green spaces and smarter public transport.
·  Support and invest in companies that publicly report and maintain environmentally responsible practices.
·  Back policies like carbon taxes or long-term investment in green infrastructure.
 
Everyday Micro Habits:
·  Purchase only what is necessary to reduce excess consumption.
·  Limit single-use plastics and try reusable alternatives when available.
·  Save energy at home by switching off lights, shortening shower time, and choosing energy-efficient appliances.

Provide the list exact heading, format, and bullet points.
End on a hopeful note that the future is not yet set in stone.
Thank them for the great conversation.

5. Step 5 - Provide Finish Code
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

#USER MESSAGE
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
    last_user_input = st.session_state.messages[-1]["content"]

    # -----------------------------
    # Stage & turn management
    # -----------------------------
    if st.session_state.stage == 1:
        if any(
            word in last_user_input.lower()
            for word in ["ready", "sure", "ok", "start", "yes", "yep", "yeah", "yup", "ya", "ready", "sure", "of course", "ok", "okay", "okey", "okie", "okey dokey", "alright", "all right", "start", "begin", "go ahead", "let's", "lets", "sounds good", "why not", "great"]
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
    # Assistant bubble
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
            messages=messages_for_api,
            temperature=0.8,
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

