import os
import html
import hashlib
import tempfile

import pandas as pd
import streamlit as st

from ui.styles import apply_custom_css
from utils.pdf_extractor import extract_text_from_pdf
from utils.medical_parser import extract_medical_values
from utils.severity_checker import check_severity
from utils.report_classifier import classify_report_sections
from utils.medical_nlp import simplify_medical_text
from utils.pdf_exporter import generate_medical_summary_pdf

try:
    from docx import Document
except Exception:
    Document = None

try:
    from utils.semantic_classifier import SemanticMedicalClassifier
except Exception:
    SemanticMedicalClassifier = None

try:
    from utils.semantic_retriever import SemanticMedicalRetriever
except Exception:
    SemanticMedicalRetriever = None

try:
    from utils.faiss_retriever import FAISSMedicalRetriever
except Exception:
    FAISSMedicalRetriever = None

try:
    from utils.medical_chatbot import MedicalChatbot
except Exception:
    MedicalChatbot = None


st.set_page_config(
    page_title="MediInsight",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)
apply_custom_css()


PATIENT_SECTIONS = [
    "📋 Simplified Report",
    "⚠️ Important Findings",
    "🧪 Medical Values",
    "💬 Ask Questions",
    "❤️ Health Concerns",
]


HERO_HTML = """
<div class="hero-card">
    <div class="hero-badge">
        <span>◎</span> AI-Powered Medical Report Analysis
    </div>
    <div class="hero-title">🩺 Medi<span>Insight</span></div>
    <div class="hero-subtitle">
        Understand your medical report in plain language — review abnormal values,
        track health concerns, and ask questions about your findings.
    </div>
</div>
"""

