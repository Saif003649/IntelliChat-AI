import streamlit as st
import google.generativeai as genai
import sqlite3
import os
import uuid
import warnings
from dotenv import load_dotenv

# Suppress deprecation warnings from legacy SDK
warnings.filterwarnings("ignore", category=FutureWarning)

load_dotenv()

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(page_title="IntelliChat AI", page_icon="💬", layout="wide")

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.stApp {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Inter', sans-serif;
}

[data-testid="stSidebar"] {
    background-color: #161b22;
    border-right: 1px solid #30363d;
}

.chat-header {
    padding: 12px 0 20px 0;
    border-bottom: 1px solid #30363d;
    margin-bottom: 20px;
}

.chat-header h2 {
    margin: 0;
    font-weight: 700;
    font-size: 1.6rem;
    color: #58a6ff;
}

.chat-header p {
    margin: 4px 0 0 0;
    color: #8b949e;
    font-size: 0.9rem;
}

.stChatMessage {
    background-color: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 12px !important;
    margin-bottom: 12px !important;
}

div[data-testid="stChatInput"] {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ── Database Setup ───────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_history.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        """)
        conn.commit()

def create_conversation(title="New Conversation"):
    cid = str(uuid.uuid4())[:8]
    with get_db() as conn:
        conn.execute("INSERT INTO conversations (id, title) VALUES (?, ?)", (cid, title))
        conn.commit()
    return cid

def get_all_conversations():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM conversations ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

def delete_conversation(cid):
    with get_db() as conn:
        conn.execute("DELETE FROM conversations WHERE id = ?", (cid,))
        conn.commit()

def rename_conversation(cid, title):
    with get_db() as conn:
        conn.execute("UPDATE conversations SET title = ? WHERE id = ?", (title, cid))
        conn.commit()

def save_message(cid, role, content):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (cid, role, content)
        )
        conn.commit()

def get_messages(cid):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
            (cid,)
        ).fetchall()
        return [dict(r) for r in rows]

init_db()

# ── Session State ────────────────────────────────────────────
if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("GEMINI_API_KEY", "").strip()

if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

if "model_name" not in st.session_state:
    st.session_state.model_name = "gemini-3.8-flash"

if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7

# ── Gemini Service ───────────────────────────────────────────
def call_gemini_stream(messages, api_key, model_name="gemini-3.8-flash", temperature=0.7):
    """Configures and streams responses from Gemini API."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=4096,
        )
    )

    # Format historical turns
    history = []
    for m in messages[:-1]:
        role = "user" if m["role"] == "user" else "model"
        history.append({"role": role, "parts": [m["content"]]})

    chat = model.start_chat(history=history)
    last_prompt = messages[-1]["content"]
    response = chat.send_message(last_prompt, stream=True)
    return response

