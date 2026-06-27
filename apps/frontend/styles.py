"""
Premium CSS theme injection for the EcoNav AI Dashboard.
Uses glassmorphism, Google Fonts (Inter), and a dark emerald + charcoal palette.
"""

THEME_CSS = """
<style>
    /* ===== Google Font ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ===== Root Variables ===== */
    :root {
        --bg-primary: #0a0f1a;
        --bg-secondary: #111827;
        --bg-card: rgba(17, 24, 39, 0.7);
        --bg-glass: rgba(255, 255, 255, 0.03);
        --border-glass: rgba(255, 255, 255, 0.08);
        --accent-green: #10b981;
        --accent-green-glow: rgba(16, 185, 129, 0.3);
        --accent-emerald: #34d399;
        --accent-blue: #3b82f6;
        --accent-purple: #8b5cf6;
        --accent-amber: #f59e0b;
        --accent-red: #ef4444;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --gradient-green: linear-gradient(135deg, #10b981 0%, #059669 100%);
        --gradient-blue: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
        --gradient-card: linear-gradient(135deg, rgba(16,185,129,0.05) 0%, rgba(59,130,246,0.05) 100%);
    }

    /* ===== Global Reset ===== */
    .stApp {
        background: var(--bg-primary) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: var(--text-primary) !important;
    }
    
    .stApp > header {
        background: transparent !important;
    }
    
    /* ===== Main Content ===== */
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px !important;
    }

    /* ===== Sidebar ===== */
    section[data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-glass) !important;
    }
    
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--text-primary) !important;
    }

    /* ===== Tabs ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: var(--bg-secondary) !important;
        border-radius: 12px;
        padding: 6px;
        border: 1px solid var(--border-glass);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 8px !important;
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--gradient-green) !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px var(--accent-green-glow) !important;
    }
    
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }
    
    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
    }

    /* ===== Buttons ===== */
    .stButton > button {
        background: var(--gradient-green) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        letter-spacing: 0.02em;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px var(--accent-green-glow) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px var(--accent-green-glow) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Secondary / outline buttons */
    .stButton > button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid var(--accent-green) !important;
        color: var(--accent-green) !important;
        box-shadow: none !important;
    }

    /* ===== Inputs ===== */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-glass) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--accent-green) !important;
        box-shadow: 0 0 0 2px var(--accent-green-glow) !important;
    }

    /* ===== Labels ===== */
    .stTextInput label,
    .stSelectbox label,
    .stNumberInput label,
    .stSlider label {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
    }

    /* ===== Metrics ===== */
    [data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-glass) !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        backdrop-filter: blur(10px);
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-size: 0.8rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    
    [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
    }

    /* ===== Expanders ===== */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-glass) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }

    /* ===== Alerts / Info Boxes ===== */
    .stAlert {
        border-radius: 10px !important;
        border: 1px solid var(--border-glass) !important;
    }

    /* ===== Dividers ===== */
    hr {
        border-color: var(--border-glass) !important;
    }

    /* ===== Scrollbar ===== */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: var(--bg-primary);
    }
    ::-webkit-scrollbar-thumb {
        background: var(--text-muted);
        border-radius: 3px;
    }

    /* ===== Glass Card Utility ===== */
    .glass-card {
        background: var(--bg-card);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--border-glass);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 16px;
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        border-color: rgba(16, 185, 129, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    /* ===== Best Route Highlight ===== */
    .best-route-card {
        background: linear-gradient(135deg, rgba(16,185,129,0.12) 0%, rgba(52,211,153,0.06) 100%) !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 16px;
        position: relative;
        overflow: hidden;
    }
    
    .best-route-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 4px;
        height: 100%;
        background: var(--gradient-green);
    }

    /* ===== Alt Route ===== */
    .alt-route-card {
        background: var(--bg-card);
        border: 1px solid var(--border-glass);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 12px;
        transition: all 0.3s ease;
    }
    
    .alt-route-card:hover {
        border-color: rgba(59, 130, 246, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    
    /* ===== Stat Pill ===== */
    .stat-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255,255,255,0.05);
        border: 1px solid var(--border-glass);
        border-radius: 20px;
        padding: 6px 14px;
        font-size: 0.82rem;
        color: var(--text-secondary);
        margin-right: 8px;
        margin-bottom: 6px;
    }
    
    .stat-pill.green { color: var(--accent-emerald); border-color: rgba(16,185,129,0.2); }
    .stat-pill.blue { color: var(--accent-blue); border-color: rgba(59,130,246,0.2); }
    .stat-pill.amber { color: var(--accent-amber); border-color: rgba(245,158,11,0.2); }
    .stat-pill.red { color: var(--accent-red); border-color: rgba(239,68,68,0.2); }

    /* ===== Hero Banner ===== */
    .hero-banner {
        background: linear-gradient(135deg, rgba(16,185,129,0.08) 0%, rgba(59,130,246,0.08) 50%, rgba(139,92,246,0.08) 100%);
        border: 1px solid var(--border-glass);
        border-radius: 20px;
        padding: 32px;
        margin-bottom: 24px;
        text-align: center;
    }
    
    .hero-banner h1 {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #10b981, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    
    .hero-banner p {
        color: var(--text-secondary);
        font-size: 1rem;
        max-width: 600px;
        margin: 0 auto;
    }

    /* ===== Place Card ===== */
    .place-card {
        background: var(--bg-card);
        border: 1px solid var(--border-glass);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .place-card .place-name {
        font-weight: 600;
        color: var(--text-primary);
        font-size: 0.95rem;
    }
    
    .place-card .place-meta {
        color: var(--text-muted);
        font-size: 0.78rem;
    }

    /* ===== Status Indicator ===== */
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
        animation: pulse 2s ease-in-out infinite;
    }
    
    .status-dot.online { background: var(--accent-green); }
    .status-dot.offline { background: var(--accent-red); }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }

    /* ===== Section Headers ===== */
    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* ===== Training Log ===== */
    .training-log {
        background: var(--bg-secondary);
        border: 1px solid var(--border-glass);
        border-radius: 12px;
        padding: 16px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: var(--accent-emerald);
        max-height: 300px;
        overflow-y: auto;
    }
</style>
"""

def inject_theme():
    """Call this at the top of app.py to inject the premium theme."""
    import streamlit as st
    st.markdown(THEME_CSS, unsafe_allow_html=True)
