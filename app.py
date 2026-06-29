import os
import tempfile

import streamlit as st

from shopping_agent import agent
import config
from setup_db import create_database

# Auto-create database only for SQLite (not Supabase)
if not config.DATABASE_URL and not os.path.exists(config.DB_PATH):
    create_database()

# ---------------------------------------------------------------------------
# Page config — must be first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Natura — AI Shopping",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — Premium dark theme with amber accents
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

/* ── Root variables ── */
:root {
    --bg-primary: #0d0f14;
    --bg-secondary: #13161e;
    --bg-card: #1a1e2a;
    --bg-card-hover: #1f2436;
    --accent-amber: #f59e0b;
    --accent-amber-light: #fbbf24;
    --accent-amber-glow: rgba(245, 158, 11, 0.15);
    --accent-green: #10b981;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --border: rgba(255,255,255,0.06);
    --border-accent: rgba(245, 158, 11, 0.3);
    --radius: 12px;
    --radius-lg: 20px;
}

/* ── Global reset ── */
.stApp {
    background: var(--bg-primary) !important;
    font-family: 'Inter', sans-serif !important;
}

/* Hide default Streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Main container ── */
.main .block-container {
    padding: 0 2rem 4rem 2rem !important;
    max-width: 900px !important;
    margin: 0 auto !important;
}

/* ── Hero header ── */
.hero-header {
    text-align: center;
    padding: 3rem 0 2rem 0;
    position: relative;
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--accent-amber-glow);
    border: 1px solid var(--border-accent);
    border-radius: 50px;
    padding: 6px 16px;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--accent-amber);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 1.25rem;
}

.hero-title {
    font-family: 'Playfair Display', serif !important;
    font-size: 3rem !important;
    font-weight: 700 !important;
    line-height: 1.1 !important;
    margin: 0 0 1rem 0 !important;
    background: linear-gradient(135deg, #f1f5f9 0%, #f59e0b 60%, #fbbf24 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-sub {
    font-size: 1.05rem;
    color: var(--text-secondary);
    font-weight: 400;
    margin: 0 0 2rem 0;
    line-height: 1.6;
}

/* ── Category pills ── */
.pills-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    margin-bottom: 2.5rem;
}

.pill {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 50px;
    padding: 6px 14px;
    font-size: 0.8rem;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
}

.pill:hover {
    border-color: var(--border-accent);
    color: var(--accent-amber);
    background: var(--accent-amber-glow);
}

/* ── Divider ── */
.divider {
    height: 1px;
    background: var(--border);
    margin: 0.5rem 0 1.5rem 0;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 0.25rem 0 !important;
}

/* User messages */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) .stMarkdown {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1rem 1.25rem !important;
    color: var(--text-primary) !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
}

/* Assistant messages */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) .stMarkdown {
    background: linear-gradient(135deg, var(--bg-card) 0%, rgba(245,158,11,0.05) 100%) !important;
    border: 1px solid var(--border-accent) !important;
    border-radius: var(--radius) !important;
    padding: 1rem 1.25rem !important;
    color: var(--text-primary) !important;
    font-size: 0.95rem !important;
    line-height: 1.7 !important;
}

/* Avatar styling */
[data-testid="stChatMessageAvatarUser"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
}

[data-testid="stChatMessageAvatarAssistant"] {
    background: var(--accent-amber-glow) !important;
    border: 1px solid var(--border-accent) !important;
}

/* ── Chat input ── */
[data-testid="stChatInput"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 0 !important;
    margin-top: 1rem !important;
    transition: border-color 0.2s !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: var(--border-accent) !important;
    box-shadow: 0 0 0 3px var(--accent-amber-glow) !important;
}

[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] textarea:focus,
.stChatInput textarea {
    background: transparent !important;
    color: #f1f5f9 !important;
    caret-color: #f59e0b !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 1rem 1.25rem !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: var(--text-muted) !important;
}

[data-testid="stChatInputSubmitButton"] button {
    background: var(--accent-amber) !important;
    border-radius: 50% !important;
    border: none !important;
    color: #0d0f14 !important;
    margin-right: 8px !important;
    transition: all 0.2s !important;
}

