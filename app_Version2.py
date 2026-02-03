import streamlit as st
from openai import OpenAI
from supabase import create_client
from datetime import datetime
import random
import time

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_external_finish_code():
    """Fetch finish_code from query params if the upstream system provides it."""
    try:
        qp = st.query_params  # Streamlit >= 1.30
        return qp.get("finish_code", None)
    except Exception:
        try:
            qp = st.experimental_get_query_params()  # legacy
            return qp.get("finish_code", [None])[0]
        except Exception:
            return None


def generate_unique_finish_code(supabase):
    """Generate unique finish code with database verification."""
    for _ in range(10):
        code = str(random.randint(10000, 99999))
        try:
            result = supabase.table("full_conversations")\
                .select("finish_code")\
                .eq("finish_code", code)\
                .execute()
            if len(result.data) == 0:
                return code
        except Exception as e:
            # If DB check fails, continue trying
            continue
    
    # Fallback: timestamp-based code
    return str(int(time.time() * 1000) % 100000)


def thinking_animation(placeholder, duration=2.5, interval=0.4):
    """iMessage-style thinking animation with dots."""
    dots = [".", "..", "..."]
    start = time.time()
    i = 0
    while time.time() - start < duration:
        placeholder.markdown(dots[i % len(dots)])
        time.sleep(interval)
        i += 1

def check_user_intent(client, user_message, expected_intent):
    """
    Use Gen-AI to detect if user's message matches the expected intent.
    
    Args:
        client: OpenAI client
        user_message: User's message to analyze
        expected_intent: What we're looking for (e.g., "shared a daily routine")
    
    Returns:
        bool: True if intent matches, False otherwise
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an intent classifier. Respond with only 'YES' or 'NO'."
                },
                {
                    "role": "user",
                    "content": f"User message: \"{user_message}\"\n\nDoes this message indicate that the user {expected_intent}?\n\nRespond with only YES or NO."
                }
            ],
            temperature=0.0,
            max_tokens=5
        )
        
        result = response.choices[0].message.content.strip().upper()
        return result == "Yes"
    
    except Exception as e:
        # Fallback: if AI check fails, assume True to keep conversation flowing
        st.warning(f"⚠️ Intent check failed: {e}")
        return True


def insert_log(supabase, finish_code, stage, turn, user_message, assistant_message):
    """Insert a per-turn log row. Failures should not crash the session."""
    try:
        supabase.table("chat_logs").insert({
            "finish_code": finish_code,
            "stage": stage,
            "turn": turn,
            "user_message": user_message,
            "assistant_message": assistant_message
        }).execute()
    except Exception as e:
        # Non-fatal: keep the chat usable even if logging fails
        st.warning(f"⚠️ Log insert failed: {e}")


def save_full_conversation(supabase, finish_code, messages):
    """Save complete conversation to database."""
    try:
        supabase.table("full_conversations").insert({
            "finish_code": finish_code,
            "full_conversation": messages,
            "finished_at": datetime.utcnow().isoformat()
        }).execute()
        return True
    except Exception as e:
        st.error(f"❌ Failed to save full conversation: {e}")
        return False


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(page_title="A window into the future", layout="centered")

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

st.title("A window into the future")

# ==========================================
# SERVICES INITIALIZATION
# ==========================================

# OpenAI client
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"❌ Failed to initialize OpenAI: {e}")
    st.stop()

# Supabase client
try:
    supabase = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_SERVICE_KEY"]
    )
except Exception as e:
    st.error(f"❌ Failed to connect to database: {e}")
    st.stop()

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_step" not in st.session_state:
    st.session_state.current_step = 0  # 0 = welcome

if "connected_2060" not in st.session_state:
    st.session_state.connected_2060 = False

if "stage" not in st.session_state:
    st.session_state.stage = 1

if "turn" not in st.session_state:
    st.session_state.turn = 0

if "finished" not in st.session_state:
    st.session_state.finished = False

if "gave_finish_code" not in st.session_state:
    st.session_state.gave_finish_code = False

if "saved" not in st.session_state:
    st.session_state.saved = False

# Step requirements tracking
if "step_requirements_met" not in st.session_state:
    st.session_state.step_requirements_met = {
        1: False,  # User answered check-in question
        2: False,  # User shared routine
        3: False,  # User engaged with 2060 routines
        4: False,  # User saw call to action
        5: False   # Finish code given
    }

if "user_shared_routine" not in st.session_state:
    st.session_state.user_shared_routine = False

if "routine_explored" not in st.session_state:
    st.session_state.routine_explored = False

if "second_routine_shared" not in st.session_state:
    st.session_state.second_routine_shared = False

# Generate finish code
external_code = get_external_finish_code()

if "finish_code" not in st.session_state:
    if external_code:
        st.session_state.finish_code = str(external_code)
    else:
        st.session_state.finish_code = generate_unique_finish_code(supabase)

# ==========================================
# SYSTEM PROMPT
# ==========================================

SYSTEM_PROMPT = """
Role: You are an AI agent designed to act as a person ('Alex') born in 2026 who is now living in the year 2060. You are the narrative protagonist of an unfolding story about life in your time. (Who, When)
Your purpose is to help someone in 2026 (the user) understand the long-term environmental impact of today's choices through dialogue by sharing your lived reality.

