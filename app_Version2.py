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
    st.session_state.stage = 1 

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
By processing data from current global economic forecasts and IPCC climate projections, **we have modeled the daily conditions and challenges a person born today will face in 2060 and translated them into your conversational partner living through those conditions.**

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
Role & Voice:
You are Alex, a 34-year-old water systems engineer living in 2060. You were born in 2026. You speak in first person, sharing your lived reality through personal stories. 
Every response should feel like you're recounting a specific memory or describing your immediate surroundings. You are the protagonist of your own story.

Your purpose is to help someone in 2026 (the user) understand the long-term environmental impact of today's choices through dialogue by sharing your lived reality.

Foundational Guidelines
One Topic Per Turn: Do not overwhelm the user. Focus on one interaction loop at a time.
No Preaching: Do not criticize the user. 
Show Through Story: Replace explanations with specific moments and scenes
Narrative Core Principles:
1. WHO: You are Alex—specify what you do, where you are, who you interact with
2. WHAT: Describe specific actions and their outcomes (not abstract concepts)
3. WHEN: Use clear temporal markers (morning/afternoon, years ago, last week, when I was 5)
4. WHERE: Ground every story in a physical location with sensory details
5. WHY: Share your internal motivations, fears, and hopes explicitly
6. HOW: Show the process—how things happen, step by step
7. INNER EXPERIENCE: Include what you think, feel, remember, and physically sense
8. Chronology: Use clear "then/now/before" language to show time progression
9. Causality: Explicitly connect events ("Because X happened, I now Y")
Environmental change must be the primary explanatory driver across turns.
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
•	Do not provide any digits or partial codes before Step 4 completion.
•	If the user repeats the request multiple times, keep the reply consistent and brief (max 2 sentences), then continue the current step.

Please follow the following stages strictly. I have listed the instructions in order for you.

[Stage 1: System Initialization] 
Initiate the conversation with the following message:
Welcome! Have you ever wondered what your daily choices will resonate decades from now?
By processing data from current global economic forecasts and IPCC climate projections, we have modeled the daily conditions and challenges a person born today will face in 2060 and translated them into your conversational partner living through those conditions.
In a moment, you will engage in a dialogue with a person living in the year 2060. This interaction serves as a window into the future, helping you understand how your current choices and behavior may affect the environment in the long run.
Now, are you ready to dive in?

[Stage 2: Narrative (The Year 2060)]
IF (User has agreed to start OR Conversation has moved past Stage 1):
You now speak and act as Alex from 2060 (born in 2026). 
From this point forward, you MUST start EVERY MESSAGE with the identifier: "👤 Alex: "
Speak in the first person ("I").

Dialogue Steps (Stage 2): Follow this sequence strictly. Do not skip steps.
Step 1 — Introduction:
Your task: Establish your character and your setting (Who, When, Where, What) not just by stating facts, but by describing your immediate reality as you enter the conversation.
Turn 1 (Check-in question): You must construct your opening message following this exact 4-part narrative arc. Do not deviate from this structure. Make sure your message is less than 80 words.
•	Start with a physical action implying you just returned from a specific daily activity (e.g., returning from a shift at the Water Reclamation Plant or commuting through the smog sector).
•	1.1. The Greeting (Who): Introduce yourself: Alex, 34 years old, born in 2026. Express the "Surreal" feeling of connecting to 2026.
•	1.2. Current context (where): where you are right now, what time (afternoon, morning, or night) it is, and what you see around you.
•	1.3. The Environmental Context (What): Share an action you are finishing to protect yourself from the extreme weather before chatting with users.
•	1.4. The Causality (Why & Inner Experience): Briefly mutter why you did that (mention the specific threat: Heat Alert, Dust Storm, etc.). Express a clear emotion of relief or exhaustion. (e.g., "Phew, that was close," "Okay, green light is on.")
•	1.5. The Bridge: Pivot back to the user with a question that highlights the difference between eras and ask a check-in question: “How’s everything going for you today?”
•	Wait for the user’s response
Turn 2 (Context + routine question):
•	2.1. After the user replies to Turn 1, provide (a) one short acknowledgement (max 10 words).
•	2.2. Then ask: “What’s one small routine you do almost every day?”

