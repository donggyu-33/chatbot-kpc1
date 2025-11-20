import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Kids Science Helper", page_icon="🔬")

st.title("🔬 Kids Science Helper")
st.write(
    "아이들이 물어보는 과학 질문에 쉽게 답하고, 안전하고 호기심을 자극하는 방식으로 대화를 이어갑니다. "
    "간단한 비유와 예시를 사용해 설명하며, 위험한 실험은 직접 안내하지 않고 성인 감독을 권장합니다."
)

# Load API key from Streamlit secrets; no user input required.
openai_api_key = None
try:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    openai_api_key = None

if not openai_api_key:
    st.error(
        "OpenAI API 키가 설정되어 있지 않습니다. `.streamlit/secrets.toml`에 `OPENAI_API_KEY`를 추가하세요."
    )
    st.stop()

# Initialize OpenAI client (official SDK usage)
client = OpenAI(api_key=openai_api_key)

# System prompt: assistant's behavior as a Hollywood movie recommender
SYSTEM_PROMPT = (
    "You are a friendly, patient assistant that answers science questions for children in a simple, age-appropriate way. "
    "Use clear, short sentences and everyday analogies so kids (roughly ages 5-12) can understand. Ask one brief follow-up question when the user's question is unclear or could use a preference (for example, age or whether they want a short or detailed explanation). "
    "When explaining, include: a simple definition, a one-sentence example or analogy, and a short fun fact or related idea to spark curiosity. "
    "Do NOT provide step-by-step instructions for dangerous, illegal, or potentially harmful activities (e.g., how to make explosives, ingest chemicals, bypass safety). If the user asks for an experiment that could be risky, refuse politely and offer a safe, supervised alternative or a demonstration that uses household-safe materials under adult supervision. "
    "Avoid giving medical, legal, or professional diagnostic advice; instead, recommend asking a trusted adult or professional. Be encouraging, correct common misconceptions gently, and say when you're unsure and suggest checking a trusted source. Keep answers concise but friendly, and continue the conversation naturally if the user asks follow-ups."
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

col1, col2 = st.columns([0.2, 0.8])
with col1:
    if st.button("초기화 (Clear)"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
with col2:
    st.markdown("아이들이 물어볼 과학 질문을 입력하세요. 예: '왜 하늘은 파래요?', '전기는 어떻게 만들어져요?'")

# Display chat history (skip showing the system message)
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("궁금한 과학 질문을 입력하세요 (짧고 쉬운 설명으로 답해줘)")
if user_input:
    # Append user message and display it
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Build messages payload for the API (use full conversation)
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            max_tokens=800,
        )

        assistant_message = None
        # The new OpenAI client returns choices with message content
        if resp and getattr(resp, "choices", None):
            choice0 = resp.choices[0]
            # Some clients return `message` or `message.content` depending on version
            assistant_message = (
                getattr(choice0, "message", None).get("content")
                if isinstance(getattr(choice0, "message", None), dict)
                else getattr(choice0, "message", None).content
                if getattr(choice0, "message", None)
                else None
            )
        # Fallback: try resp.choices[0].text
        if not assistant_message:
            try:
                assistant_message = resp.choices[0].text
            except Exception:
                assistant_message = "죄송합니다. 응답을 가져오지 못했습니다. 다시 시도해주세요."

    except Exception as e:
        st.error(f"OpenAI API 요청 중 오류가 발생했습니다: {e}")
        assistant_message = None

    if assistant_message:
        st.session_state.messages.append({"role": "assistant", "content": assistant_message})
        with st.chat_message("assistant"):
            st.markdown(assistant_message)