[data-testid="stChatInputSubmitButton"] button:hover {
    background: var(--accent-amber-light) !important;
    transform: scale(1.05) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] .block-container {
    padding: 2rem 1.5rem !important;
}

/* Sidebar header */
.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--border);
}

.sidebar-logo-icon {
    width: 36px;
    height: 36px;
    background: var(--accent-amber-glow);
    border: 1px solid var(--border-accent);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
}

.sidebar-logo-text {
    font-family: 'Playfair Display', serif;
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text-primary);
}

.sidebar-section-title {
    font-size: 0.7rem;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 1rem;
}

.sidebar-tip {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem;
    margin-top: 1.5rem;
}

.sidebar-tip-title {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--accent-amber);
    margin-bottom: 0.5rem;
}

.sidebar-tip-text {
    font-size: 0.78rem;
    color: var(--text-secondary);
    line-height: 1.5;
}

/* Sidebar file uploader */
[data-testid="stFileUploader"] {
    background: var(--bg-card) !important;
    border: 1px dashed var(--border-accent) !important;
    border-radius: var(--radius) !important;
    padding: 1rem !important;
}

[data-testid="stFileUploader"] label {
    color: var(--text-secondary) !important;
    font-size: 0.85rem !important;
}

/* Hide the duplicate internal uploader label text */
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] span:first-child,
[data-testid="stFileUploaderDropzoneInstructions"] div:first-child span {
    display: none !important;
}

/* Show only one "Browse files" button label */
[data-testid="stFileUploaderDropzoneInstructions"] {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
}

/* Hide the duplicate "upload" text that appears twice in the button */
[data-testid="stFileUploaderDropzone"] button span + span {
    display: none !important;
}

[data-testid="stBaseButton-secondary"] span:not(:first-child) {
    display: none !important;
}

/* Sidebar button */
[data-testid="stSidebar"] .stButton button {
    background: var(--accent-amber) !important;
    color: #0d0f14 !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    border: none !important;
    border-radius: var(--radius) !important;
    padding: 0.6rem 1rem !important;
    width: 100% !important;
    transition: all 0.2s !important;
    font-family: 'Inter', sans-serif !important;
}

[data-testid="stSidebar"] .stButton button:hover {
    background: var(--accent-amber-light) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(245,158,11,0.3) !important;
}

/* Sidebar text */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {
    color: var(--text-secondary) !important;
    font-family: 'Inter', sans-serif !important;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] {
    color: var(--accent-amber) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* ── Stats bar ── */
.stats-bar {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin-bottom: 2rem;
    flex-wrap: wrap;
}

.stat-item {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.75rem 1.25rem;
    text-align: center;
    min-width: 100px;
}

.stat-number {
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--accent-amber);
    display: block;
    line-height: 1;
    margin-bottom: 4px;
}

.stat-label {
    font-size: 0.72rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 3rem 0;
}

.empty-state-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    display: block;
}

.empty-state-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}

.empty-state-text {
    font-size: 0.9rem;
    color: var(--text-muted);
    line-height: 1.6;
    max-width: 400px;
    margin: 0 auto 1.5rem auto;
}

.prompt-chip {
    display: inline-block;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 50px;
    padding: 8px 16px;
    font-size: 0.82rem;
    color: var(--text-secondary);
    margin: 4px;
    cursor: pointer;
    transition: all 0.2s;
}

