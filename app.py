import streamlit as st
import torch
from PIL import Image
import pandas as pd
from datetime import datetime, timedelta
import clip
import numpy as np
import cv2
import re
import easyocr
from supabase import create_client

# -----------------------------
# SUPABASE INIT
# -----------------------------
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(
    page_title="Smart Kühlschrank",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# -----------------------------
# CUSTOM CSS — Mobile App Style
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* ── Global Reset ── */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ── Background ── */
.stApp {
    background: #F0F4FF;
    min-height: 100vh;
    max-width: 430px;
    margin: 0 auto;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 0 !important;
    max-width: 430px !important;
}

/* ── Top Header Bar ── */
.top-header {
    background: #2C3FD6;
    padding: 52px 20px 20px;
    position: relative;
    border-radius: 0 0 28px 28px;
    margin-bottom: 8px;
}
.top-header h1 {
    color: white !important;
    font-size: 1.6rem !important;
    font-weight: 800 !important;
    margin: 0 0 4px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
.top-header p {
    color: rgba(255,255,255,0.65) !important;
    font-size: 0.85rem !important;
    margin: 0 !important;
    font-weight: 500 !important;
}
.header-icon {
    position: absolute;
    top: 52px;
    right: 20px;
    width: 40px;
    height: 40px;
    background: rgba(255,255,255,0.15);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
}

/* ── Stats Bar ── */
.stats-row {
    display: flex;
    gap: 10px;
    padding: 16px 20px 8px;
}
.stat-card {
    flex: 1;
    background: white;
    border-radius: 16px;
    padding: 12px 10px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(44,63,214,0.08);
}
.stat-card .stat-num {
    font-size: 1.4rem;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 3px;
}
.stat-card .stat-label {
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: #9aa0b8;
}
.stat-card.blue  .stat-num { color: #2C3FD6; }
.stat-card.red   .stat-num { color: #E63946; }
.stat-card.amber .stat-num { color: #E8950A; }
.stat-card.green .stat-num { color: #2A9D5C; }

/* ── Section Title ── */
.section-title {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #9aa0b8;
    padding: 12px 20px 6px;
}

/* ── Inventory Cards ── */
.inv-card {
    background: white;
    margin: 0 16px 10px;
    border-radius: 18px;
    padding: 14px 16px;
    display: flex;
    align-items: center;
    gap: 14px;
    box-shadow: 0 2px 12px rgba(44,63,214,0.07);
    border-left: 4px solid transparent;
}
.inv-card.danger { border-left-color: #E63946; }
.inv-card.warn   { border-left-color: #E8950A; }
.inv-card.ok     { border-left-color: #2A9D5C; }
.inv-card.none   { border-left-color: #CBD0E8; }

.inv-icon {
    width: 46px;
    height: 46px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
    flex-shrink: 0;
}
.inv-icon.danger { background: #FFF0F1; }
.inv-icon.warn   { background: #FFF6E8; }
.inv-icon.ok     { background: #EDFAF4; }
.inv-icon.none   { background: #F2F3F9; }

.inv-info { flex: 1; min-width: 0; }
.inv-name {
    font-weight: 700;
    font-size: 0.95rem;
    color: #1A1F3C;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.inv-meta {
    font-size: 0.75rem;
    color: #9aa0b8;
    font-weight: 500;
    margin-top: 2px;
}

.inv-badge {
    flex-shrink: 0;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 20px;
    white-space: nowrap;
}
.inv-badge.danger { background: #FFF0F1; color: #E63946; }
.inv-badge.warn   { background: #FFF6E8; color: #E8950A; }
.inv-badge.ok     { background: #EDFAF4; color: #2A9D5C; }
.inv-badge.none   { background: #F2F3F9; color: #9aa0b8; }

/* ── Empty State ── */
.empty-state {
    text-align: center;
    padding: 3rem 2rem;
    color: #9aa0b8;
}
.empty-state .empty-icon {
    font-size: 3.5rem;
    display: block;
    margin-bottom: 12px;
}
.empty-state p {
    font-size: 0.95rem;
    font-weight: 600;
    color: #9aa0b8;
    margin: 0;
}

/* ── Bottom Navigation Shell (visual only) ── */
.bottom-nav-shell {
    position: fixed;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 430px;
    max-width: 100vw;
    background: white;
    border-top: 1px solid #E8EAF6;
    display: flex;
    align-items: center;
    justify-content: space-around;
    padding: 10px 0 20px;
    z-index: 998;
    box-shadow: 0 -4px 20px rgba(44,63,214,0.08);
    pointer-events: none;
}
.nav-slot {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    flex: 1;
}
.nav-icon-wrap {
    width: 40px;
    height: 40px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
}
.nav-slot.active .nav-icon-wrap {
    background: #EEF1FF;
}
.nav-slot .nav-label {
    font-size: 0.65rem;
    font-weight: 700;
    color: #9aa0b8;
}
.nav-slot.active .nav-label {
    color: #2C3FD6;
}
.nav-slot.center {
    position: relative;
    top: -14px;
}
.fab-visual {
    width: 56px;
    height: 56px;
    border-radius: 18px;
    background: #F4A024;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
    color: white;
    box-shadow: 0 6px 20px rgba(244,160,36,0.45);
}

/* ── Nav button overlay (invisible real buttons) ── */
div[data-testid="stHorizontalBlock"]:has(button[kind="secondary"][data-testid*="nav_"]),
div[data-testid="stHorizontalBlock"]:last-of-type {
    position: fixed !important;
    bottom: 0 !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: 430px !important;
    max-width: 100vw !important;
    z-index: 999 !important;
    padding: 10px 0 20px !important;
    background: transparent !important;
    gap: 0 !important;
}

/* Make nav buttons invisible but clickable */
button[key="nav_inventar"],
button[key="nav_fab"],
button[key="nav_scan"] {
    opacity: 0 !important;
    height: 70px !important;
    cursor: pointer !important;
}

/* Universal nav button invisibility via data-testid */
[data-testid="stBaseButton-secondary"]:has(+ [data-testid]),
.nav-btn-overlay button {
    opacity: 0 !important;
    height: 70px !important;
}

/* ── Scan Page ── */
.scan-header {
    background: #2C3FD6;
    padding: 52px 20px 24px;
    border-radius: 0 0 28px 28px;
    margin-bottom: 16px;
}
.scan-header h1 {
    color: white !important;
    font-size: 1.6rem !important;
    font-weight: 800 !important;
    margin: 0 0 4px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
.scan-header p {
    color: rgba(255,255,255,0.65) !important;
    font-size: 0.85rem !important;
    margin: 0 !important;
}

/* ── Scan Cards ── */
.scan-section {
    background: white;
    margin: 0 16px 12px;
    border-radius: 20px;
    padding: 18px 18px 12px;
    box-shadow: 0 2px 12px rgba(44,63,214,0.07);
}
.scan-section-title {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #9aa0b8;
    margin-bottom: 12px;
}

/* ── Detected pill ── */
.detected-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #EEF1FF;
    color: #2C3FD6;
    border-radius: 30px;
    padding: 8px 16px;
    font-weight: 700;
    font-size: 0.9rem;
    margin-top: 6px;
}
.detected-pill .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #2C3FD6;
    flex-shrink: 0;
}

/* ── Save button override ── */
.stButton > button {
    border-radius: 14px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important;
    padding: 0.65rem 1.8rem !important;
    font-size: 0.95rem !important;
    border: none !important;
    transition: all 0.2s ease !important;
    background: #2C3FD6 !important;
    color: white !important;
    width: 100% !important;
}
.stButton > button:hover {
    background: #1F2EA8 !important;
    transform: translateY(-1px) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: #EEF1FF;
    border-radius: 12px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 10px !important;
    padding: 0.35rem 1rem !important;
    font-weight: 600 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.82rem !important;
    border: none !important;
    color: #9aa0b8 !important;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    color: #2C3FD6 !important;
    box-shadow: 0 2px 8px rgba(44,63,214,0.12) !important;
}

/* ── Text inputs ── */
.stTextInput > div > div > input {
    border-radius: 12px !important;
    border: 1.5px solid #E0E4F5 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    padding: 0.55rem 1rem !important;
    background: #F5F7FF !important;
}
.stTextInput > div > div > input:focus {
    border-color: #2C3FD6 !important;
    background: white !important;
    box-shadow: 0 0 0 3px rgba(44,63,214,0.1) !important;
}

/* ── Alerts ── */
.stAlert {
    border-radius: 14px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
}

/* ── Camera input ── */
.stCameraInput > div { border-radius: 16px !important; overflow: hidden; }
[data-testid="stCameraInput"] { border-radius: 16px !important; }

/* ── Padding for bottom nav ── */
.main-content { padding-bottom: 90px; }

/* ── Divider ── */
.divider {
    height: 1px;
    background: #E8EAF6;
    margin: 8px 20px 0;
}

/* ── Page nav selector (hidden visually) ── */
.stSelectbox { display: none !important; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# MODELS (cached)
# -----------------------------
@st.cache_resource
def load_models():
    model, preprocess = clip.load("ViT-B/32")
    return model, preprocess

model, preprocess = load_models()

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['de', 'en'])

ocr = load_ocr()

# -----------------------------
# LABELS
# -----------------------------
labels = [
    "ein Apfel","eine Banane","eine Orange","eine Birne","eine Erdbeere",
    "eine Traube","eine Zitrone","eine Limette","eine Mango","eine Ananas",
    "eine Wassermelone","eine Kirsche","ein Pfirsich","eine Nektarine",
    "eine Heidelbeere","eine Himbeere","eine Brombeere","eine Kiwi",
    "eine Granatapfel","eine Grapefruit","eine Papaya",
    "eine Tomate","eine Gurke","eine Paprika","eine Karotte","eine Kartoffel",
    "eine Zwiebel","ein Knoblauch","ein Brokkoli","ein Blumenkohl","ein Salatkopf",
    "eine Zucchini","eine Aubergine","ein Spinat","eine Avocado","ein Pilz",
    "ein Käse","eine Milchpackung","ein Joghurt","ein Quark","ein Frischkäse",
    "ein Stück Butter","eine Sahne","ein Pudding",
    "ein Hähnchen","ein Rindfleisch","ein Schweinefleisch","ein Fischfilet",
    "eine Wurst","ein Schinken","eine Salami",
    "ein Brot","ein Brötchen","eine Pizza","ein Croissant","ein Sandwich",
    "eine Schokolade","ein Keks","eine Packung Chips","ein Eis","eine Cola"
]

text_tokens = clip.tokenize(labels)

# -----------------------------
# SESSION STATE
# -----------------------------
if "food_item" not in st.session_state:
    st.session_state.food_item = None
if "mhd_value" not in st.session_state:
    st.session_state.mhd_value = None
if "page" not in st.session_state:
    st.session_state.page = "inventar"

# -----------------------------
# HELPERS
# -----------------------------
def normalize_date(value):
    if not value:
        return None
    value = value.strip()
    if re.match(r"\d{4}-\d{2}-\d{2}", value):
        return value
    match = re.match(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{2,4})", value)
    if match:
        d, m, y = match.groups()
        if len(y) == 2:
            y = "20" + y
        return f"{y}-{int(m):02d}-{int(d):02d}"
    return None

def extract_mhd(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(3.0, (8, 8))
    gray = clahe.apply(gray)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    result = ocr.readtext(thresh, detail=0)
    text = " ".join(result)
    match = re.search(r"\d{2}[.\-/]\d{2}[.\-/]\d{2,4}", text)
    return match.group() if match else None

def food_emoji(name):
    mapping = {
        "Apfel": "🍎", "Banane": "🍌", "Orange": "🍊", "Birne": "🍐",
        "Erdbeere": "🍓", "Traube": "🍇", "Zitrone": "🍋", "Limette": "🍋",
        "Mango": "🥭", "Ananas": "🍍", "Wassermelone": "🍉", "Kirsche": "🍒",
        "Pfirsich": "🍑", "Heidelbeere": "🫐", "Himbeere": "🍓",
        "Kiwi": "🥝", "Tomate": "🍅", "Gurke": "🥒", "Paprika": "🫑",
        "Karotte": "🥕", "Kartoffel": "🥔", "Zwiebel": "🧅", "Knoblauch": "🧄",
        "Brokkoli": "🥦", "Blumenkohl": "🥦", "Salat": "🥗", "Avocado": "🥑",
        "Pilz": "🍄", "Käse": "🧀", "Milch": "🥛", "Joghurt": "🥛",
        "Butter": "🧈", "Sahne": "🥛", "Hähnchen": "🍗", "Rindfleisch": "🥩",
        "Schweinefleisch": "🥩", "Fisch": "🐟", "Wurst": "🌭", "Schinken": "🥩",
        "Brot": "🍞", "Brötchen": "🥐", "Pizza": "🍕", "Croissant": "🥐",
        "Schokolade": "🍫", "Keks": "🍪", "Chips": "🥔", "Eis": "🍦",
        "Cola": "🥤"
    }
    for k, v in mapping.items():
        if k.lower() in name.lower():
            return v
    return "🛒"

# -----------------------------
# BOTTOM NAV — real st.buttons styled as bottom bar
# -----------------------------
def bottom_nav(active):
    inv_active = "active" if active == "inventar" else ""
    scan_active = "active" if active == "scan" else ""

    # Outer fixed bar (pure visual shell)
    st.markdown(f"""
    <div class="bottom-nav-shell">
        <div class="nav-slot left {inv_active}">
            <div class="nav-icon-wrap">🏠</div>
            <span class="nav-label">Inventar</span>
        </div>
        <div class="nav-slot center">
            <div class="fab-visual">＋</div>
        </div>
        <div class="nav-slot right {scan_active}">
            <div class="nav-icon-wrap">📷</div>
            <span class="nav-label">Scannen</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Real invisible Streamlit buttons overlaid on top
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Inventar", key="nav_inventar", use_container_width=True):
            st.session_state.page = "inventar"
            st.rerun()
    with col2:
        if st.button("＋", key="nav_fab", use_container_width=True):
            st.session_state.page = "scan"
            st.rerun()
    with col3:
        if st.button("Scannen", key="nav_scan", use_container_width=True):
            st.session_state.page = "scan"
            st.rerun()

# -----------------------------
# PAGE: INVENTAR
# -----------------------------
if st.session_state.page == "inventar":

    data = supabase.table("fridge_inventory").select("*").execute().data

    today = datetime.now().date()
    total = len(data) if data else 0
    danger_count = warn_count = ok_count = 0

    if data:
        def parse_date(v):
            try:
                return datetime.fromisoformat(v)
            except:
                return datetime.max

        data = sorted(data, key=lambda x: parse_date(x["mhd"]) if x["mhd"] else datetime.max)

        for row in data:
            try:
                mhd_date = datetime.fromisoformat(row["mhd"]).date()
                diff = (mhd_date - today).days
                if diff <= 2:
                    danger_count += 1
                elif diff <= 5:
                    warn_count += 1
                else:
                    ok_count += 1
            except:
                ok_count += 1

    # Header
    st.markdown(f"""
    <div class="top-header">
        <h1>🧊 Mein Kühlschrank</h1>
        <p>{total} Produkte gespeichert</p>
        <div class="header-icon">🔍</div>
    </div>
    """, unsafe_allow_html=True)

    # Stats row
    st.markdown(f"""
    <div class="stats-row">
        <div class="stat-card blue">
            <div class="stat-num">{total}</div>
            <div class="stat-label">Gesamt</div>
        </div>
        <div class="stat-card red">
            <div class="stat-num">{danger_count}</div>
            <div class="stat-label">Ablaufend</div>
        </div>
        <div class="stat-card amber">
            <div class="stat-num">{warn_count}</div>
            <div class="stat-label">Bald</div>
        </div>
        <div class="stat-card green">
            <div class="stat-num">{ok_count}</div>
            <div class="stat-label">Frisch</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Alle Produkte</div>", unsafe_allow_html=True)

    if data:
        for row in data:
            status = "none"
            badge_text = "Kein MHD"
            diff_text = ""

            try:
                mhd_date = datetime.fromisoformat(row["mhd"]).date()
                diff = (mhd_date - today).days
                if diff < 0:
                    status = "danger"
                    badge_text = "Abgelaufen"
                elif diff <= 2:
                    status = "danger"
                    badge_text = f"Noch {diff}T"
                elif diff <= 5:
                    status = "warn"
                    badge_text = f"Noch {diff}T"
                else:
                    status = "ok"
                    badge_text = f"Noch {diff}T"
                diff_text = f"MHD: {str(row['mhd'])[:10]}"
            except:
                diff_text = "Kein MHD"

            emoji = food_emoji(row['food_name'])
            added = str(row.get("added_at", ""))[:10]

            col_main, col_del = st.columns([10, 1])
            with col_main:
                st.markdown(f"""
                <div class="inv-card {status}">
                    <div class="inv-icon {status}">{emoji}</div>
                    <div class="inv-info">
                        <div class="inv-name">{row['food_name']}</div>
                        <div class="inv-meta">{diff_text} · Hinzugefügt {added}</div>
                    </div>
                    <div class="inv-badge {status}">{badge_text}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_del:
                if st.button("🗑️", key=f"del_{row['id']}", help="Löschen"):
                    supabase.table("fridge_inventory").delete().eq("id", row["id"]).execute()
                    st.rerun()
    else:
        st.markdown("""
        <div class="empty-state">
            <span class="empty-icon">🧺</span>
            <p>Dein Kühlschrank ist leer.<br>Tippe auf ＋ um etwas hinzuzufügen.</p>
        </div>
        """, unsafe_allow_html=True)

    bottom_nav("inventar")

# -----------------------------
# PAGE: SCAN
# -----------------------------
elif st.session_state.page == "scan":

    st.markdown("""
    <div class="scan-header">
        <h1>📷 Scannen</h1>
        <p>Lebensmittel & MHD erkennen</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Lebensmittel ──
    st.markdown("""
    <div style="padding: 0 16px 0;">
        <div class="scan-section">
            <div class="scan-section-title">🍎 Lebensmittel</div>
    """, unsafe_allow_html=True)

    food_tab1, food_tab2, food_tab3 = st.tabs(["📷 Kamera", "📁 Upload", "✏️ Manuell"])
    image = None

    with food_tab1:
        cam = st.camera_input("Foto aufnehmen")
        if cam:
            image = Image.open(cam)

    with food_tab2:
        up = st.file_uploader("Bild hochladen", type=["jpg", "png"])
        if up:
            image = Image.open(up)

    with food_tab3:
        manual_food = st.text_input("Lebensmittel eingeben", placeholder="z. B. Joghurt, Milch …")
        if manual_food:
            st.session_state.food_item = manual_food

    if image:
        col_img, col_info = st.columns([1, 1])
        with col_img:
            st.image(image, use_container_width=True)
        with col_info:
            with st.spinner("Erkenne …"):
                img_tensor = preprocess(image).unsqueeze(0)
                with torch.no_grad():
                    logits, _ = model(img_tensor, text_tokens)
                    probs = logits.softmax(dim=-1).cpu().numpy()[0]
            st.session_state.food_item = labels[probs.argmax()]
            st.markdown("**Erkannt:**")
            st.markdown(f"<div class='detected-pill'><span class='dot'></span>{st.session_state.food_item}</div>", unsafe_allow_html=True)

    elif st.session_state.food_item:
        st.markdown(f"<div class='detected-pill'><span class='dot'></span>{st.session_state.food_item}</div>", unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

    # ── MHD ──
    st.markdown("""
    <div style="padding: 0 16px 0;">
        <div class="scan-section">
            <div class="scan-section-title">📅 Mindesthaltbarkeitsdatum</div>
    """, unsafe_allow_html=True)

    mhd_tab1, mhd_tab2, mhd_tab3 = st.tabs(["📷 Kamera", "📁 Upload", "✏️ Manuell"])
    mhd_image = None

    with mhd_tab1:
        cam_mhd = st.camera_input("MHD Foto aufnehmen")
        if cam_mhd:
            mhd_image = Image.open(cam_mhd)

    with mhd_tab2:
        up_mhd = st.file_uploader("MHD Bild hochladen", type=["jpg", "png"], key="mhd")
        if up_mhd:
            mhd_image = Image.open(up_mhd)

    with mhd_tab3:
        manual_mhd = st.text_input("Datum eingeben", placeholder="z. B. 31.12.2025")
        if manual_mhd:
            st.session_state.mhd_value = manual_mhd

    if mhd_image:
        col_m1, col_m2 = st.columns([1, 1])
        with col_m1:
            st.image(mhd_image, use_container_width=True)
        with col_m2:
            if st.button("Datum erkennen"):
                with st.spinner("Lese Datum …"):
                    st.session_state.mhd_value = extract_mhd(mhd_image)
                if st.session_state.mhd_value:
                    st.success(f"Erkannt: **{st.session_state.mhd_value}**")
                else:
                    st.warning("Kein Datum gefunden.")

    elif st.session_state.mhd_value:
        st.markdown(f"<div class='detected-pill'><span class='dot'></span>{st.session_state.mhd_value}</div>", unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

    # ── Speichern ──
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    if st.session_state.food_item:
        mhd_display = st.session_state.mhd_value or "kein MHD"
        st.markdown(f"""
        <div style="padding: 0 16px; margin-bottom: 12px;">
            <div style="background: #EEF1FF; border-radius: 14px; padding: 12px 16px; display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.5rem;">{food_emoji(st.session_state.food_item)}</span>
                <div>
                    <div style="font-weight: 700; color: #1A1F3C; font-size: 0.95rem;">{st.session_state.food_item}</div>
                    <div style="font-size: 0.75rem; color: #9aa0b8; font-weight: 500;">MHD: {mhd_display}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_btn = st.columns([1, 2, 1])[1]
        with col_btn:
            if st.button("✅ Jetzt speichern"):
                now = datetime.now() + timedelta(hours=2)
                mhd_clean = normalize_date(st.session_state.mhd_value)
                supabase.table("fridge_inventory").insert({
                    "food_name": st.session_state.food_item,
                    "mhd": mhd_clean,
                    "added_at": now.date().isoformat()
                }).execute()
                st.success("🎉 Gespeichert!")
                st.session_state.food_item = None
                st.session_state.mhd_value = None
                st.query_params["page"] = "inventar"
                st.rerun()

    bottom_nav("scan")