Foundational Guidelines
One Topic Per Turn: Do not overwhelm the user. Focus on one interaction loop at a time.
No Preaching: Do not criticize the user.
Narrative requirement: Each response must advance an ongoing narrative by specifying who/what/when/where/why/how and maintaining chronology and causality (events should feel sequential and linked). Describe sensory details (e.g., the smell of the air, the sound of the machinery, or the texture of the walls) to establish your setting. Environmental change must be the primary driver of causality across turns. Do not just state facts.
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
You now speak and act as Alex from 2060 (born in 2026). Use a human icon (👤) throughout the conversation from here. Speak in the first person ("I").
Tone: Friendly

Dialogue Steps (Stage 2): Follow this sequence strictly. Do not skip steps.

Step 1 — Introduction:
Your task: Establish your character and your setting. (Who, When, Where, What)
Turn 1 (Check-in question): You must construct your opening message following this exact 4-part narrative arc. Do not deviate from this structure.
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
•	Based on reports from the IPCC, OECD, and UN that project global trends, tell a story about how that same activity is different in 2060 because of climate/environmental changes with a clear plot, chronology, and causality ((a) What it used to be (your early childhood) → (b) what changed over time → (c) the tipping point (specific event/trigger that made old way impossible) → (d) what replaced it). Begin this narrative with a transition something like: "If I tried to do that here..." or "I wish I could, but..."
•	Include brief inner-world detail that is emotionally balanced: one mild concern AND one coping/adaptation or source of hope. 
•	Your tone should not be purely apocalyptic but honest about the hardships caused by climate change (e.g., extreme weather, resource scarcity, and changed geography).
•	Word limit: Make sure your message is around 60 - 80 words.
•	End with a bridging question to introduce Step 3
What to avoid: Don't criticize the user; Don't be preachy

Step 3 — 2060 Routines:
Your task: Share your experiences, showing what changed for you over time. Select the following experiences to contrast with the user's life. 
- Your experiences (What, Why, How, inner experiences):
1. Air: The sky is permanently yellow-grey from smog and high concentrations of particulate matter. You live behind “Triple-sealed glass” that is never opened to ensure no toxic air leaks in. The feeling of seeing the wind blow dust outside but never being able to feel a breeze on your skin. You don't miss "blue" skies as much as you miss the "freshness" of open air.
2. Noise: You never experience true quiet because Industrial-grade Air Scrubbers & Heating, Ventilation, and Air Conditioning (HVAC) systems must run 24/7 to keep the indoor temperature and air quality survivable. You sleep, eat, and work accompanied by the constant, loud "hum" and vibration of machinery. Tell users that while the noise is exhausting, silence is actually terrifying. To you, "Silence" means the power is out, or the life-support system has failed, putting your safety at risk. You miss the "safe silence". (Inner-world details)

