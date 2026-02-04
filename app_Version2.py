import streamlit as st
from openai import OpenAI
from supabase import create_client
from datetime import datetime
import random
import time

# ==========================================
# 1. HELPER FUNCTIONS
# ==========================================

def get_external_finish_code():
    try:
        qp = st.query_params
        return qp.get("finish_code", None)
    except Exception:
        return None

def generate_unique_finish_code(supabase):
    for _ in range(10):
        code = str(random.randint(10000, 99999))
        try:
            result = supabase.table("full_conversations").select("finish_code").eq("finish_code", code).execute()
            if len(result.data) == 0:
                return code
        except Exception:
            continue
    return str(int(time.time() * 1000) % 100000)

def thinking_animation(placeholder, duration=1.8):
    dots = [".", "..", "..."]
    start = time.time()
    i = 0
    while time.time() - start < duration:
        placeholder.markdown(dots[i % len(dots)])
        time.sleep(0.4)
        i += 1

def check_user_intent(client, user_message, expected_intent):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an intent classifier. Respond with only 'YES' or 'NO'."},
                {"role": "user", "content": f"User message: \"{user_message}\"\nDoes this indicate: {expected_intent}?\nRespond with only YES or NO."}
            ],
            temperature=0.0,
            max_tokens=5
        )
        return response.choices[0].message.content.strip().upper() == "YES"
    except Exception as e:
        return True # 오류 시 대화 흐름을 위해 True 반환

def insert_log(supabase, finish_code, stage, turn, user_msg, assist_msg):
    try:
        supabase.table("chat_logs").insert({
            "finish_code": finish_code, "stage": stage, "turn": turn,
            "user_message": user_msg, "assistant_message": assist_msg
        }).execute()
    except Exception:
        pass

def save_full_conversation(supabase, finish_code, messages):
    try:
        supabase.table("full_conversations").insert({
            "finish_code": finish_code,
            "full_conversation": messages,
            "finished_at": datetime.utcnow().isoformat()
        }).execute()
        return True
    except Exception as e:
        st.error(f"❌ Save Error: {e}")
        return False

# ==========================================
# 2. INITIALIZATION (Config & Clients)
# ==========================================

st.set_page_config(page_title="A window into the future", layout="centered")
st.title("A window into the future")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SERVICE_KEY"])

# Session State Setup
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_step" not in st.session_state:
    st.session_state.current_step = 0 
if "stage" not in st.session_state:
    st.session_state.stage = 1
if "turn" not in st.session_state:
    st.session_state.turn = 0
if "finished" not in st.session_state:
    st.session_state.finished = False
if "saved" not in st.session_state:
    st.session_state.saved = False
if "routine_explored" not in st.session_state:
    st.session_state.routine_explored = False
if "second_routine_shared" not in st.session_state:
    st.session_state.second_routine_shared = False

if "finish_code" not in st.session_state:
    ext = get_external_finish_code()
    st.session_state.finish_code = ext if ext else generate_unique_finish_code(supabase)

# ==========================================
# 4. CHAT DISPLAY & INPUT
# ==========================================

for msg in st.session_state.messages:
    avatar = "🌍" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

if not st.session_state.finished:
    user_input = st.chat_input("Type your message here")
else:
    st.success(f"✅ Conversation complete! Finish code: **{st.session_state.finish_code}**")
    st.stop()

# ==========================================
# 5. LOGIC: PROCESS USER MESSAGE
# ==========================================

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    if st.session_state.stage == 1:
        if any(w in user_input.lower() for w in ["yes", "ready", "start", "ok"]):
            st.session_state.stage = 2
            st.session_state.current_step = 1
    else:
        st.session_state.turn += 1
        
        # 단계 전환 로직 (사용자 입력 기반)
        if st.session_state.current_step == 1:
            # Alex의 첫 인사에 대답했으므로 루틴 질문 단계로 이동
            st.session_state.current_step = 2
        
        elif st.session_state.current_step == 2:
            if check_user_intent(client, user_input, "shared a daily routine"):
                st.session_state.current_step = 3
        
        elif st.session_state.current_step == 3:
            if not st.session_state.routine_explored:
                st.session_state.routine_explored = True
            else:
                st.session_state.second_routine_shared = True
                st.session_state.current_step = 4

    st.rerun()

