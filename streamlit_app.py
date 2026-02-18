import streamlit as st
from orchestrator import run_orchestrator

#page config
st.set_page_config(
    page_title="Delta Dental AI Assistant (Unofficial)",
    page_icon="🦷",
    layout="wide")

# dark theme
st.markdown("""
<style>
    :root {
        color-scheme: dark;
    }
</style>
""", unsafe_allow_html=True)

# Custom Css
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    [data-testid="stSidebar"] {
        background-color: #1a365d;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    [data-testid="stSidebar"] .stSelectbox label {
        color: white !important;
    }
    .chat-user {
        background-color: #1e2a3a;
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0;
        border-left: 4px solid #1a365d;
    }
    .chat-assistant {
        background-color: #1a1f2e;
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0;
        border-left: 4px solid #4caf50;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    .header-container {
        text-align: center;
        padding: 10px 0 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 🦷 Delta Dental (Unofficial)")
    st.markdown("**AI Insurance Assistant**")
    st.markdown("---")

    plan_options = {
        "Base Plan": "baseplan.pdf",
        "Premium Plan": "premiumplan.pdf",
        "State Plan": "stateplan.pdf",
        "Compare Plans": "plancompare.pdf",
        "FAQ": "BasicFAQ.txt",
    }

    selected_plan = st.selectbox("Select a plan:", list(plan_options.keys()) + ["All Plans"])
    plan_filter = plan_options[selected_plan, None]


    st.markdown("---")
    st.markdown("### What I can help with:")
    st.markdown("🔍 **Coverage** — plan benefits & percentages")
    st.markdown("👨‍⚕️ **Providers** — find dentists near you")
    st.markdown("💰 **Costs** — estimate out-of-pocket expenses")
    st.markdown("---")
    st.markdown("*Powered by Azure AI Foundry*")

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Main area header
st.markdown('<div class="header-container">', unsafe_allow_html=True)
st.markdown("# 🦷 Delta Dental AI Assistant (Unofficial)")
st.markdown(f"*Currently viewing: **{selected_plan}***")
st.markdown('</div>', unsafe_allow_html=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div class="chat-user">🧑 {message["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-assistant">🤖 {message["content"]}</div>', unsafe_allow_html=True)

# Welcome message if no chat history
if not st.session_state.messages:
    st.markdown("""
    <div class="chat-assistant">
    🤖 Welcome! I'm your Delta Dental AI Assistant. I can help you with:
    <br><br>
    • <b>Coverage questions</b> — "What's covered for root canals?"<br>
    • <b>Finding providers</b> — "Find me a dentist in Grand Rapids"<br>
    • <b>Cost estimates</b> — "How much will a crown cost me?"<br>
    • <b>Multi-intent</b> — "Find me a dentist for a cleaning in Cadillac and tell me what my plan covers"
    <br><br>
    Select your plan from the sidebar and ask away!
    </div>
    """, unsafe_allow_html=True)

# Chat input
user_input = st.chat_input("Ask about your dental coverage, find providers, or estimate costs...")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.markdown(f'<div class="chat-user">🧑 {user_input}</div>', unsafe_allow_html=True)

    # Get response
    with st.spinner("Thinking..."):
        response = run_orchestrator(user_input, plan_filter)

    # Add assistant message
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.markdown(f'<div class="chat-assistant">🤖 {response}</div>', unsafe_allow_html=True)
    st.rerun()