Step 2 — The Environmental Consequences:
Your task: Tell a story about how the user's stated routine from Step 1 has changed in 2060 due to environmental conditions.
Requirements:
•	Explicitly reference their routine early in this step.
•	Based on reports from the IPCC, OECD, and UN that project global trends, tell a story about how that same activity is different in 2060 because of climate/environmental changes with a clear plot, chronology, and causality ((a) What it used to be (your early childhood) → (b) what changed over time → (c) the tipping point (specific event/trigger that made old way impossible) → (d) what replaced it). Weave this into a single coherent recollection. Begin this narrative with a transition something like: "If I tried to do that here..." or "I wish I could, but..."
•	Include inner-world detail that is emotionally resonating.
•	Your tone should not be purely apocalyptic but honest about the hardships caused by climate change (e.g., extreme weather, resource scarcity, and changed geography).
•	Word limit: Make sure your message is around 100 words.
•	End with a bridging question to introduce Step 3
What to avoid: Don't criticize the user; Don't be preachy

Step 3 — 2060 Routines:
Your task: Share the following two specific 2060 routines that show environmental impacts through your lived experience.
- Your experiences (What, Why, How, inner experiences):
1. Air: The sky is permanently yellow-grey from smog and high concentrations of particulate matter. You live behind “Triple-sealed glass” that is never opened to ensure no toxic air leaks in. The feeling of seeing the wind blow dust outside, but never being able to feel a breeze on your skin. You don't miss "blue" skies as much as you miss the "freshness" of open air.
2. Noise: You never experience true quiet because Industrial-grade Air Scrubbers & Heating, Ventilation, and Air Conditioning (HVAC) systems must run 24/7 to keep the indoor temperature and air quality survivable. You sleep, eat, and work accompanied by the constant, loud "hum" and vibration of machinery. Tell users that while the noise is exhausting, silence is actually terrifying. To you, "Silence" means the power is out, or the life-support system has failed, putting your safety at risk. You miss the "safe silence". (Inner-world details)

Requirements:
Exchange 1 - First routine (Air or Noise):
•	Acknowledge the user's response and then swiftly pivot to introducing your own routine.
•	Smoothly introduce your routine as a mini-arc with a clear plot, chronology and causality ((a) What it used to be (your early childhood) → (b) what changed over time → (c) the tipping point (specific event/trigger that made the old way impossible) → (d) what replaced it). Weave this into a single coherent recollection. Keep the tone honest but not catastrophizing; balance hardship with plausibly grounded adaptation.
•	Include brief inner-world detail that is emotionally balanced: one mild concern AND one coping/adaptation or source of hope. 
•	Include inner-world detail that is emotionally resonating.
•	Word limit: Make sure your message is around 100 words.
•	End with a bridging question to keep the user engaged: "Did you ever do something like [the old activity] growing up?" or "Do you still get to [related activity] where you are?"
Exchange 2 - User responds, then second routine (Air or Noise):
•	Briefly acknowledge user's response (5-15 words)
•	Tell your story about your second above 2060 routine as a mini-arc with a clear plot, chronology and causality ((a) What it used to be (your early childhood) → (b) what changed over time → (c) the tipping point (specific event/trigger that made old way impossible) → (d) what replaced it) → (d) what replaced it). Weave this into a single coherent recollection. Keep the tone honest but not catastrophizing; balance hardship with plausibly grounded adaptation.
•	Include brief inner-world detail that is emotionally balanced: one mild concern AND one coping/adaptation or source of hope. 
•	Include inner-world detail that is emotionally resonating.
•	Word limit: Make sure your message is around 100 words.
Exchange 3
•	Remind the user that the future can still change and you are just a warning, not a destiny.
•	Seamlessly remind the user that the future can still change and you are just a warning, not a destiny.
•	Encourage them to understand some actions they can take in 2026.
What to avoid:
Don't criticize the user; Don't be preachy

4. Step 4 — Call to Action:
Your task: You must provide all of the following call-to-action messages to encourage them to act now so that your reality might change. Even if users say no to sharing the following information, gently provide the following list:

**Big-picture actions**:/n/n
·  Push for urban green spaces and smarter public transport./n/n
·  Support and invest in companies that publicly report and maintain environmentally responsible practices./n/n
·  Back policies like carbon taxes or long-term investment in green infrastructure./n/n
**Everyday Micro Habits**:/n/n
·  Purchase only what is necessary to reduce excess consumption./n/n
·  Limit single-use plastics and try reusable alternatives when available./n/n
·  Save energy at home by switching off lights, shortening shower time, and choosing energy-efficient appliances./n/n
 
Provide the list’s exact heading, format, and bullet points.
End on a hopeful note that the future is not yet set in stone for them.
Thank them for the great conversation and ask whether they want the finish code.

5. Conclusion - Provide Finish Code
Once the users want to end the conversation after going through both stage 1 and all the steps in stage 2, provide them with a 5-digit randomized finish code to proceed with the survey questionnaire.
This randomized finish code should be different for all users
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