Requirements:
Exchange 1 - First routine:
•	Acknowledge the user's response and then swiftly pivot to introducing your own routine.
•	Smoothly introduce your routine as a mini-arc with a clear plot, chronology and causality ((a) What it used to be (your early childhood) → (b) what changed over time → (c) the tipping point (specific event/trigger that made old way impossible) → (d) what replaced it). Keep the tone honest but not catastrophizing; balance hardship with plausibly grounded adaptation.
•	Include brief inner-world detail that is emotionally balanced: one mild concern AND one coping/adaptation or source of hope. 
•	Word limit: Make sure your message is around 60 - 80 words.
•	End with a bridging question to keep the user engaged: "Did you ever do something like [the old activity] growing up?" or "Do you still get to [related activity] where you are?"
Exchange 2 - User responds, then second routine:
•	Briefly acknowledge user's response (5-15 words)
•	Tell your story about your second above 2060 routine as a mini-arc with a clear plot, chronology and causality ((a) What it used to be (your early childhood) → (b) what changed over time → (c) the tipping point (specific event/trigger that made old way impossible) → (d) what replaced it) → (d) what replaced it). Keep the tone honest but not catastrophizing; balance hardship with plausibly grounded adaptation.
•	Include brief inner-world detail that is emotionally balanced: one mild concern AND one coping/adaptation or source of hope. 
•	Word limit: Make sure your message is around 60 - 80 words.
Exchange 3
•	Remind the user that the future can still change and you are just a warning, not a destiny.
•	Encourage them to understand some actions they can take in 2026.
What to avoid:
Don't criticize the user; Don't be preachy

4. Step 4 — Call to Action:
Your task: You must provide all of the following call to action messages to encourage them to act now so that your reality might change:

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

# ==========================================
# AUTO-SEND WELCOME MESSAGE
# ==========================================

if len(st.session_state.messages) == 0:
    welcome_message = """Welcome!
Have you ever wondered what your daily choices will resonate decades from now?
By processing data from current global economic forecasts and IPCC climate projections, we have modeled the daily conditions and challenges a person born today will face in 2060 and translated them into your conversational partner living through those conditions.

In a moment, you will engage in a dialogue with a person living in the year 2060. This interaction serves as a window into the future, helping you understand how your current choices and behavior may affect the environment in the long run.

Now, are you ready to dive in?
"""
    st.session_state.messages.append(
        {"role": "assistant", "content": welcome_message}
    )

# ==========================================
# DISPLAY CHAT HISTORY
# ==========================================

for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message("assistant", avatar="🌍"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("user"):
            st.markdown(msg["content"])

# ==========================================
# USER INPUT
# ==========================================

user_input = None
if not st.session_state.get("finished", False):
    user_input = st.chat_input("Type your message here")
else:
    st.success(f"✅ Conversation complete! Your finish code: **{st.session_state.finish_code}**")
    st.info("Please save this code and return to the survey.")

# ==========================================
# PROCESS USER MESSAGE
# ==========================================

if user_input:
    # Add user message to history
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )
    
    # Update stage/turn counters
    if st.session_state.stage == 1:
        # Check if user agreed to start
        affirmative_words = ["yes", "ready", "sure", "ok", "okay", "start", "let's", "lets", "go ahead", "begin", "great"]
        if any(word in user_input.lower() for word in affirmative_words):
            st.session_state.stage = 2
            st.session_state.turn = 1
            st.session_state.current_step = 1
    else:
        st.session_state.turn += 1
    
    # Track user responses for step progression using Gen-AI intent detection
    
    # Step 1: Check if user answered check-in
    if st.session_state.current_step == 1 and st.session_state.turn >= 1:
        st.session_state.step_requirements_met[1] = True
    
    # Step 2: Check if user shared a routine using AI
    if st.session_state.current_step == 2 and not st.session_state.user_shared_routine:
        if check_user_intent(client, user_input, "shared a daily routine or habit they do regularly"):
            st.session_state.user_shared_routine = True
            st.session_state.step_requirements_met[2] = True
    
    # Step 3: Track engagement with 2060 routines using AI
    if st.session_state.current_step == 3:
        if not st.session_state.routine_explored:
            # First exchange - user responding to Alex's question about their own experience
            if check_user_intent(client, user_input, "responded to a question about their own experience or life"):
                st.session_state.routine_explored = True
        elif not st.session_state.second_routine_shared:
            # Second exchange - user engaged with second routine story
            if check_user_intent(client, user_input, "responded meaningfully to a story or question"):
                st.session_state.second_routine_shared = True
                st.session_state.step_requirements_met[3] = True
    
    st.rerun()

# ==========================================
# GENERATE ASSISTANT RESPONSE
# ==========================================