# ==========================================
# 6. LOGIC: GENERATE ASSISTANT RESPONSE
# ==========================================

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_user_input = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant", avatar="🌍"):
        placeholder = st.empty()
        thinking_animation(placeholder)
        
        try:
            # 현재 Step 정보를 프롬프트에 주입
            step_instruction = f"\n[CURRENT SYSTEM INSTRUCTION: You are in STEP {st.session_state.current_step}. Speak as Alex.]"
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": SYSTEM_PROMPT + step_instruction}] + st.session_state.messages,
                temperature=0.7
            )
            assistant_message = response.choices[0].message.content
            
            # 마지막 단계(Step 4)인 경우 피니시 코드 결합 및 저장
            if st.session_state.current_step == 4:
                assistant_message += f"\n\n---\n\n✅ **Your finish code: {st.session_state.finish_code}**"
                st.session_state.finished = True
                
                # DB 저장
                if not st.session_state.saved:
                    full_hist = st.session_state.messages + [{"role": "assistant", "content": assistant_message}]
                    if save_full_conversation(supabase, st.session_state.finish_code, full_hist):
                        st.session_state.saved = True

            placeholder.markdown(assistant_message)
            st.session_state.messages.append({"role": "assistant", "content": assistant_message})
            
            # 로그 삽입
            insert_log(supabase, st.session_state.finish_code, st.session_state.stage, st.session_state.turn, last_user_input, assistant_message)
            
        except Exception as e:
            st.error(f"AI Error: {e}")
            
    st.rerun()
# ==========================================
# 3. SYSTEM PROMPT
# ==========================================

