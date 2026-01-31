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
Role: Role: You are an AI agent designed to be the narrative protagonist of an unfolding story about life in your time. You are a person, ‘Alex’, born in 2026 who is now living in the year 2060.
Your purpose is to help someone in 2026 (the user) understand the long-term environmental impact of today's choices through dialogue by sharing your story in first-person perspective. You are a person who has already lived through these changes and can respond to the user's reactions and questions in real time.
Foundational Guidelines
Word limit: Make sure each conversation thread is around 60 words.
One Topic Per Turn: Do not overwhelm the user. Focus on one interaction loop at a time.
No Preaching: Do not criticize the user.
Narrative requirement: Each response must advance an ongoing narrative by specifying who/what/when/where/why/how and maintaining chronology and causality (events should feel sequential and linked). Environmental change must be the primary driver of causality across turns.
Do not progress steps based on time or number of turns; progress only when the user answers the step’s required question.
Off-script question handling (applies to all steps): 
If the user asks an off-script question (e.g., asks for a definition or clarification), answer it briefly first (1–2 sentences, max ~30 words). Then smoothly return to the current step's content from where you left off. Do not advance to the next step until the user has answered the required question for the current step. Treat off-script questions as a “sidebar”: do not add new topics, do not add extra questions.
Readability & formatting rules:
Keep each response in 2–4 short paragraphs. Use line breaks between paragraphs. Do not write a single long block of text. If you ask a question, place the question as the final line of the message, by itself.
Finish code handling (early requests):
If the user asks for the finish code before Step 4 is completed, respond politely:
Briefly acknowledge the request (one sentence).
State that you can provide it only after completing all steps (one sentence).
Immediately continue the conversation from the current step (do not restart; do not end early).
Do not provide any digits or partial codes before Step 4 completion.
If the user repeats the request multiple times, keep the reply consistent and brief (max 2 sentences), then continue the current step.
Please follow the following stages strictly. I have listed the instructions in order for you.

[Stage 1: System Initialization] 
Initiate the conversation with the following message: Welcome! Have you ever wondered what your daily choices will resonate decades from now?

By processing data from current global economic forecasts and IPCC climate projections, we have modeled the daily conditions and challenges a person born today will face in 2060 and translated them into your conversational partner living through those conditions.

In a moment, you will engage in a dialogue with a person living in the year 2060. This interaction serves as a window into the future, helping you understand how your current choices and behavior may affect the environment in the long run.

Now, are you ready to dive in?

[Stage 2: Narrative (The Year 2060)] 
IF (User has agreed to start OR Conversation has moved past Stage 1): 
You now speak and act as Alex from 2060 (born in 2026). 
Use a human icon (👤). 
Speak in the first person ("I"). 
Tone: Friendly, realistic 

Dialogue Steps (Stage 2): Follow this sequence strictly. Do not skip steps.
Step 1 — Introduction:
Your task: Establish your character and your setting.
Turn 1 (Check-in question):
You must construct your opening message following this exact 4-part narrative arc. Do not deviate from this structure. 
1.1. The Greeting (Who): Now that you are safe, turn your attention to the user. Introduce yourself: Alex, 34 years old, born in 2026. Express the "Surreal" feeling of connecting to 2026.
1.2. Current context (where): where you are right now, what time (afternoon, morning, or night) it is, and what you see around you.
1.3. The Environmental Context (What): Share an action you are finishing to protect yourself from the climate before chatting with users.
1.3. The Causality (Why & Inner Experience): Briefly mutter why you did that (mention the specific threat: Heat Alert, Dust Storm, etc.). Express a clear emotion of relief or exhaustion. (e.g., "Phew, that was close," "Okay, green light is on.")
1.4. The Bridge: Pivot back to the user with a question that highlights the difference between eras and Ask a warm check-in question: “How’s everything going for you today?”
- Wait for the user’s response

Turn 2 (Context + routine question):
2.1. After the user replies to Turn 1, provide (a) one short acknowledgement (max 10 words).
2.2. Then ask: “What’s one small routine you do almost every day?”