st.markdown(HERO_HTML, unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def load_semantic_classifier():
    if SemanticMedicalClassifier is None:
        return None
    try:
        return SemanticMedicalClassifier()
    except Exception:
        return None


@st.cache_resource(show_spinner=False)
def load_semantic_retriever():
    if SemanticMedicalRetriever is None:
        return None
    try:
        return SemanticMedicalRetriever()
    except Exception:
        return None


@st.cache_resource(show_spinner=False)
def load_faiss_retriever():
    if FAISSMedicalRetriever is None:
        return None
    try:
        return FAISSMedicalRetriever()
    except Exception:
        return None


@st.cache_resource(show_spinner=False)
def load_medical_chatbot():
    if MedicalChatbot is None:
        return None
    try:
        return MedicalChatbot()
    except Exception:
        return None


def escape_text(value):
    return html.escape(str(value))


def get_file_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()


def severity_badge(status):
    status_text = str(status).lower()

    if any(word in status_text for word in ["critical", "severe", "very high", "very low"]):
        return "🔴"
    if any(word in status_text for word in ["high", "low", "abnormal"]):
        return "🟠"
    if "borderline" in status_text:
        return "🟡"
    return "🟢"


def calculate_health_concerns(report_sections, severity_results):
    concern_sources = []
    concern_sources.extend(report_sections.get("possible_conditions", []))
    concern_sources.extend(report_sections.get("clinical_findings", []))

    abnormal_count = 0
    for status in severity_results.values():
        status_text = str(status).lower()
        if any(word in status_text for word in ["high", "low", "critical", "severe", "very high", "very low"]):
            abnormal_count += 1

    return min(len(concern_sources) + abnormal_count, 9)


def get_abnormal_count(severity_results):
    return len(severity_results or {})


def extract_text_from_uploaded_file(uploaded_file):
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        temp_file.write(uploaded_file.getvalue())
        temp_path = temp_file.name

    if file_extension == ".pdf":
        return extract_text_from_pdf(temp_path)

    if file_extension == ".txt":
        with open(temp_path, "r", encoding="utf-8", errors="ignore") as file:
            return file.read().strip()

    if file_extension == ".docx":
        if Document is None:
            return "DOCX Error: python-docx is not installed. Run: pip install python-docx"
        doc = Document(temp_path)
        return "\n".join(
            paragraph.text.strip()
            for paragraph in doc.paragraphs
            if paragraph.text.strip()
        )

    return "Unsupported file format. Please upload PDF, TXT, or DOCX."


def process_uploaded_report(uploaded_file, use_semantic_nlp=True, retrieval_engine="FAISS Vector Retrieval"):
    report_text = extract_text_from_uploaded_file(uploaded_file)

    if report_text.startswith("PDF Error"):
        return {"success": False, "error": report_text}
    if report_text.startswith("DOCX Error"):
        return {"success": False, "error": report_text}
    if report_text.startswith("Unsupported file format"):
        return {"success": False, "error": report_text}
    if not report_text.strip():
        return {
            "success": False,
            "error": "No readable text was found in this file. Please upload a text-based PDF, TXT, or DOCX report.",
        }

    extracted_values = extract_medical_values(report_text)
    severity_results = check_severity(extracted_values)
    report_sections = classify_report_sections(report_text)

    semantic_sections = None
    retrieved_context = []

    if use_semantic_nlp:
        semantic_classifier = load_semantic_classifier()
        if semantic_classifier:
            semantic_sections = semantic_classifier.classify_report(report_text)

    if retrieval_engine == "FAISS Vector Retrieval":
        faiss_retriever = load_faiss_retriever()
        if faiss_retriever:
            retrieved_context = faiss_retriever.retrieve(
                extracted_values, severity_results, report_sections, top_k=5, min_score=0.20,
            )
    else:
        semantic_retriever = load_semantic_retriever()
        if semantic_retriever:
            retrieved_context = semantic_retriever.retrieve(
                extracted_values, severity_results, report_sections, top_k=5, min_score=0.20,
            )

    summary = simplify_medical_text(
        extracted_values, severity_results, report_sections, use_mistral=False,
    )

    return {
        "success": True,
        "report_text": report_text,
        "extracted_values": extracted_values,
        "severity_results": severity_results,
        "report_sections": report_sections,
        "semantic_sections": semantic_sections,
        "retrieved_context": retrieved_context,
        "summary": summary,
    }


# ─── CARD COMPONENTS ──────────────────────────────────────────────────────────

def metric_card(label, value):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">{escape_text(value)}</div>
            <div class="metric-label">{escape_text(label)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_card(title, text):
    safe_text = escape_text(text).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="dashboard-card">
            <div class="card-title">{escape_text(title)}</div>
            <div class="card-text">{safe_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(icon, title, subtitle=""):
    sub_html = f'<p style="color:var(--text-muted);font-size:13px;margin:4px 0 0 0;font-weight:400;">{escape_text(subtitle)}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div style="margin-bottom:20px;">
            <h2 style="font-family:\'Space Grotesk\',sans-serif;font-size:22px;font-weight:700;
                       color:var(--text-primary);margin:0;letter-spacing:-0.4px;">
                {escape_text(icon)}&nbsp; {escape_text(title)}
            </h2>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def is_noise_item(item):
    if item is None:
        return True
    text = str(item).strip()
    if not text or len(text) < 3:
        return True
    noise_chars = set("_-—–=━─•●* .")
    if all(char in noise_chars for char in text):
        return True
    cleaned = text.replace("_", "").replace("-", "").replace("—", "").replace("–", "")
    cleaned = cleaned.replace("=", "").replace("━", "").replace("─", "").strip()
    return not cleaned


def clean_bullet_items(items):
    cleaned_items = []
    seen = set()
    for item in items or []:
        text = str(item).strip()
        text = " ".join(text.split())
        if is_noise_item(text):
            continue
        normalized = text.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        cleaned_items.append(text)
    return cleaned_items


def bullet_card(title, items, empty_text="No major items detected in this section.", accent_color="var(--teal)"):
    cleaned_items = clean_bullet_items(items)

    if not cleaned_items:
        info_card(title, empty_text)
        return

    list_items = "".join(
        f"""<li style="color:var(--text-secondary);margin-bottom:7px;font-size:14px;line-height:1.6;">
                <span style="color:{accent_color};margin-right:6px;">›</span>{escape_text(item)}
            </li>"""
        for item in cleaned_items
    )

    st.markdown(
        f"""
        <div class="dashboard-card">
            <div class="card-title">{escape_text(title)}</div>
            <div class="card-text">
                <ul style="list-style:none;padding:0;margin:0;">{list_items}</ul>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── EMPTY STATE ──────────────────────────────────────────────────────────────

def display_empty_state():
    left, right = st.columns([1.35, 0.65])

    with left:
        st.markdown(
            """
            <div class="dashboard-card" style="border-left: 3px solid var(--teal);">
                <div class="card-title">Upload a report to get started</div>
                <div class="card-text">
                    MediInsight supports <strong style="color:var(--teal);">PDF, TXT, and DOCX</strong> formats.
                    Once uploaded, the AI will identify medical values, flag abnormal results, and explain
                    everything in clear, patient-friendly language — no medical background needed.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        features = [
            ("📋", "Simplified Report", "Plain-language explanation"),
            ("⚠️", "Important Findings", "Abnormal values flagged"),
            ("🧪", "Medical Values", "Extracted test results"),
            ("💬", "Ask Questions", "Chat with your report"),
            ("❤️", "Health Concerns", "Symptoms & recommendations"),
        ]
        items_html = "".join(
            f"""<div style="display:flex;align-items:center;gap:10px;padding:9px 0;
                            border-bottom:1px solid var(--glass-border);">
                    <span style="font-size:16px;">{esc}</span>
                    <div>
                        <div style="font-size:13.5px;font-weight:600;color:var(--text-primary);">{escape_text(name)}</div>
                        <div style="font-size:12px;color:var(--text-muted);">{escape_text(desc)}</div>
                    </div>
                </div>"""
            for esc, name, desc in features
        )
        st.markdown(
            f"""
            <div class="dashboard-card">
                <div class="card-title">What you'll see</div>
                <div>{items_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─── SECTION RENDERERS ────────────────────────────────────────────────────────

def display_simplified_report(
    summary, extracted_values, severity_results, report_sections, retrieved_context, health_concerns_count,
):
    section_header("📋", "Simplified Report", "AI-generated plain-language explanation of your report")

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        metric_card("Values Found", len(extracted_values))
    with metric_col2:
        metric_card("Abnormal Findings", get_abnormal_count(severity_results))
    with metric_col3:
        metric_card("Health Concerns", health_concerns_count)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="dashboard-card" style="border-left: 3px solid var(--teal);">
            <div class="card-title" style="color:var(--teal);">🧠 AI Explanation</div>
            <div class="card-text" style="font-size:15px;line-height:1.9;color:var(--text-secondary);">
                {escape_text(summary).replace(chr(10), '<br>')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """<p style="font-family:'Space Grotesk',sans-serif;font-size:12px;font-weight:600;
                     letter-spacing:1px;text-transform:uppercase;color:var(--text-muted);
                     margin:20px 0 10px 0;">Export</p>""",
        unsafe_allow_html=True,
    )

    medical_summary_pdf = generate_medical_summary_pdf(
        summary=summary,
        extracted_values=extracted_values,
        severity_results=severity_results,
        report_sections=report_sections,
        retrieved_context=retrieved_context,
    )

    st.download_button(
        label="📄 Download Medical Summary PDF",
        data=medical_summary_pdf,
        file_name="medexplain_medical_summary.pdf",
        mime="application/pdf",
        use_container_width=True,
    )


def display_important_findings(severity_results, report_sections):
    section_header("⚠️", "Important Findings", "Abnormal values and clinically significant results")

    if severity_results:
        rows_html = "".join(
            f"""<tr>
                <td style="text-align:center;font-size:16px;padding:10px 14px;">{severity_badge(interp)}</td>
                <td style="padding:10px 14px;font-weight:500;color:#D1E8FF;">{escape_text(param)}</td>
                <td style="padding:10px 14px;color:#94A3B8;">{escape_text(interp)}</td>
            </tr>"""
            for param, interp in severity_results.items()
        )
        st.markdown(
            f"""
            <div style="border-radius:14px;overflow:hidden;border:1px solid rgba(56,189,248,0.18);margin-bottom:8px;">
                <table style="width:100%;border-collapse:collapse;font-family:'DM Sans',sans-serif;font-size:13.5px;">
                    <thead>
                        <tr style="background:#0A1526;border-bottom:1px solid rgba(45,212,191,0.25);">
                            <th style="padding:11px 14px;text-align:center;font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:700;letter-spacing:0.8px;text-transform:uppercase;color:#2DD4BF;width:60px;">Status</th>
                            <th style="padding:11px 14px;text-align:left;font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:700;letter-spacing:0.8px;text-transform:uppercase;color:#2DD4BF;">Medical Value</th>
                            <th style="padding:11px 14px;text-align:left;font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:700;letter-spacing:0.8px;text-transform:uppercase;color:#2DD4BF;">Interpretation</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
            <style>
                table tr {{ background: #0F1C2E; }}
                table tr:nth-child(even) {{ background: #111E30; }}
                table tr:hover td {{ background: rgba(45,212,191,0.06) !important; color: #F0F6FF !important; }}
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="dashboard-card" style="border-left:3px solid var(--emerald);text-align:center;padding:30px;">
                <div style="font-size:28px;margin-bottom:8px;">✅</div>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:600;
                            color:var(--emerald);">No Abnormal Values Detected</div>
                <div style="font-size:13px;color:var(--text-muted);margin-top:6px;">
                    All extracted values appear within reference ranges.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        bullet_card(
            "🩺 Clinical Findings",
            report_sections.get("clinical_findings", []),
            accent_color="var(--sky)",
        )
    with col2:
        bullet_card(
            "📌 Possible Conditions",
            report_sections.get("possible_conditions", []),
            accent_color="var(--violet)",
        )


def display_medical_values(extracted_values):
    section_header("🧪", "Medical Values", "All extracted test results from the report")

    filtered_values = {
        key: value
        for key, value in extracted_values.items()
        if value not in ["Not Found", None, ""]
    }

    if not filtered_values:
        st.markdown(
            """
            <div class="dashboard-card" style="text-align:center;padding:30px;">
                <div style="font-size:28px;margin-bottom:8px;">🔍</div>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:600;
                            color:var(--text-muted);">No medical values detected</div>
                <div style="font-size:13px;color:var(--text-muted);margin-top:6px;">
                    The system could not extract quantitative values from this report.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    rows_html = "".join(
        f"""<tr>
            <td style="padding:10px 14px;font-weight:500;color:#D1E8FF;">{escape_text(key)}</td>
            <td style="padding:10px 14px;color:#2DD4BF;font-family:'DM Mono',monospace;font-size:13px;">{escape_text(str(value))}</td>
        </tr>"""
        for key, value in filtered_values.items()
    )
    st.markdown(
        f"""
        <div style="border-radius:14px;overflow:hidden;border:1px solid rgba(56,189,248,0.18);margin-bottom:8px;">
            <table style="width:100%;border-collapse:collapse;font-family:'DM Sans',sans-serif;font-size:13.5px;">
                <thead>
                    <tr style="background:#0A1526;border-bottom:1px solid rgba(45,212,191,0.25);">
                        <th style="padding:11px 14px;text-align:left;font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:700;letter-spacing:0.8px;text-transform:uppercase;color:#2DD4BF;">Medical Value</th>
                        <th style="padding:11px 14px;text-align:left;font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:700;letter-spacing:0.8px;text-transform:uppercase;color:#2DD4BF;">Result</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        <style>
            table tr {{ background: #0F1C2E; }}
            table tr:nth-child(even) {{ background: #111E30; }}
            table tr:hover td {{ background: rgba(45,212,191,0.06) !important; color: #F0F6FF !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def display_health_concerns(report_sections, severity_results):
    section_header("❤️", "Health Concerns", "Symptoms mentioned and recommendations from the report")

    symptoms = report_sections.get("symptoms", [])
    recommendations = report_sections.get("recommendations", [])

    col1, col2 = st.columns(2)
    with col1:
        bullet_card(
            "🤒 Symptoms Mentioned", symptoms,
            accent_color="var(--rose)",
        )
    with col2:
        bullet_card(
            "✅ Recommendations", recommendations,
            accent_color="var(--emerald)",
        )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if severity_results:
        st.markdown(
            """
            <div class="dashboard-card" style="border-left:3px solid var(--amber);">
                <div class="card-title" style="color:var(--amber);">⚕️ Discuss with a Doctor</div>
                <div class="card-text">
                    This report contains abnormal values or clinically significant findings.
                    Use this explanation as a guide to understand the report — not as a diagnosis.
                    A qualified doctor should confirm what these results mean for you personally.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="dashboard-card" style="border-left:3px solid var(--sky);">
                <div class="card-title" style="color:var(--sky);">ℹ️ General Note</div>
                <div class="card-text">
                    No major abnormal values were detected by the system. However, a doctor should
                    still review the complete report if symptoms are present or if this was ordered
                    for an ongoing medical concern.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─── CHATBOT ──────────────────────────────────────────────────────────────────

def build_contextual_followup_question(question, chat_history):
    question = question.strip()
    if not chat_history:
        return question

    previous_question = chat_history[-1].get("question", "")
    previous_answer = chat_history[-1].get("answer", "")

    return (
        f"Previous question: {previous_question}\n"
        f"Previous answer summary: {previous_answer[:500]}\n"
        f"Follow-up question: {question}"
    )


def display_chat_message(role, text):
    if role == "user":
        css_class = "user-card"
        label = "You"
    else:
        css_class = "assistant-card"
        label = "MedExplain Assistant"

    safe_text = escape_text(text).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="{css_class}">
            <b>{escape_text(label)}</b><br><br>
            {safe_text}
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_medical_chatbot(
    chatbot, extracted_values, severity_results, report_sections, semantic_sections, retrieved_context,
):
    section_header("💬", "Ask MedExplain", "Questions answered based on your uploaded report findings")

    if chatbot is None:
        st.error("Ask MedExplain could not be loaded.")
        return

    chatbot_sections = semantic_sections if semantic_sections else report_sections

    if "phase4_chat_history" not in st.session_state:
        st.session_state.phase4_chat_history = []
    if "phase4_latest_question" not in st.session_state:
        st.session_state.phase4_latest_question = ""
    if "phase4_latest_answer" not in st.session_state:
        st.session_state.phase4_latest_answer = ""

    sample_questions = [
        "What are the main problems in this report?",
        "Which findings look serious?",
        "Explain the kidney-related findings.",
        "What should I ask my doctor about this report?",
        "Can you explain this report in very simple words?",
    ]

    with st.form(key="phase4_question_form", clear_on_submit=True):
        selected_question = st.selectbox("Try a sample question", [""] + sample_questions)
        user_question = st.text_input("Or ask your own question about the report", placeholder="e.g. What does my blood sugar result mean?")
        ask_clicked = st.form_submit_button("Ask MedExplain →")

    clear_clicked = st.button("Clear Chat History", key="phase4_clear_button")
    if clear_clicked:
        st.session_state.phase4_chat_history = []
        st.session_state.phase4_latest_question = ""
        st.session_state.phase4_latest_answer = ""
        st.success("Chat history cleared.")

    if ask_clicked:
        final_question = user_question.strip() or selected_question.strip()

        if not final_question:
            st.warning("Please enter or select a question.")
            return

        contextual_question = build_contextual_followup_question(
            final_question, st.session_state.phase4_chat_history,
        )

        with st.spinner("Preparing your answer..."):
            answer = chatbot.answer_question(
                question=contextual_question,
                values=extracted_values,
                severity_results=severity_results,
                report_sections=chatbot_sections,
                retrieved_chunks=retrieved_context,
            )

        st.session_state.phase4_latest_question = final_question
        st.session_state.phase4_latest_answer = answer
        st.session_state.phase4_chat_history.append({"question": final_question, "answer": answer})

    if st.session_state.phase4_latest_answer:
        st.markdown(
            """<p style="font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:600;
                         letter-spacing:1px;text-transform:uppercase;color:var(--text-muted);
                         margin:18px 0 10px 0;">Latest Answer</p>""",
            unsafe_allow_html=True,
        )
        display_chat_message("user", st.session_state.phase4_latest_question)
        display_chat_message("assistant", st.session_state.phase4_latest_answer)
    else:
        st.markdown(
            """
            <div style="text-align:center;padding:30px 20px;color:var(--text-muted);font-size:14px;">
                <div style="font-size:28px;margin-bottom:10px;">💬</div>
                Select a sample question or type your own to get started.
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.session_state.phase4_chat_history:
        if "show_chat_history" not in st.session_state:
            st.session_state.show_chat_history = False

        toggle_label = "▲ Hide previous questions" if st.session_state.show_chat_history else "▼ Show previous questions"
        if st.button(toggle_label, key="phase4_history_toggle"):
            st.session_state.show_chat_history = not st.session_state.show_chat_history

        if st.session_state.show_chat_history:
            st.markdown(
                """<div style="border:1px solid rgba(56,189,248,0.16);border-radius:14px;
                               padding:16px;margin-top:8px;background:#0D1828;">""",
                unsafe_allow_html=True,
            )
            for chat_turn in st.session_state.phase4_chat_history:
                display_chat_message("user", chat_turn["question"])
                display_chat_message("assistant", chat_turn["answer"])
            st.markdown("</div>", unsafe_allow_html=True)


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

def render_sidebar():
    st.sidebar.markdown(
        """<p style="font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:600;
                     letter-spacing:1.2px;text-transform:uppercase;color:var(--teal);
                     margin-bottom:10px;">Upload Report</p>""",
        unsafe_allow_html=True,
    )

    uploaded_file = st.sidebar.file_uploader(
        "📂 Upload Medical Report",
        type=["pdf", "txt", "docx"],
        help="Supported formats: PDF, TXT, DOCX. Maximum upload size: 50MB.",
        label_visibility="visible",
    )

    st.sidebar.markdown("---")

    st.sidebar.markdown(
        """<p style="font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:600;
                     letter-spacing:1.2px;text-transform:uppercase;color:var(--teal);
                     margin-bottom:10px;">Navigation</p>""",
        unsafe_allow_html=True,
    )

    if "active_patient_section" not in st.session_state:
        st.session_state.active_patient_section = PATIENT_SECTIONS[0]

    active_section = st.sidebar.radio(
        "Choose a section",
        PATIENT_SECTIONS,
        index=PATIENT_SECTIONS.index(st.session_state.active_patient_section),
        label_visibility="collapsed",
    )

    st.session_state.active_patient_section = active_section

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """<p style="font-size:11.5px;color:var(--text-muted);line-height:1.6;">
            MediInsight is an AI assistant for understanding reports.<br>
            <strong style="color:var(--rose);">It does not replace a doctor.</strong>
        </p>""",
        unsafe_allow_html=True,
    )

    return uploaded_file, active_section


# ─── MAIN RENDER ──────────────────────────────────────────────────────────────

def render_active_section(active_section, processed_data):
    extracted_values = processed_data["extracted_values"]
    severity_results = processed_data["severity_results"]
    report_sections = processed_data["report_sections"]
    semantic_sections = processed_data["semantic_sections"]
    retrieved_context = processed_data["retrieved_context"]
    summary = processed_data["summary"]

    health_concerns_count = calculate_health_concerns(report_sections, severity_results)

    if active_section == "📋 Simplified Report":
        display_simplified_report(
            summary, extracted_values, severity_results,
            report_sections, retrieved_context, health_concerns_count,
        )

    elif active_section == "⚠️ Important Findings":
        display_important_findings(severity_results, report_sections)

    elif active_section == "🧪 Medical Values":
        display_medical_values(extracted_values)

    elif active_section == "💬 Ask Questions":
        medical_chatbot = load_medical_chatbot()
        display_medical_chatbot(
            chatbot=medical_chatbot,
            extracted_values=extracted_values,
            severity_results=severity_results,
            report_sections=report_sections,
            semantic_sections=semantic_sections,
            retrieved_context=retrieved_context,
        )

    elif active_section == "❤️ Health Concerns":
        display_health_concerns(report_sections, severity_results)


def main():
    uploaded_file, active_section = render_sidebar()

    if uploaded_file is None:
        display_empty_state()
        return

    uploaded_file_bytes = uploaded_file.getvalue()
    current_file_hash = get_file_hash(uploaded_file_bytes)
    current_processing_signature = (
        current_file_hash,
        uploaded_file.name,
        True,
        "FAISS Vector Retrieval",
        "single_export_v1",
    )

    if (
        "processed_signature" not in st.session_state
        or st.session_state.processed_signature != current_processing_signature
    ):
        with st.spinner("Analysing your medical report..."):
            processed_data = process_uploaded_report(
                uploaded_file=uploaded_file,
                use_semantic_nlp=True,
                retrieval_engine="FAISS Vector Retrieval",
            )

        st.session_state.processed_signature = current_processing_signature
        st.session_state.processed_data = processed_data
        st.session_state.phase4_chat_history = []
        st.session_state.phase4_latest_question = ""
        st.session_state.phase4_latest_answer = ""
        st.session_state.show_chat_history = False

    processed_data = st.session_state.processed_data

    if not processed_data["success"]:
        st.error(processed_data["error"])
        return

    render_active_section(active_section, processed_data)


main()