import streamlit as st


def apply_custom_css():
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;0,9..40,800;1,9..40,300&family=Space+Grotesk:wght@300;400;500;600;700&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">

        <style>

        /* ─── RESET & HIDE STREAMLIT CHROME ───────────────────────── */
        header[data-testid="stHeader"],
        div[data-testid="stToolbar"],
        div[data-testid="stStatusWidget"],
        #MainMenu {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
        }

        /* ─── CSS TOKENS ─────────────────────────────────────────── */
        :root {
            --bg-base:        #080E1A;
            --bg-mid:         #0D1626;
            --bg-panel:       #111C2E;
            --glass-bg:       rgba(17, 28, 46, 0.72);
            --glass-border:   rgba(56, 189, 248, 0.14);
            --glass-hover:    rgba(56, 189, 248, 0.08);

            --teal:           #2DD4BF;
            --teal-dim:       rgba(45, 212, 191, 0.18);
            --teal-glow:      rgba(45, 212, 191, 0.30);
            --sky:            #38BDF8;
            --sky-dim:        rgba(56, 189, 248, 0.15);
            --emerald:        #34D399;
            --amber:          #FBBF24;
            --rose:           #FB7185;
            --violet:         #A78BFA;

            --text-primary:   #F0F6FF;
            --text-secondary: #94A3B8;
            --text-muted:     #475569;

            --radius-sm:      10px;
            --radius-md:      16px;
            --radius-lg:      22px;
            --radius-xl:      28px;

            --shadow-card:    0 4px 24px rgba(0, 0, 0, 0.40), 0 1px 4px rgba(0,0,0,0.30);
            --shadow-glow:    0 0 32px rgba(45, 212, 191, 0.12);
        }

        /* ─── GLOBAL BASE ────────────────────────────────────────── */
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            font-family: 'DM Sans', sans-serif !important;
            background-color: var(--bg-base) !important;
            color: var(--text-primary) !important;
        }

        .stApp {
            background:
                radial-gradient(ellipse 80% 50% at 10% -10%, rgba(56, 189, 248, 0.07) 0%, transparent 60%),
                radial-gradient(ellipse 60% 40% at 90% 110%, rgba(45, 212, 191, 0.06) 0%, transparent 55%),
                radial-gradient(ellipse 40% 30% at 50% 50%, rgba(167, 139, 250, 0.04) 0%, transparent 70%),
                var(--bg-base) !important;
            background-attachment: fixed !important;
        }

        /* Subtle dot-grid texture overlay */
        .stApp::before {
            content: '';
            position: fixed;
            inset: 0;
            background-image: radial-gradient(rgba(56, 189, 248, 0.06) 1px, transparent 1px);
            background-size: 28px 28px;
            pointer-events: none;
            z-index: 0;
        }

        .main .block-container {
            padding-top: 1.8rem !important;
            padding-bottom: 3rem !important;
            max-width: 1380px !important;
            position: relative;
            z-index: 1;
        }

        p, li, span, label, div {
            color: var(--text-primary) !important;
            font-family: 'DM Sans', sans-serif !important;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Space Grotesk', sans-serif !important;
            color: var(--text-primary) !important;
            letter-spacing: -0.4px;
        }

        /* ─── SIDEBAR ────────────────────────────────────────────── */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0A1221 0%, #0D1626 100%) !important;
            border-right: 1px solid var(--glass-border) !important;
            box-shadow: 4px 0 32px rgba(0, 0, 0, 0.40) !important;

            min-width: 320px !important;
            width: 320px !important;
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            z-index: 999999 !important;
        }

        section[data-testid="stSidebar"][aria-expanded="false"] {
            transform: translateX(0px) !important;
            margin-left: 0px !important;
        }

        section[data-testid="stSidebar"] > div {
            padding-top: 1.5rem !important;
        }

        section[data-testid="stSidebar"] * {
            color: var(--text-primary) !important;
            font-family: 'DM Sans', sans-serif !important;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] .markdown-text-container strong {
            font-family: 'Space Grotesk', sans-serif !important;
            color: var(--teal) !important;
            font-size: 12px !important;
            font-weight: 600 !important;
            letter-spacing: 1.2px !important;
            text-transform: uppercase !important;
        }

        /* ─── FILE UPLOADER ─────────────────────────────────────── */
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] {
            background: rgba(13, 22, 40, 0.80) !important;
            border-radius: var(--radius-md) !important;
            padding: 4px 12px 12px 12px !important;
            border: 1px solid var(--glass-border) !important;
            box-shadow: var(--shadow-card);
        }

        /* Label above the dropzone */
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] label {
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 12px !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px !important;
            color: var(--text-primary) !important;
            margin-bottom: 8px !important;
            display: block !important;
        }

        /* Kill backgrounds inside uploader */
        section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"],
        section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] *,
        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"],
        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {
            background-color: transparent !important;
            color: var(--text-primary) !important;
        }

        /* Dropzone box */
        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
            border: 1.5px dashed rgba(45, 212, 191, 0.40) !important;
            border-radius: var(--radius-sm) !important;
            background: rgba(45, 212, 191, 0.03) !important;
            padding: 14px 10px !important;
            text-align: center !important;
            transition: all 0.25s ease;
        }

        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]:hover {
            border-color: rgba(45, 212, 191, 0.70) !important;
            background: rgba(45, 212, 191, 0.07) !important;
        }

        /* Teal upload icon */
        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] svg {
            color: var(--teal) !important;
            fill: var(--teal) !important;
        }

        /* Browse button inside dropzone */
        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
            background: rgba(45,212,191,0.10) !important;
            color: var(--teal) !important;
            border: 1px solid rgba(45,212,191,0.30) !important;
            border-radius: 8px !important;
            font-size: 12px !important;
            padding: 5px 12px !important;
            margin-top: 6px !important;
        }

        /* Helper text */
        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small,
        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] span {
            font-size: 11px !important;
            color: var(--text-muted) !important;
        }

        /* Uploaded file chip */
        section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] {
            background: rgba(45, 212, 191, 0.06) !important;
            border: 1px solid rgba(45, 212, 191, 0.20) !important;
            border-radius: 8px !important;
            padding: 6px 10px !important;
            margin-top: 8px !important;
        }

        /* Sidebar radio nav */
        section[data-testid="stSidebar"] [data-testid="stRadio"] label {
            background: transparent !important;
            border-radius: var(--radius-sm) !important;
            padding: 9px 14px !important;
            margin: 3px 0 !important;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 14px !important;
            font-weight: 500 !important;
            display: flex !important;
            align-items: center !important;
        }

        section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
            background: var(--glass-hover) !important;
            color: var(--teal) !important;
        }

        section[data-testid="stSidebar"] [data-testid="stRadio"] input:checked + div {
            color: var(--teal) !important;
        }

        /* Sidebar caption */
        section[data-testid="stSidebar"] small,
        section[data-testid="stSidebar"] .caption {
            color: var(--text-muted) !important;
            font-size: 11.5px !important;
            line-height: 1.6 !important;
        }

        /* ─── HERO CARD ──────────────────────────────────────────── */
        .hero-card {
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, #0D2340 0%, #0A1E36 40%, #0E1A30 100%);
            padding: 38px 44px;
            border-radius: var(--radius-xl);
            border: 1px solid rgba(56, 189, 248, 0.20);
            box-shadow: 0 8px 40px rgba(0, 0, 0, 0.50), 0 0 80px rgba(45, 212, 191, 0.06);
            margin-bottom: 28px;
        }

        .hero-card::before {
            content: '';
            position: absolute;
            top: -60px; right: -60px;
            width: 280px; height: 280px;
            background: radial-gradient(circle, rgba(45, 212, 191, 0.12) 0%, transparent 70%);
            pointer-events: none;
        }

        .hero-card::after {
            content: '';
            position: absolute;
            bottom: -40px; left: 30%;
            width: 200px; height: 200px;
            background: radial-gradient(circle, rgba(56, 189, 248, 0.08) 0%, transparent 70%);
            pointer-events: none;
        }

        .hero-eyebrow {
            font-family: 'DM Mono', monospace !important;
            font-size: 11px;
            font-weight: 400;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: var(--teal) !important;
            margin-bottom: 10px;
            opacity: 0.85;
        }

        .hero-title {
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 46px;
            font-weight: 700;
            color: #FFFFFF !important;
            margin-bottom: 14px;
            letter-spacing: -1.5px;
            line-height: 1.1;
        }

        .hero-title span {
            background: linear-gradient(90deg, var(--teal), var(--sky));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .hero-subtitle {
            font-size: 16px;
            line-height: 1.75;
            color: #8BAABF !important;
            max-width: 700px;
            font-weight: 400;
        }

        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(45, 212, 191, 0.10);
            border: 1px solid rgba(45, 212, 191, 0.25);
            border-radius: 100px;
            padding: 4px 12px;
            font-family: 'DM Mono', monospace;
            font-size: 11px;
            color: var(--teal) !important;
            margin-bottom: 16px;
            letter-spacing: 0.5px;
        }

        /* ─── GLASS CARDS ────────────────────────────────────────── */
        .dashboard-card,
        div[data-testid="stForm"],
        div[data-testid="stExpander"] {
            background: var(--glass-bg) !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            border-radius: var(--radius-lg) !important;
            padding: 26px 28px !important;
            border: 1px solid var(--glass-border) !important;
            box-shadow: var(--shadow-card) !important;
            margin-bottom: 18px;
            color: var(--text-primary) !important;
            transition: border-color 0.25s ease, box-shadow 0.25s ease;
        }

        .dashboard-card:hover {
            border-color: rgba(56, 189, 248, 0.25) !important;
            box-shadow: var(--shadow-card), var(--shadow-glow) !important;
        }

        .card-title {
            font-family: 'Space Grotesk', sans-serif !important;
            color: var(--text-primary) !important;
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 14px;
            letter-spacing: -0.2px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .card-title::after {
            content: '';
            flex: 1;
            height: 1px;
            background: linear-gradient(90deg, var(--glass-border), transparent);
        }

        .card-text {
            color: var(--text-secondary) !important;
            font-size: 14.5px;
            line-height: 1.85;
        }

        .card-text ul {
            margin: 6px 0 0 0;
            padding-left: 18px;
        }

        .card-text ul li {
            color: var(--text-secondary) !important;
            margin-bottom: 6px;
            font-size: 14px;
            line-height: 1.6;
        }

        /* ─── METRIC CARDS ───────────────────────────────────────── */
        .metric-card {
            position: relative;
            overflow: hidden;
            background: var(--glass-bg);
            border-radius: var(--radius-lg);
            padding: 26px 20px;
            text-align: center;
            border: 1px solid var(--glass-border);
            box-shadow: var(--shadow-card);
            transition: all 0.25s ease;
        }

        .metric-card:hover {
            transform: translateY(-2px);
            border-color: rgba(45, 212, 191, 0.30);
            box-shadow: var(--shadow-card), 0 0 28px rgba(45, 212, 191, 0.10);
        }

        .metric-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, var(--teal), var(--sky));
            border-radius: var(--radius-lg) var(--radius-lg) 0 0;
        }

        .metric-value {
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 48px;
            font-weight: 700;
            background: linear-gradient(135deg, var(--teal), var(--sky));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1;
            margin-bottom: 8px;
        }

        .metric-label {
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.8px;
            text-transform: uppercase;
            color: var(--text-muted) !important;
            margin-top: 4px;
        }

        /* ─── CHAT CARDS ─────────────────────────────────────────── */
        .assistant-card,
        .user-card {
            border-radius: var(--radius-md);
            padding: 20px 22px;
            color: var(--text-primary) !important;
            line-height: 1.8;
            border: 1px solid var(--glass-border);
            box-shadow: var(--shadow-card);
            margin-bottom: 14px;
            font-size: 14.5px;
            transition: border-color 0.2s ease;
        }

        .assistant-card {
            background: linear-gradient(135deg, rgba(17, 28, 46, 0.85), rgba(13, 26, 40, 0.90));
            border-left: 3px solid var(--emerald);
        }

        .user-card {
            background: linear-gradient(135deg, rgba(14, 22, 40, 0.80), rgba(10, 18, 32, 0.85));
            border-left: 3px solid var(--sky);
        }

        .assistant-card b,
        .user-card b {
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 11px !important;
            font-weight: 600 !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
        }

        .assistant-card b { color: var(--emerald) !important; }
        .user-card b { color: var(--sky) !important; }

        /* ─── INPUTS & FORMS ─────────────────────────────────────── */
        div[data-testid="stTextInput"] *,
        div[data-testid="stTextInput"] input,
        div[data-baseweb="input"],
        div[data-baseweb="input"] *,
        input {
            background-color: rgba(10, 18, 34, 0.90) !important;
            color: var(--text-primary) !important;
            border-color: var(--glass-border) !important;
            caret-color: var(--teal) !important;
            font-family: 'DM Sans', sans-serif !important;
            border-radius: var(--radius-sm) !important;
        }

        input:focus, textarea:focus {
            border-color: rgba(45, 212, 191, 0.45) !important;
            box-shadow: 0 0 0 3px rgba(45, 212, 191, 0.10) !important;
            outline: none !important;
        }

        div[data-baseweb="select"],
        div[data-baseweb="select"] *,
        div[data-baseweb="popover"],
        div[data-baseweb="popover"] * {
            background-color: rgba(10, 18, 34, 0.95) !important;
            color: var(--text-primary) !important;
            font-family: 'DM Sans', sans-serif !important;
        }

        div[data-testid="stForm"] {
            background: rgba(10, 18, 34, 0.60) !important;
            border: 1px solid var(--glass-border) !important;
        }

        input::placeholder,
        textarea::placeholder {
            color: var(--text-muted) !important;
        }

        /* ─── BUTTONS ────────────────────────────────────────────── */
        .stButton > button,
        button {
            font-family: 'Space Grotesk', sans-serif !important;
            border-radius: var(--radius-sm) !important;
            background: rgba(45, 212, 191, 0.08) !important;
            color: var(--teal) !important;
            border: 1px solid rgba(45, 212, 191, 0.30) !important;
            font-weight: 600 !important;
            font-size: 13.5px !important;
            padding: 10px 20px !important;
            letter-spacing: 0.2px;
            transition: all 0.2s ease !important;
        }

        .stButton > button:hover,
        button:hover {
            background: rgba(45, 212, 191, 0.18) !important;
            border-color: rgba(45, 212, 191, 0.60) !important;
            color: #FFFFFF !important;
            box-shadow: 0 0 20px rgba(45, 212, 191, 0.20) !important;
            transform: translateY(-1px);
        }

        .stButton > button:active {
            transform: translateY(0px) !important;
        }

        button:disabled {
            background: rgba(71, 85, 105, 0.25) !important;
            color: var(--text-muted) !important;
            border: 1px solid rgba(71, 85, 105, 0.35) !important;
            cursor: not-allowed;
        }

        /* Download button gets a special gradient treatment */
        .stDownloadButton > button {
            background: linear-gradient(135deg, rgba(45, 212, 191, 0.15), rgba(56, 189, 248, 0.15)) !important;
            border: 1px solid rgba(45, 212, 191, 0.40) !important;
            color: var(--teal) !important;
            width: 100%;
        }

        .stDownloadButton > button:hover {
            background: linear-gradient(135deg, rgba(45, 212, 191, 0.28), rgba(56, 189, 248, 0.28)) !important;
            box-shadow: 0 0 28px rgba(45, 212, 191, 0.22) !important;
            color: #FFFFFF !important;
        }

        /* ─── DATAFRAMES ─────────────────────────────────────────── */
        .stDataFrame {
            border-radius: var(--radius-md) !important;
            overflow: hidden;
            border: 1px solid rgba(56, 189, 248, 0.20) !important;
        }

        /* Outer wrapper — solid, not transparent */
        [data-testid="stDataFrame"] {
            background-color: #0F1C2E !important;
        }

        /* Every cell element: force solid bg + bright text */
        [data-testid="stDataFrame"] *,
        [data-testid="stDataFrame"] td,
        [data-testid="stDataFrame"] div,
        [data-testid="stDataFrame"] span,
        [data-testid="stDataFrame"] p {
            background-color: #0F1C2E !important;
            color: #D1E8FF !important;
            font-family: 'DM Sans', sans-serif !important;
            font-size: 13.5px !important;
            border-color: rgba(56, 189, 248, 0.10) !important;
        }

        /* Column headers */
        [data-testid="stDataFrame"] th,
        [data-testid="stDataFrame"] [role="columnheader"],
        [data-testid="stDataFrame"] [role="columnheader"] * {
            background-color: #0A1526 !important;
            color: #2DD4BF !important;
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 11.5px !important;
            font-weight: 700 !important;
            letter-spacing: 0.7px !important;
            text-transform: uppercase !important;
            border-bottom: 1px solid rgba(45, 212, 191, 0.25) !important;
        }

        /* Row hover */
        [data-testid="stDataFrame"] tr:hover td,
        [data-testid="stDataFrame"] [role="row"]:hover [role="cell"],
        [data-testid="stDataFrame"] [role="row"]:hover [role="cell"] * {
            background-color: rgba(45, 212, 191, 0.07) !important;
        }

        /* Alternating row shade */
        [data-testid="stDataFrame"] [role="row"]:nth-child(even) [role="cell"],
        [data-testid="stDataFrame"] [role="row"]:nth-child(even) [role="cell"] * {
            background-color: #111E30 !important;
        }

        /* Fix the inner canvas/iframe that Streamlit uses for the Arrow table */
        [data-testid="stDataFrame"] iframe,
        [data-testid="stDataFrame"] canvas {
            background-color: #0F1C2E !important;
        }

        /* ─── HISTORY TOGGLE BUTTON (replaces expander) ─────────── */
        /* This targets the "Show/Hide previous questions" st.button */
        div[data-testid="stButton"] button[kind="secondary"] {
            background: transparent !important;
            border: 1px solid rgba(56, 189, 248, 0.20) !important;
            color: var(--text-muted) !important;
            font-size: 12.5px !important;
            font-weight: 500 !important;
            padding: 8px 16px !important;
            border-radius: 8px !important;
            width: 100% !important;
            text-align: left !important;
            margin-top: 10px !important;
            letter-spacing: 0.2px !important;
        }

        div[data-testid="stButton"] button[kind="secondary"]:hover {
            border-color: rgba(45, 212, 191, 0.45) !important;
            color: var(--teal) !important;
            background: rgba(45, 212, 191, 0.04) !important;
            box-shadow: none !important;
        }

        /* ─── ALERTS / INFO BOXES ────────────────────────────────── */
        div[data-testid="stAlert"] {
            background: rgba(10, 18, 34, 0.80) !important;
            border-radius: var(--radius-sm) !important;
            border: 1px solid var(--glass-border) !important;
            color: var(--text-primary) !important;
        }

        div[data-testid="stAlert"][kind="info"] {
            border-left: 3px solid var(--sky) !important;
        }

        div[data-testid="stAlert"][kind="success"] {
            border-left: 3px solid var(--emerald) !important;
        }

        div[data-testid="stAlert"][kind="warning"] {
            border-left: 3px solid var(--amber) !important;
        }

        div[data-testid="stAlert"][kind="error"] {
            border-left: 3px solid var(--rose) !important;
        }

        /* ─── MARKDOWN / TEXT ────────────────────────────────────── */
        .stMarkdown * {
            color: var(--text-secondary) !important;
        }

        .stMarkdown h3 {
            font-family: 'Space Grotesk', sans-serif !important;
            color: var(--text-primary) !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            margin: 20px 0 12px 0 !important;
        }

        .stMarkdown h4 {
            font-family: 'Space Grotesk', sans-serif !important;
            color: var(--text-secondary) !important;
            font-size: 14px !important;
            font-weight: 500 !important;
        }

        /* ─── SPINNER ────────────────────────────────────────────── */
        .stSpinner > div {
            border-top-color: var(--teal) !important;
        }

        /* ─── SCROLLBAR ──────────────────────────────────────────── */
        ::-webkit-scrollbar {
            width: 5px;
            height: 5px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-base);
        }

        ::-webkit-scrollbar-thumb {
            background: rgba(45, 212, 191, 0.30);
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(45, 212, 191, 0.55);
        }

        /* ─── CAPTION TEXT ───────────────────────────────────────── */
        .stCaption, small {
            color: var(--text-muted) !important;
            font-size: 12px !important;
        }

        /* ─── HR / DIVIDERS ──────────────────────────────────────── */
        hr {
            border-color: var(--glass-border) !important;
            margin: 16px 0 !important;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )