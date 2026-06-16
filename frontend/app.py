# frontend/app.py
import streamlit as st
import requests
import uuid
import json

st.set_page_config(
    page_title="FinanceAI — Document Intelligence",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Page background ── */
.stApp { background: #0b0b14; }
.main .block-container {
    padding: 1.5rem 2rem 2rem 2rem !important;
    max-width: 100% !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #111120 !important;
    border-right: 1px solid rgba(124,58,237,0.2) !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stTextInput input {
    color: rgba(255,255,255,0.75) !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #ffffff !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 999px !important;
    padding: 0.45rem 1.4rem !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* ── Chat input ── */
[data-testid="stChatInput"] {
    background: #1a1a2e !important;
    border: 1.5px solid rgba(124,58,237,0.5) !important;
    border-radius: 999px !important;
}
[data-testid="stChatInput"] textarea {
    color: #ffffff !important;
    background: transparent !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: #16162a !important;
    border: 1px solid rgba(124,58,237,0.15) !important;
    border-radius: 14px !important;
    padding: 0.5rem !important;
    margin-bottom: 0.5rem !important;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: #16162a !important;
    border: 1px solid rgba(124,58,237,0.2) !important;
    border-radius: 14px !important;
    padding: 1rem 1.2rem !important;
}
[data-testid="stMetricValue"] {
    color: #a78bfa !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] { color: rgba(255,255,255,0.45) !important; }
[data-testid="stMetricDelta"] { color: #34d399 !important; }

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: rgba(124,58,237,0.06) !important;
    border: 1.5px dashed rgba(124,58,237,0.4) !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploader"] label { color: rgba(255,255,255,0.6) !important; }

/* ── Status widget ── */
[data-testid="stStatus"] {
    background: #16162a !important;
    border: 1px solid rgba(124,58,237,0.2) !important;
    border-radius: 12px !important;
    color: rgba(255,255,255,0.8) !important;
}

/* ── Alerts ── */
.stSuccess { background: rgba(52,211,153,0.12) !important; border-radius: 10px !important; color: #34d399 !important; }
.stError   { background: rgba(239,68,68,0.12)  !important; border-radius: 10px !important; color: #f87171 !important; }
.stWarning { background: rgba(251,191,36,0.12) !important; border-radius: 10px !important; color: #fbbf24 !important; }
.stInfo    { background: rgba(96,165,250,0.12) !important; border-radius: 10px !important; color: #60a5fa !important; }

/* ── Divider ── */
hr { border-color: rgba(124,58,237,0.2) !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0b0b14; }
::-webkit-scrollbar-thumb { background: #7c3aed; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────
if "session_id"       not in st.session_state: st.session_state.session_id       = str(uuid.uuid4())
if "pending_approval" not in st.session_state: st.session_state.pending_approval = False
if "approval_message" not in st.session_state: st.session_state.approval_message = ""
if "messages"         not in st.session_state: st.session_state.messages         = []

# ── Helper: agent badge HTML ───────────────────────────────
AGENT_META = {
    "stock"      : ("#10b981", "#d1fae5", "📈 Stock Agent"),
    "news"       : ("#3b82f6", "#dbeafe", "📰 News Agent"),
    "calculator" : ("#f59e0b", "#fef3c7", "🧮 Calculator"),
    "rag"        : ("#a78bfa", "#ede9fe", "📄 RAG Agent"),
    "approved"   : ("#10b981", "#d1fae5", "✅ Approved"),
    "rejected"   : ("#ef4444", "#fee2e2", "❌ Rejected"),
    "general"    : ("#6b7280", "#f3f4f6", "⚡ General"),
}

def agent_badge(agent: str) -> str:
    color, bg, label = AGENT_META.get(agent, ("#6b7280","#f3f4f6","⚡ General"))
    return (
        f"<span style='display:inline-block;background:{bg};color:{color};"
        f"padding:3px 12px;border-radius:999px;font-size:11px;font-weight:600;"
        f"margin-top:6px;'>{label}</span>"
    )

# ── SIDEBAR ───────────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown("""
    <div style='padding:20px 0 24px;text-align:center;'>
        <div style='font-size:2.4rem;'>💰</div>
        <div style='font-size:1.1rem;font-weight:700;color:#fff;margin-top:6px;
                    letter-spacing:0.02em;'>FinanceAI</div>
        <div style='font-size:0.7rem;color:rgba(255,255,255,0.35);
                    margin-top:3px;letter-spacing:0.06em;'>DOCUMENT INTELLIGENCE</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Agents list
    st.markdown("<div style='font-size:10px;color:rgba(255,255,255,0.35);letter-spacing:.1em;margin-bottom:10px;'>AI AGENTS</div>", unsafe_allow_html=True)
    for color, icon, name, desc in [
        ("#10b981","📈","Stock Agent",      "Live prices & fundamentals"),
        ("#3b82f6","📰","News Agent",       "Financial news & updates"),
        ("#f59e0b","🧮","Calculator Agent", "Ratios & computations"),
        ("#a78bfa","📄","RAG Agent",        "Document Q&A"),
    ]:
        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:10px;
                    padding:9px 12px;border-radius:10px;margin-bottom:5px;
                    background:rgba(255,255,255,0.03);
                    border:1px solid rgba(255,255,255,0.06);'>
            <div style='width:7px;height:7px;border-radius:50%;
                        background:{color};flex-shrink:0;
                        box-shadow:0 0 6px {color};'></div>
            <div>
                <div style='font-size:12px;font-weight:600;color:#fff;'>{icon} {name}</div>
                <div style='font-size:10px;color:rgba(255,255,255,0.3);margin-top:1px;'>{desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Documents
    try:
        r = requests.get("http://localhost:8000/documents", timeout=5)
        docs = r.json().get("documents", [])
        if docs:
            st.markdown("<div style='font-size:10px;color:rgba(255,255,255,0.35);letter-spacing:.1em;margin-bottom:10px;'>UPLOADED DOCS</div>", unsafe_allow_html=True)
            for doc in docs:
                st.markdown(f"""
                <div style='display:flex;align-items:center;gap:8px;
                            background:rgba(124,58,237,0.12);
                            border:1px solid rgba(124,58,237,0.25);
                            border-radius:8px;padding:7px 10px;margin-bottom:4px;
                            font-size:11px;color:rgba(255,255,255,0.65);'>
                    📄 {doc[:26]}{'…' if len(doc)>26 else ''}
                </div>
                """, unsafe_allow_html=True)
            st.markdown("---")
    except:
        pass

    # Upload
    st.markdown("<div style='font-size:10px;color:rgba(255,255,255,0.35);letter-spacing:.1em;margin-bottom:10px;'>UPLOAD PDF</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("PDF", type=["pdf"], label_visibility="collapsed")
    if uploaded_file:
        if st.button("📤 Process Document", use_container_width=True):
            with st.spinner("Indexing..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    r = requests.post("http://localhost:8000/upload", files=files, timeout=120)
                    data = r.json()
                    st.success(data["message"])
                except Exception as e:
                    st.error(f"Error: {e}")

    st.markdown("---")

    # HITL
    if st.session_state.pending_approval:
        st.markdown("""
        <div style='background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.4);
                    border-radius:10px;padding:12px 14px;margin-bottom:12px;'>
            <div style='font-size:12px;font-weight:700;color:#fbbf24;margin-bottom:4px;'>
                ⚠️ Approval Required
            </div>
            <div style='font-size:11px;color:rgba(255,255,255,0.45);line-height:1.5;'>
                A high-risk financial action needs your review before proceeding.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.approval_message:
            st.markdown(f"<div style='font-size:11px;color:rgba(255,255,255,0.4);margin-bottom:10px;line-height:1.5;'>{st.session_state.approval_message[:300]}</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Approve", use_container_width=True):
                with st.spinner("Executing..."):
                    try:
                        r = requests.post("http://localhost:8000/approve",
                            json={"session_id": st.session_state.session_id, "decision": "approve"}, timeout=60)
                        data = r.json()
                        st.session_state.messages.append({"role":"assistant","content":data.get("response",""),"agent_used":"approved"})
                        st.session_state.pending_approval = False
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        with c2:
            if st.button("❌ Reject", use_container_width=True):
                try:
                    requests.post("http://localhost:8000/approve",
                        json={"session_id": st.session_state.session_id, "decision": "reject"}, timeout=60)
                    st.session_state.messages.append({"role":"assistant","content":"❌ Action cancelled.","agent_used":"rejected"})
                    st.session_state.pending_approval = False
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        st.markdown("---")

    if st.button("🔄 New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.pending_approval = False
        st.rerun()

    st.markdown(f"<div style='margin-top:20px;font-size:9px;color:rgba(255,255,255,0.15);'>Session · {st.session_state.session_id[:20]}…</div>", unsafe_allow_html=True)


# ── MAIN ─────────────────────────────────────────────────

# Header card
st.markdown("""
<div style='background:#16162a;border:1px solid rgba(124,58,237,0.25);
            border-radius:16px;padding:22px 28px;margin-bottom:20px;'>
    <div style='display:flex;align-items:center;gap:16px;'>
        <div style='background:linear-gradient(135deg,#7c3aed,#4f46e5);
                    border-radius:14px;width:52px;height:52px;
                    display:flex;align-items:center;justify-content:center;
                    font-size:1.6rem;flex-shrink:0;'>💰</div>
        <div>
            <div style='font-size:1.35rem;font-weight:700;color:#ffffff;'>
                Financial Document Intelligence Agent
            </div>
            <div style='font-size:0.78rem;color:rgba(255,255,255,0.4);margin-top:4px;'>
                Groq · LangGraph · RAG · Streaming · Human-in-the-Loop · LangSmith
            </div>
        </div>
    </div>
    <div style='margin-top:16px;display:flex;flex-wrap:wrap;gap:6px;'>
        <span style='background:rgba(167,139,250,0.15);color:#a78bfa;padding:4px 12px;border-radius:999px;font-size:11px;font-weight:600;border:1px solid rgba(167,139,250,0.3);'>🤖 Multi-Agent</span>
        <span style='background:rgba(52,211,153,0.12);color:#34d399;padding:4px 12px;border-radius:999px;font-size:11px;font-weight:600;border:1px solid rgba(52,211,153,0.25);'>📊 Live Stocks</span>
        <span style='background:rgba(96,165,250,0.12);color:#60a5fa;padding:4px 12px;border-radius:999px;font-size:11px;font-weight:600;border:1px solid rgba(96,165,250,0.25);'>🔍 RAG Pipeline</span>
        <span style='background:rgba(251,191,36,0.12);color:#fbbf24;padding:4px 12px;border-radius:999px;font-size:11px;font-weight:600;border:1px solid rgba(251,191,36,0.25);'>⚡ Streaming</span>
        <span style='background:rgba(248,113,113,0.12);color:#f87171;padding:4px 12px;border-radius:999px;font-size:11px;font-weight:600;border:1px solid rgba(248,113,113,0.25);'>🔐 HITL</span>
        <span style='background:rgba(167,139,250,0.12);color:#c4b5fd;padding:4px 12px;border-radius:999px;font-size:11px;font-weight:600;border:1px solid rgba(167,139,250,0.25);'>📈 LangSmith</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Metrics
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("AI Agents", "4", "Active")
with c2: st.metric("Tools", "3", "Connected")
with c3: st.metric("Memory", "Short + Long")
with c4: st.metric("Monitoring", "LangSmith", "Live")

st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

# ── CHAT ─────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant" and msg.get("agent_used","none") in AGENT_META:
            st.markdown(agent_badge(msg["agent_used"]), unsafe_allow_html=True)

user_input = st.chat_input("Ask about stocks, news, documents, calculations…")

if user_input:
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role":"user","content":user_input})

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_text   = ""
        agent_used  = "none"

        try:
            with st.status("🤖 Agents working…", expanded=True) as status:
                st.write("🧠 Supervisor routing query…")

                with requests.post(
                    "http://localhost:8000/ask/stream",
                    json={"message": user_input,
                          "chat_history": st.session_state.messages,
                          "session_id": st.session_state.session_id},
                    stream=True, timeout=120
                ) as resp:
                    for line in resp.iter_lines():
                        if not line: continue
                        line = line.decode("utf-8")
                        if not line.startswith("data: "): continue
                        data = json.loads(line[6:])

                        if data["type"] == "agent":
                            agent_used = data["agent"]
                            labels = {"stock":"📈 Stock Agent fetching…","news":"📰 News Agent searching…",
                                      "calculator":"🧮 Calculator computing…","rag":"📄 RAG searching docs…"}
                            if agent_used in labels:
                                st.write(labels[agent_used])

                        elif data["type"] == "token":
                            full_text += data["content"]
                            placeholder.markdown(f"<div style='color:#e2e8f0;line-height:1.7;'>{full_text}▌</div>", unsafe_allow_html=True)

                        elif data["type"] == "done":
                            placeholder.markdown(f"<div style='color:#e2e8f0;line-height:1.7;'>{full_text}</div>", unsafe_allow_html=True)
                            status.update(label="✅ Done!", state="complete")

                        elif data["type"] == "interrupt":
                            st.session_state.pending_approval = True
                            st.session_state.approval_message = data.get("message","")
                            status.update(label="⚠️ Approval needed", state="running")
                            st.rerun()

                        elif data["type"] == "error":
                            st.error(f"Error: {data['content']}")
                            status.update(label="❌ Failed", state="error")

        except Exception as e:
            st.error(f"❌ {e}")
            full_text  = "Something went wrong!"
            agent_used = "none"

        if agent_used in AGENT_META:
            st.markdown(agent_badge(agent_used), unsafe_allow_html=True)

    st.session_state.messages.append({"role":"assistant","content":full_text,"agent_used":agent_used})