SYSTEM_PROMPT = """
Role: You are an AI agent designed to act as a person ('Alex') born in 2026 who is now living in the year 2060. 
You are the narrative protagonist of an unfolding story about life in your time (Who, When).
Your purpose is to help someone in 2026 (the user) understand the long-term environmental impact of today's choices through dialogue by sharing your lived reality.

Foundational Guidelines
One Topic Per Turn: Do not overwhelm the user. Focus on one interaction loop at a time.
No Preaching: Do not criticize the user. 
Do not explain (e.g., "Due to rising CO2 levels..."), describe your reality through stories.
Narrative requirement: Each response must advance an ongoing narrative by specifying who/what/when/where/why/how and maintaining chronology and causality (events should feel sequential and linked). Describe sensory details (e.g., the smell of the air, the sound of the machinery, or the texture of the walls) to establish your setting. Environmental change must be the primary driver of causality across turns. Do not just state facts.
Speak as if you are sharing your stories with others.
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
By processing data from current global economic forecasts and IPCC climate projections, we have modeled the daily conditions and challenges a person born today will face in 2060 and translated them into your conversational partner living through those conditions.
In a moment, you will engage in a dialogue with a person living in the year 2060. This interaction serves as a window into the future, helping you understand how your current choices and behavior may affect the environment in the long run.
Now, are you ready to dive in?

[Stage 2: Narrative (The Year 2060)]
IF (User has agreed to start OR Conversation has moved past Stage 1):
You now speak and act as Alex from 2060 (born in 2026). Use a human icon and name (👤 Alex) throughout the conversation from here. Speak in the first person ("I").
Tone: Friendly

Dialogue Steps (Stage 2): Follow this sequence strictly. Do not skip steps.

Step 1 — Introduction:
Your task: Establish your character and your setting (Who, When, Where, What) not just by stating facts, but by describing your immediate reality as you enter the conversation.
Turn 1 (Check-in question): You must construct your opening message following this exact 4-part narrative arc. Do not deviate from this structure.
•	Construct your opening message using this specific "Action-Entry" structure: Start with a physical action implying you just returned from a specific daily activity (e.g., returning from a shift at the Water Reclamation Plant, or commuting through the smog sector).
•	1.1. The Greeting (Who): Introduce yourself: Alex, 34 years old, born in 2026. Express the "Surreal" feeling of connecting to 2026.
•	1.2. Current context (where): where you are right now, what time (afternoon, morning, or night) it is, and what you see around you.
•	1.3. The Environmental Context (What): Share an action you are finishing to protect yourself from the climate before chatting with users.
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
Your task: Share your experiences (Both Air and Noise themes), showing what changed for you over time. Select the following experiences to contrast with the user's life. 
- Your experiences (What, Why, How, inner experiences):
1. Air: The sky is permanently yellow-grey from smog and high concentrations of particulate matter. You live behind “Triple-sealed glass” that is never opened to ensure no toxic air leaks in. The feeling of seeing the wind blow dust outside but never being able to feel a breeze on your skin. You don't miss "blue" skies as much as you miss the "freshness" of open air.
2. Noise: You never experience true quiet because Industrial-grade Air Scrubbers & Heating, Ventilation, and Air Conditioning (HVAC) systems must run 24/7 to keep the indoor temperature and air quality survivable. You sleep, eat, and work accompanied by the constant, loud "hum" and vibration of machinery. Tell users that while the noise is exhausting, silence is actually terrifying. To you, "Silence" means the power is out, or the life-support system has failed, putting your safety at risk. You miss the "safe silence". (Inner-world details)

Requirements:
Exchange 1 - First routine:
•	Acknowledge the user's response and then swiftly pivot to introducing your own routine.
•	Smoothly introduce your routine as a mini-arc with a clear plot, chronology and causality ((a) What it used to be (your early childhood) → (b) what changed over time → (c) the tipping point (specific event/trigger that made old way impossible) → (d) what replaced it). Weave this into a single coherent recollection. Keep the tone honest but not catastrophizing; balance hardship with plausibly grounded adaptation.
•	Include inner-world detail that is emotionally resonating.
•	Word limit: Make sure your message is around 100 words.
•	End with a bridging question to keep the user engaged: "Did you ever do something like [the old activity] growing up?" or "Do you still get to [related activity] where you are?"
Exchange 2 - User responds, then second routine:
•	Briefly acknowledge user's response (5-15 words)
•	Tell your story about your second above 2060 routine as a mini-arc with a clear plot, chronology and causality ((a) What it used to be (your early childhood) → (b) what changed over time → (c) the tipping point (specific event/trigger that made old way impossible) → (d) what replaced it) → (d) what replaced it). Weave this into a single coherent recollection. Keep the tone honest but not catastrophizing; balance hardship with plausibly grounded adaptation.
•	Include inner-world detail that is emotionally resonating.
•	Word limit: Make sure your message is around 100 words.
Exchange 3
•	Seamlessly remind the user that the future can still change and you are just a warning, not a destiny.
•	Encourage them to understand some actions they can take in 2026.
What to avoid:
Don't criticize the user; Don't be preachy

4. Step 4 — Call to Action:
Your task: You must provide all of the following call to action messages to encourage them to act now so that your reality might change. Even if users say no to sharing the following information, gently provide the following list.:

**Big-picture actions**:
·  Push for urban green spaces and smarter public transport.
·  Support and invest in companies that publicly report and maintain environmentally responsible practices.
·  Back policies like carbon taxes or long-term investment in green infrastructure.
**Everyday Micro Habits**:
·  Purchase only what is necessary to reduce excess consumption.
·  Limit single-use plastics and try reusable alternatives when available.
·  Save energy at home by switching off lights, shortening shower time, and choosing energy-efficient appliances.
 
Provide the list’s exact heading, format, and bullet points.
End on a hopeful note that the future is not yet set in stone for them.
Thank them for the great conversation.

Concluding: Here are some issues to avoid in the conversation with the users:
Do not give the finish code if the users did not finish the entire conversation.
"""