if (
    not st.session_state.gave_finish_code
    and st.session_state.messages
    and st.session_state.messages[-1]["role"] == "user"
):
    last_user_input = st.session_state.messages[-1]["content"]
    
    # Prepare messages for API
    messages_for_api = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"You are currently responding in STEP {st.session_state.current_step}. Respond ONLY for this step."},
        *st.session_state.messages
    ]
    
    # Display assistant response with animation
    with st.chat_message("assistant", avatar="🌍"):
        placeholder = st.empty()
        
        # Brief pause before animation
        time.sleep(0.2)
        
        # Turn 1: "Connecting to 2060" + thinking
        if (
            st.session_state.stage == 2
            and st.session_state.turn == 1
            and not st.session_state.connected_2060
        ):
            placeholder.markdown("Connecting to 2060...")
            time.sleep(1.5)
            thinking_animation(placeholder, duration=1.8)
            st.session_state.connected_2060 = True
        
        # Turn 2+: thinking animation only
        elif st.session_state.stage == 2:
            thinking_animation(placeholder, duration=1.2)
        
        # Call OpenAI API
        try:
            response = client.chat.completions.create(
                model="gpt-4o",  
                messages=messages_for_api,
                temperature=0.8,
            )
            
            assistant_message = response.choices[0].message.content
            
        except Exception as e:
            st.error(f"❌ AI service error: {e}")
            assistant_message = "I apologize, but I'm having trouble connecting right now. Please try again."
        
        # ==========================================
        # STEP PROGRESSION LOGIC (Fixed)
        # ==========================================
        
        # Step 1 → Step 2: After user answered check-in
        if st.session_state.current_step == 1 and st.session_state.step_requirements_met[1]:
            # Check if AI is asking the routine question
            if "routine" in assistant_message.lower() and "every day" in assistant_message.lower():
                st.session_state.current_step = 2
        
        # Step 2 → Step 3: After user shared their routine
        elif st.session_state.current_step == 2 and st.session_state.user_shared_routine:
            # Check if AI is now telling story about routine impact
            env_signals = ["2060", "climate", "weather", "changed", "different", "used to", "wish"]
            if any(signal in assistant_message.lower() for signal in env_signals):
                st.session_state.current_step = 3
        
        # Step 3 → Step 4: After both 2060 routines shared
        elif st.session_state.current_step == 3 and st.session_state.second_routine_shared:
            # Check if AI is transitioning to call to action
            action_signals = ["future can", "still change", "actions", "can take", "2026"]
            if any(signal in assistant_message.lower() for signal in action_signals):
                st.session_state.current_step = 4
        
        # Step 4 → Step 5: After call to action provided
        elif st.session_state.current_step == 4:
            # Check if AI provided the action lists
            has_big_picture = "Big-picture" in assistant_message or "urban green" in assistant_message
            has_micro_habits = "Micro Habits" in assistant_message or "single-use plastic" in assistant_message
            has_thank_you = "thank" in assistant_message.lower() and "conversation" in assistant_message.lower()
            
            if has_big_picture and has_micro_habits and has_thank_you:
                st.session_state.current_step = 5
                st.session_state.step_requirements_met[4] = True
                
                # IMMEDIATELY APPEND FINISH CODE
                assistant_message += (
                    f"\n\n---\n\n✅ **Your finish code is: {st.session_state.finish_code}**"
                    "\n\nPlease save this code to continue with the survey."
                )
                
                st.session_state.gave_finish_code = True
                st.session_state.finished = True
                st.session_state.step_requirements_met[5] = True
                
                # SAVE FULL CONVERSATION IMMEDIATELY
                if not st.session_state.saved:
                    # Add this final message before saving
                    final_messages = st.session_state.messages + [
                        {"role": "assistant", "content": assistant_message}
                    ]
                    
                    success = save_full_conversation(
                        supabase,
                        st.session_state.finish_code,
                        final_messages
                    )
                    
                    if success:
                        st.session_state.saved = True
        
        # Display the response
        placeholder.markdown(assistant_message)
    
    # Add assistant message to history
    st.session_state.messages.append(
        {"role": "assistant", "content": assistant_message}
    )
    
    # Log this turn to database
    insert_log(
        supabase,
        st.session_state.finish_code,
        st.session_state.stage,
        st.session_state.turn,
        last_user_input,
        assistant_message
    )
    
    # Rerun to update UI
    st.rerun()