def auto_generate_title(prompt, api_key, model_name="gemini-3.8-flash"):
    """Generates a concise title for the conversation."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_name)
        res = model.generate_content(
            f"Generate a 3-5 word concise title for this topic. Output ONLY the title text:\n\n{prompt[:150]}"
        )
        title = res.text.strip().replace('"', '').replace("'", "")
        return title[:40] if title else prompt[:25]
    except Exception:
        return prompt[:25] + ("..." if len(prompt) > 25 else "")

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 IntelliChat AI")
    st.caption("Simple & Fast Gemini Chatbot")

    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        st.session_state.current_chat = None
        st.rerun()

    st.markdown("---")

    # API Key Configuration
    with st.expander("🔑 API Key Settings", expanded=not bool(st.session_state.api_key)):
        entered_key = st.text_input(
            "Gemini API Key:",
            value=st.session_state.api_key,
            type="password",
            placeholder="Paste your key here",
            help="Get your key at aistudio.google.com/apikey"
        )
        if st.button("Save Key", use_container_width=True):
            st.session_state.api_key = entered_key.strip()
            # Update .env file
            env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
            with open(env_file, "w") as f:
                f.write(f"GEMINI_API_KEY={entered_key.strip()}\n")
            st.success("API Key saved!")
            st.rerun()

        if st.session_state.api_key:
            st.caption("🟢 API key loaded")
        else:
            st.caption("🔴 Please provide an API key")

    # Model Settings
    with st.expander("⚙️ Model Settings"):
        available_models = ["gemini-3.8-flash", "gemini-2.5-pro", "gemini-flash-latest"]
        st.session_state.model_name = st.selectbox(
            "Model:",
            available_models,
            index=0 if st.session_state.model_name not in available_models else available_models.index(st.session_state.model_name)
        )
        st.session_state.temperature = st.slider(
            "Creativity (Temperature):",
            min_value=0.0,
            max_value=1.5,
            value=float(st.session_state.temperature),
            step=0.1
        )

    st.markdown("---")
    st.subheader("Recent Chats")
    
    conversations = get_all_conversations()
    if not conversations:
        st.caption("No chat history yet.")
    else:
        for conv in conversations:
            col1, col2 = st.columns([4, 1])
            is_active = st.session_state.current_chat == conv["id"]
            prefix = "💬 " if not is_active else "👉 "
            with col1:
                if st.button(f"{prefix}{conv['title']}", key=f"chat_{conv['id']}", use_container_width=True):
                    st.session_state.current_chat = conv["id"]
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{conv['id']}", help="Delete chat"):
                    delete_conversation(conv["id"])
                    if st.session_state.current_chat == conv["id"]:
                        st.session_state.current_chat = None
                    st.rerun()

    st.markdown("---")
    if st.button("Clear All History", type="secondary", use_container_width=True):
        for c in conversations:
            delete_conversation(c["id"])
        st.session_state.current_chat = None
        st.success("History cleared.")
        st.rerun()

# ── Main Chat Area ───────────────────────────────────────────
# Header Info
active_title = "New Chat"
if st.session_state.current_chat:
    convs = get_all_conversations()
    found = next((c for c in convs if c["id"] == st.session_state.current_chat), None)
    if found:
        active_title = found["title"]
    else:
        st.session_state.current_chat = None

st.markdown(f"""
<div class="chat-header">
    <h2>{active_title}</h2>
    <p>Model: <code>{st.session_state.model_name}</code> | Temperature: <code>{st.session_state.temperature}</code></p>
</div>
""", unsafe_allow_html=True)

# Warning if API key is missing
if not st.session_state.api_key:
    st.warning("⚠️ No Gemini API key detected! Please add your key in the sidebar under **API Key Settings** to start chatting.")
    st.info("Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).")

# Fetch and display chat messages
messages = []
if st.session_state.current_chat:
    messages = get_messages(st.session_state.current_chat)

for msg in messages:
    avatar = "👤" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# User prompt input
user_input = st.chat_input("Type your message here...")

if user_input:
    if not st.session_state.api_key:
        st.error("Please enter a valid Gemini API key in the sidebar before sending messages.")
    else:
        # 1. Initialize conversation in database if not created yet
        if not st.session_state.current_chat:
            conv_title = auto_generate_title(user_input, st.session_state.api_key, st.session_state.model_name)
            cid = create_conversation(conv_title)
            st.session_state.current_chat = cid
        else:
            cid = st.session_state.current_chat

        # 2. Save and display user message
        save_message(cid, "user", user_input)
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        # 3. Stream assistant response
        with st.chat_message("assistant", avatar="🤖"):
            response_placeholder = st.empty()
            full_response = ""
            
            # Fetch full conversation history
            history_messages = get_messages(cid)
            
            try:
                with st.spinner("Thinking..."):
                    stream = call_gemini_stream(
                        messages=history_messages,
                        api_key=st.session_state.api_key,
                        model_name=st.session_state.model_name,
                        temperature=st.session_state.temperature
                    )
                
                for chunk in stream:
                    if chunk.text:
                        full_response += chunk.text
                        response_placeholder.markdown(full_response + "▌")
                
                response_placeholder.markdown(full_response)
                # 4. Save assistant response to DB
                save_message(cid, "assistant", full_response)
                
            except Exception as e:
                err_text = str(e)
                if "API_KEY_INVALID" in err_text or "API key not valid" in err_text:
                    st.error("❌ Invalid API Key. Please verify your Gemini API key in the sidebar.")
                elif "RESOURCE_EXHAUSTED" in err_text or "429" in err_text:
                    st.error("⏳ API Rate limit exceeded. Please wait a moment and try again.")
                elif "404" in err_text:
                    st.error(f"❌ Model `{st.session_state.model_name}` not available. Try selecting another model in the sidebar.")
                else:
                    st.error(f"❌ Error generating response: {err_text}")