.prompt-chip:hover {
    border-color: var(--border-accent);
    color: var(--accent-amber);
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Chat state
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []


def run_agent(spinner_text: str) -> str:
    with st.spinner(spinner_text):
        result = agent.invoke({"messages": st.session_state.messages})
    return result["messages"][-1].content.replace("`", "")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="sidebar-logo-icon">🌿</div>
        <span class="sidebar-logo-text">Natura</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-title">Shop by Image</div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.82rem; color:#64748b; margin-bottom:1rem;">Upload a product photo and I\'ll find similar items.</p>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload a product image",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        st.image(uploaded_file, use_container_width=True)
        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    if uploaded_file and st.button("🔍  Find similar products", use_container_width=True):
        suffix = os.path.splitext(uploaded_file.name)[1] or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            image_path = tmp.name
        prompt = (
            "I uploaded a product image. Please analyze it and find similar products "
            f"in the store. Image path: {image_path}"
        )
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.pending_image = uploaded_file.name
        st.session_state.temp_image_path = image_path
        st.rerun()

    st.markdown("""
    <div class="sidebar-tip">
        <div class="sidebar-tip-title">💡 Try asking</div>
        <div class="sidebar-tip-text">
            "Organic honey under $15 with 4.5+ stars"<br><br>
            "Best rated olive oil"<br><br>
            "Dairy-free milk options"
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-title">About</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.78rem; color:#64748b; line-height:1.6;">
        Powered by <span style="color:#f59e0b;">GPT-4o</span> · 
        Built with LangChain<br>
        32 products · 102 reviews
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main — Hero header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero-header">
    <div class="hero-badge">✦ AI-Powered Shopping</div>
    <h1 class="hero-title">Your personal<br>shopping assistant</h1>
    <p class="hero-sub">Search by taste, price, or photo. I'll find the best match<br>and handle the order — just say the word.</p>
</div>
""", unsafe_allow_html=True)

# Stats bar
st.markdown("""
<div class="stats-bar">
    <div class="stat-item">
        <span class="stat-number">32</span>
        <span class="stat-label">Products</span>
    </div>
    <div class="stat-item">
        <span class="stat-number">8</span>
        <span class="stat-label">Categories</span>
    </div>
    <div class="stat-item">
        <span class="stat-number">102</span>
        <span class="stat-label">Reviews</span>
    </div>
    <div class="stat-item">
        <span class="stat-number">GPT-4o</span>
        <span class="stat-label">Powered by</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Category pills
st.markdown("""
<div class="pills-row">
    <span class="pill">🍯 Honey</span>
    <span class="pill">🫒 Oils</span>
    <span class="pill">🥜 Nuts & Seeds</span>
    <span class="pill">🌾 Grains</span>
    <span class="pill">🍵 Tea & Coffee</span>
    <span class="pill">🥨 Snacks</span>
    <span class="pill">🥛 Dairy Alternatives</span>
    <span class="pill">🌱 Organic</span>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Chat history
# ---------------------------------------------------------------------------
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-state">
        <span class="empty-state-icon">🛍️</span>
        <div class="empty-state-title">What are you looking for today?</div>
        <div class="empty-state-text">
            Ask me anything — I can search by ingredient, dietary preference,
            price range, or star rating. Or upload a photo to find similar products.
        </div>
        <div>
            <span class="prompt-chip">🍯 Best organic honey</span>
            <span class="prompt-chip">🫒 Olive oil under $20</span>
            <span class="prompt-chip">⭐ Top rated nuts</span>
            <span class="prompt-chip">🌱 All organic snacks</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "user" and msg["content"].startswith("I uploaded a product image"):
                filename = msg["content"].split("Image path:")[-1].strip()
                st.markdown(f"📷 Searching by image: **{os.path.basename(filename)}**")
            else:
                st.markdown(msg["content"].replace("$", r"\$"))

# ---------------------------------------------------------------------------
# Image upload processing
# ---------------------------------------------------------------------------
if (
    st.session_state.messages
    and st.session_state.messages[-1]["role"] == "user"
    and "pending_image" in st.session_state
):
    with st.chat_message("assistant"):
        response = run_agent("Analyzing image…")
        st.markdown(response.replace("$", r"\$"))

    st.session_state.messages.append({"role": "assistant", "content": response})
    temp_path = st.session_state.pop("temp_image_path", None)
    if temp_path and os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except OSError:
            pass
    del st.session_state.pending_image
    st.rerun()

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
if prompt := st.chat_input("Ask me anything — try 'organic honey under $15 with 4.5+ rating'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        response = run_agent("Thinking…")
        st.markdown(response.replace("$", r"\$"))
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
