import streamlit as st
import requests

# App Configuration
st.set_page_config(
    page_title="Persistent ChatBot",
    page_icon="💬",
    layout="wide"
)

# Constants
BASE_URL = "http://127.0.0.1:8001"
CHAT_URL = f"{BASE_URL}/chat"

# --- Session State Initialization ---
if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Functions ---

def check_backend_connection():
    try:
        response = requests.get(BASE_URL, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def get_user_threads(user_id):
    try:
        response = requests.get(f"{BASE_URL}/chat/history/{user_id}")
        if response.status_code == 200:
            return response.json().get("threads", [])
    except Exception:
        pass
    return []

def login():
    st.session_state.user_id = st.session_state.login_input
    st.session_state.thread_id = None
    st.session_state.messages = []

def logout():
    st.session_state.user_id = None
    st.session_state.thread_id = None
    st.session_state.messages = []

def select_thread(thread_id):
    st.session_state.thread_id = thread_id
    try:
        response = requests.get(f"{BASE_URL}/chat/thread/{thread_id}")
        if response.status_code == 200:
            st.session_state.messages = response.json().get("messages", [])
        else:
            st.session_state.messages = []
    except Exception:
        st.session_state.messages = []

def create_new_chat():
    st.session_state.thread_id = None
    st.session_state.messages = []

def send_message():
    user_input = st.session_state.chat_input_key
    if not user_input:
        return

    # Add user message to local history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Prepare payload
    payload = {
        "user_id": st.session_state.user_id,
        "msg": user_input,
        "thread_id": st.session_state.thread_id
    }

    try:
        # The backend returns a standard JSON response
        response = requests.post(CHAT_URL, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            # 1. Update Thread ID (if it was a new chat)
            new_thread_id = data.get("thread_id")
            if new_thread_id:
                st.session_state.thread_id = new_thread_id
            
            # 2. Get the message content
            response_message = data.get("msg", "")
            
            # 3. Save to history
            st.session_state.messages.append({"role": "assistant", "content": response_message})
        
        else:
            st.error(f"Server Error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend server.")
    except Exception as e:
        st.error(f"An error occurred: {e}")

# --- UI Logic ---

if not st.session_state.user_id:
    # --- Login Screen ---
    st.title("Welcome to ChatBot")
    st.markdown("Please enter your User ID to continue.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.text_input("User ID", key="login_input", placeholder="e.g. sadik_01")
    with col2:
        # Align button
        st.write("") 
        st.write("")
        st.button("Login", on_click=login, type="primary")

else:
    # --- Main App ---
    
    # Sidebar: History
    with st.sidebar:
        st.header(f"User: {st.session_state.user_id}")
        if st.button("Logout"):
            logout()
            st.rerun()
            
        st.divider()
        
        if st.button("+ New Chat", type="primary", use_container_width=True):
            create_new_chat()
            
        st.subheader("History")
        threads = get_user_threads(st.session_state.user_id)
        
        if not threads:
            st.info("No history yet.")
        else:
            for thread in threads:
                tid = thread['thread_id']
                label = tid[:8] + "..." # Truncate for display
                if st.button(label, key=tid, use_container_width=True):
                    select_thread(tid)

    # Chat Area
    st.header("Chat Session")
    if st.session_state.thread_id:
        st.caption(f"Thread ID: {st.session_state.thread_id}")
    else:
        st.caption("New Conversation")

    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    st.chat_input("Type your message...", key="chat_input_key", on_submit=send_message)