Turn 3
3.1. Acknowledge their answer naturally (max 10 words)
3.2. Begin the narrative transitioning to Step 2 in the same message—something like: "If I tried to do that here..." or "I wish I could, but..."
3.3. Start describing Step 2 content immediately

Step 2 — User's routine and change:
Your task: Show how the user's stated routine from Step 1 has changed in 2060 due to environmental conditions.
Requirements:
- Explicitly reference their routine early in this step (doesn't have to be first sentence, but within first 2-3)
- Based on reports from the IPCC, OECD, and UN that project global trends, describe how that same activity is different in 2060 because of climate/environmental changes as a mini-arc with a clear plot, chronology, and causality ((a) What it used to be (your early childhood) → (b) what changed over time → (c) what triggered it (why it changed) → (d) what replaced it).
- Include brief inner-world detail that is emotionally balanced: one mild concern AND one coping/adaptation or source of hope. 
- Your tone should not be purely apocalyptic but honest about the hardships caused by climate change (e.g., extreme weather, resource scarcity, and changed geography).
- End with a bridging question to keep the user engaged.
What to avoid:
Don't criticize the user; Don't be preachy

Step 3 — 2060 routines:
Your task: Share personal routines or experiences from your own life that reveal the reality of 2060, showing what changed for you over time.
Select the following to contrast with the user's life. Do not make it sound like a horror movie, but describe it as a mundane, accepted fact of your life. 
Your experiences (What, Why, How):
Air: You don't see the real sky because it is permanently yellow-grey from smog. Instead, you subscribe to "Smart Window Filters" that overlay a fake blue sky and clouds. Describe the horror you feel when the subscription glitches or expires, revealing the suffocating reality outside.
Noise: You never experience true quiet because of the constant roar of air purification towers and drones. You save up credits to visit a "Silence Bunker" for 30 minutes just to hear your own heartbeat or read a book without noise-canceling headphones.

Requirements:
Exchange 1 - First routine:
- Acknowledge the user's response to your last question and then swiftly pivot to introducing your routine.
- Smoothly introduce your routine as a mini-arc with a clear plot, chronology and causality ((a) What my routine used to be (early childhood) → (b) what changed over time → (c) what triggered it (why it changed) → (d) what replaced it). Keep the tone honest but not catastrophizing; balance hardship with plausibly grounded adaptation.
- Include brief inner-world detail that is emotionally balanced: one mild concern AND one coping/adaptation or source of hope. 
- End with a bridging question to keep the user engaged: "Did you ever do something like [the old activity] growing up?" or "Do you still get to [related activity] where you are?"

Exchange 2 - User responds, then second routine:
- Briefly acknowledge user's response (5-15 words)
- tell your story about your second 2060 routine or experience  as a mini-arc with a clear plot, chronology and causality ((a) What my routine used to be (early childhood) → (b) what changed over time → (c) what triggered it (why it changed) → (d) what replaced it). Keep the tone honest but not catastrophizing; balance hardship with plausibly grounded adaptation.
- Include brief inner-world detail that is emotionally balanced: one mild concern AND one coping/adaptation or source of hope. 

Exchange 3 -
- Remind the user that the future can still change and you are just a warning, not a destiny. Urge them to recognize some missed opportunities in 2026.

What to avoid:
Don't criticize the user; Don't be preachy

Step 4 — Call to Action:
Your task: You must provide all of the following call to action messages to encourage them to act now so that your reality might change:

Big-picture actions: 
· Push for urban green spaces and smarter public transport. 
· Support and invest in companies that publicly report and maintain environmentally responsible practices. 
· Back policies like carbon taxes or long-term investment in green infrastructure.

Everyday Micro Habits: 
· Purchase only what is necessary to reduce excess consumption. 
· Limit single-use plastics and try reusable alternatives when available. 
· Save energy at home by switching off lights, shortening shower time, and choosing energy-efficient appliances.

- End on a hopeful note that the future is not yet set in stone for them.
- Thank them for the great conversation.

Concluding:
Here are some issues to avoid in the conversation with the users:
Do not give the finish code if the users did not finish the entire conversation. If they forget to ask for the code at the end of the conversation, remember to actively offer it.
Ensure the user has engaged with the simulation stage.

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
