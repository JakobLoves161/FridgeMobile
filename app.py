import streamlit as st
from PIL import Image
from datetime import datetime, timedelta
import numpy as np
import cv2
import re
import easyocr
from supabase import create_client
import tensorflow as tf

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
# CSS
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"], .stApp {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background: #f0f4ff !important;
}

/* ── hide streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 0 !important;
    max-width: 480px !important;
    margin: 0 auto !important;
}

/* ── TOP HEADER ── */
.app-header {
    background: #2d3adf;
    padding: 1.2rem 1.4rem 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
}
.app-header-title {
    font-size: 1.35rem;
    font-weight: 800;
    color: white;
    letter-spacing: -0.3px;
}
.app-header-sub {
    font-size: 0.75rem;
    color: rgba(255,255,255,0.65);
    margin-top: 1px;
    font-weight: 500;
}
.header-icon {
    width: 38px; height: 38px;
    background: rgba(255,255,255,0.15);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
}

/* ── BOTTOM NAV ── */
.bottom-nav {
    position: fixed;
    bottom: 0; left: 50%;
    transform: translateX(-50%);
    width: 100%; max-width: 480px;
    background: #2d3adf;
    border-radius: 24px 24px 0 0;
    padding: 0.8rem 2rem 1.2rem;
    display: flex;
    align-items: center;
    justify-content: space-around;
    z-index: 200;
    box-shadow: 0 -4px 30px rgba(45,58,223,0.3);
}
.nav-item {
    display: flex; flex-direction: column;
    align-items: center; gap: 4px;
    font-size: 0.65rem;
    color: rgba(255,255,255,0.55);
    font-weight: 600;
    cursor: pointer;
    letter-spacing: 0.3px;
}
.nav-item.active { color: white; }
.nav-icon { font-size: 1.3rem; }
.nav-fab {
    width: 52px; height: 52px;
    background: #f5a623;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.6rem;
    color: white;
    box-shadow: 0 4px 20px rgba(245,166,35,0.5);
    margin-top: -24px;
    font-weight: 300;
}

/* ── PAGE CONTENT ── */
.page { padding: 1rem 1rem 7rem; }

/* ── HERO CARD (scan page) ── */
.hero-card {
    background: linear-gradient(135deg, #3d4ef0 0%, #1a9fd4 100%);
    border-radius: 20px;
    padding: 1.4rem;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
}
.hero-card::before {
    content: '';
    position: absolute;
    right: -20px; top: -20px;
    width: 100px; height: 100px;
    background: rgba(255,255,255,0.08);
    border-radius: 50%;
}
.hero-card::after {
    content: '';
    position: absolute;
    right: 30px; bottom: -30px;
    width: 80px; height: 80px;
    background: rgba(255,255,255,0.06);
    border-radius: 50%;
}
.hero-text h2 {
    font-size: 1.1rem !important;
    font-weight: 800 !important;
    color: white !important;
    margin: 0 0 0.3rem !important;
}
.hero-text p {
    font-size: 0.8rem;
    color: rgba(255,255,255,0.75);
    font-weight: 500;
}
.hero-emoji { font-size: 3rem; z-index: 1; }

/* ── SECTION LABEL ── */
.section-label {
    font-size: 0.7rem;
    font-weight: 700;
    color: #9aa3c2;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin: 1.2rem 0 0.6rem;
}

/* ── WHITE CARD ── */
.white-card {
    background: white;
    border-radius: 18px;
    padding: 1.2rem;
    margin-bottom: 0.9rem;
    box-shadow: 0 2px 12px rgba(45,58,223,0.07);
}

/* ── FOOD RESULT PILL ── */
.result-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(90deg, #2d3adf, #1a9fd4);
    color: white;
    border-radius: 30px;
    padding: 0.5rem 1.2rem;
    font-weight: 700;
    font-size: 0.95rem;
    margin-top: 0.5rem;
}
.result-pill-warn {
    background: linear-gradient(90deg, #f5a623, #f76b1c);
}

/* ── INVENTORY STATS ROW ── */
.stats-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-bottom: 1.2rem;
}
.stat-box {
    background: white;
    border-radius: 16px;
    padding: 0.9rem 0.6rem;
    text-align: center;
    box-shadow: 0 2px 10px rgba(45,58,223,0.06);
}
.stat-box .stat-num {
    font-size: 1.5rem;
    font-weight: 800;
    color: #2d3adf;
    line-height: 1;
}
.stat-box .stat-lbl {
    font-size: 0.65rem;
    font-weight: 600;
    color: #9aa3c2;
    margin-top: 3px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.stat-box.danger .stat-num { color: #e03131; }
.stat-box.warn .stat-num   { color: #e67700; }
.stat-box.ok .stat-num     { color: #2f9e44; }

/* ── INVENTORY ITEM CARD ── */
.inv-card {
    background: white;
    border-radius: 16px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.7rem;
    box-shadow: 0 2px 10px rgba(45,58,223,0.06);
    display: flex;
    align-items: center;
    gap: 12px;
    border-left: 4px solid #e9ecef;
}
.inv-card.danger { border-left-color: #ff6b6b; }
.inv-card.warn   { border-left-color: #ffa94d; }
.inv-card.ok     { border-left-color: #51cf66; }

.inv-icon {
    width: 42px; height: 42px;
    background: #f0f4ff;
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem;
    flex-shrink: 0;
}
.inv-info { flex: 1; min-width: 0; }
.inv-name {
    font-size: 0.95rem;
    font-weight: 700;
    color: #1a1f5e;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.inv-meta {
    font-size: 0.72rem;
    color: #9aa3c2;
    font-weight: 500;
    margin-top: 2px;
}
.inv-badge {
    font-size: 0.68rem;
    font-weight: 700;
    padding: 3px 9px;
    border-radius: 20px;
    flex-shrink: 0;
}
.badge-danger { background: #fff0f0; color: #e03131; }
.badge-warn   { background: #fff9e6; color: #e67700; }
.badge-ok     { background: #f0fff4; color: #2f9e44; }
.badge-none   { background: #f5f5f5; color: #999; }

/* ── EMPTY STATE ── */
.empty-inv {
    text-align: center;
    padding: 3rem 1rem;
    color: #bbb;
}
.empty-inv .e-icon { font-size: 3.5rem; margin-bottom: 0.7rem; }
.empty-inv .e-txt  { font-size: 0.95rem; font-weight: 600; }

/* ── Streamlit widget overrides ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: #f0f4ff !important;
    border-radius: 12px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 10px !important;
    padding: 0.35rem 1rem !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    color: #9aa3c2 !important;
    border: none !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    color: #2d3adf !important;
    box-shadow: 0 2px 8px rgba(45,58,223,0.12) !important;
}
.stButton > button {
    border-radius: 14px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    border: none !important;
    transition: all 0.15s !important;
}
.stButton > button[kind="primary"] {
    background: #2d3adf !important;
    color: white !important;
    box-shadow: 0 4px 14px rgba(45,58,223,0.35) !important;
    padding: 0.6rem 2rem !important;
    width: 100% !important;
}
.stTextInput > div > div > input {
    border-radius: 12px !important;
    border: 2px solid #e8ecff !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    background: #f8f9ff !important;
}
.stTextInput > div > div > input:focus {
    border-color: #2d3adf !important;
    box-shadow: 0 0 0 3px rgba(45,58,223,0.1) !important;
}
.stAlert {
    border-radius: 12px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
}
div[data-testid="stImage"] img {
    border-radius: 14px !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# MODELS
# -----------------------------
@st.cache_resource
def load_models():
    model = tf.keras.models.load_model("keras_model.h5", compile=False)
    with open("labels.txt", "r", encoding="utf-8") as f:
        class_names = [line.strip().split(" ", 1)[-1] for line in f.readlines() if line.strip()]
    return model, class_names

model, labels = load_models()

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['de', 'en'])

ocr = load_ocr()

CONFIDENCE_THRESHOLD = 0.70

def classify_image(image):
    img = image.convert("RGB").resize((224, 224))
    arr = np.array(img, dtype=np.float32)
    arr = (arr / 127.5) - 1.0
    arr = np.expand_dims(arr, axis=0)
    predictions = model.predict(arr, verbose=0)
    index = int(np.argmax(predictions[0]))
    confidence = float(predictions[0][index])
    if confidence < CONFIDENCE_THRESHOLD:
        return None
    return labels[index]

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
    name = name.lower()
    mapping = {
        "apfel": "🍎", "banane": "🍌", "orange": "🍊", "birne": "🍐",
        "erdbeere": "🍓", "traube": "🍇", "zitrone": "🍋", "mango": "🥭",
        "tomate": "🍅", "gurke": "🥒", "paprika": "🫑", "karotte": "🥕",
        "kartoffel": "🥔", "zwiebel": "🧅", "knoblauch": "🧄", "brokkoli": "🥦",
        "salat": "🥬", "avocado": "🥑", "pilz": "🍄", "käse": "🧀",
        "milch": "🥛", "joghurt": "🫙", "butter": "🧈", "ei": "🥚",
        "hähnchen": "🍗", "fisch": "🐟", "wurst": "🌭", "brot": "🍞",
        "pizza": "🍕", "schokolade": "🍫", "eis": "🍦", "cola": "🥤",
        "lauch": "🧅", "spinat": "🥬",
    }
    for key, emoji in mapping.items():
        if key in name:
            return emoji
    return "🥫"

# -----------------------------
# SESSION STATE
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "scan"
if "food_item" not in st.session_state:
    st.session_state.food_item = None
if "mhd_value" not in st.session_state:
    st.session_state.mhd_value = None

# -----------------------------
# BOTTOM NAV (always visible)
# -----------------------------
col_nav1, col_nav2, col_nav3, col_nav4, col_nav5 = st.columns(5)

with col_nav1:
    if st.button("📦\nInventar", key="nav_inv"):
        st.session_state.page = "inventory"
        st.rerun()
with col_nav2:
    st.write("")  # spacer
with col_nav3:
    if st.button("➕", key="nav_scan"):
        st.session_state.page = "scan"
        st.rerun()
with col_nav4:
    st.write("")
with col_nav5:
    if st.button("🔔\nAlerts", key="nav_alert"):
        st.session_state.page = "inventory"
        st.rerun()

# Styled bottom nav overlay
scan_active   = "active" if st.session_state.page == "scan" else ""
inv_active    = "active" if st.session_state.page == "inventory" else ""

st.markdown(f"""
<div class="bottom-nav">
    <div class="nav-item {inv_active}">
        <div class="nav-icon">📦</div>
        <span>Inventar</span>
    </div>
    <div class="nav-item">
        <div class="nav-icon">📬</div>
        <span>Alerts</span>
    </div>
    <div class="nav-fab">＋</div>
    <div class="nav-item">
        <div class="nav-icon">🔔</div>
        <span>Info</span>
    </div>
    <div class="nav-item {scan_active}">
        <div class="nav-icon">📷</div>
        <span>Scan</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================
# PAGE: SCAN
# ==============================
if st.session_state.page == "scan":

    st.markdown("""
    <div class="app-header">
        <div>
            <div class="app-header-title">🧊 Smart Kühlschrank</div>
            <div class="app-header-sub">Lebensmittel scannen & verwalten</div>
        </div>
        <div class="header-icon">⚙️</div>
    </div>
    <div class="page">
    <div class="hero-card">
        <div class="hero-text">
            <h2>Neues Lebensmittel</h2>
            <p>Foto machen oder<br>Bild hochladen</p>
        </div>
        <div class="hero-emoji">🥦</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Lebensmittel ──
    st.markdown('<div class="section-label">Lebensmittel erkennen</div>', unsafe_allow_html=True)
    st.markdown('<div class="white-card">', unsafe_allow_html=True)

    food_tab1, food_tab2, food_tab3 = st.tabs(["📷 Kamera", "📁 Upload", "✏️ Manuell"])
    image = None

    with food_tab1:
        cam = st.camera_input("Foto aufnehmen")
        if cam:
            image = Image.open(cam).convert("RGB")
    with food_tab2:
        up = st.file_uploader("Bild hochladen", type=["jpg", "png"])
        if up:
            image = Image.open(up).convert("RGB")
    with food_tab3:
        manual_food = st.text_input("Lebensmittel eingeben", placeholder="z. B. Joghurt, Milch …")
        if manual_food:
            st.session_state.food_item = manual_food

    if image is not None:
        col_img, col_info = st.columns([1, 1])
        with col_img:
            st.image(image, use_container_width=True)
        with col_info:
            with st.spinner("Erkenne …"):
                result = classify_image(image)
            if result is None:
                st.markdown("<div class='result-pill result-pill-warn'>⚠️ Nicht erkannt</div>", unsafe_allow_html=True)
                st.caption("Bitte manuell eingeben")
            else:
                st.session_state.food_item = result
                st.markdown(f"<div class='result-pill'>✅ {result}</div>", unsafe_allow_html=True)

    elif st.session_state.food_item:
        st.markdown(f"<div class='result-pill'>✅ {st.session_state.food_item}</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── MHD ──
    st.markdown('<div class="section-label">Mindesthaltbarkeitsdatum</div>', unsafe_allow_html=True)
    st.markdown('<div class="white-card">', unsafe_allow_html=True)

    mhd_tab1, mhd_tab2, mhd_tab3 = st.tabs(["📷 Kamera", "📁 Upload", "✏️ Manuell"])
    mhd_image = None

    with mhd_tab1:
        cam_mhd = st.camera_input("MHD Foto")
        if cam_mhd:
            mhd_image = Image.open(cam_mhd)
    with mhd_tab2:
        up_mhd = st.file_uploader("MHD Upload", type=["jpg", "png"], key="mhd")
        if up_mhd:
            mhd_image = Image.open(up_mhd)
    with mhd_tab3:
        manual_mhd = st.text_input("Datum eingeben", placeholder="z. B. 31.12.2025")
        if manual_mhd:
            st.session_state.mhd_value = manual_mhd

    if mhd_image:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.image(mhd_image, use_container_width=True)
        with c2:
            if st.button("📅 Datum erkennen"):
                with st.spinner("Lese Datum …"):
                    st.session_state.mhd_value = extract_mhd(mhd_image)
                if st.session_state.mhd_value:
                    st.success(f"✅ {st.session_state.mhd_value}")
                else:
                    st.warning("Nicht gefunden")

    if st.session_state.mhd_value:
        st.info(f"📅 MHD gesetzt: **{st.session_state.mhd_value}**")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Speichern ──
    st.markdown('<div class="section-label">Speichern</div>', unsafe_allow_html=True)
    st.markdown('<div class="white-card">', unsafe_allow_html=True)

    if st.session_state.food_item:
        mhd_display = st.session_state.mhd_value or "kein MHD"
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:1rem;">
            <div style="font-size:2rem;">{food_emoji(st.session_state.food_item)}</div>
            <div>
                <div style="font-weight:800;font-size:1rem;color:#1a1f5e;">{st.session_state.food_item}</div>
                <div style="font-size:0.78rem;color:#9aa3c2;margin-top:2px;">📅 {mhd_display}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("➕ In Kühlschrank speichern", type="primary"):
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
            st.rerun()
    else:
        st.markdown("<div style='color:#bbb;font-size:0.9rem;text-align:center;padding:0.5rem'>Noch kein Lebensmittel erkannt</div>", unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)

# ==============================
# PAGE: INVENTORY
# ==============================
elif st.session_state.page == "inventory":

    st.markdown("""
    <div class="app-header">
        <div>
            <div class="app-header-title">📦 Mein Inventar</div>
            <div class="app-header-sub">Alle Lebensmittel im Überblick</div>
        </div>
        <div class="header-icon">🔍</div>
    </div>
    <div class="page">
    """, unsafe_allow_html=True)

    data = supabase.table("fridge_inventory").select("*").execute().data

    if data:
        def parse_date(v):
            try:
                return datetime.fromisoformat(v)
            except:
                return datetime.max

        data = sorted(data, key=lambda x: parse_date(x["mhd"]) if x["mhd"] else datetime.max)
        today = datetime.now().date()

        total = len(data)
        danger_count = warn_count = ok_count = 0

        for row in data:
            try:
                diff = (datetime.fromisoformat(row["mhd"]).date() - today).days
                if diff <= 2:   danger_count += 1
                elif diff <= 5: warn_count += 1
                else:           ok_count += 1
            except:
                ok_count += 1

        st.markdown(f"""
        <div class="stats-row">
            <div class="stat-box">
                <div class="stat-num">{total}</div>
                <div class="stat-lbl">Gesamt</div>
            </div>
            <div class="stat-box danger">
                <div class="stat-num">{danger_count}</div>
                <div class="stat-lbl">Ablaufend</div>
            </div>
            <div class="stat-box ok">
                <div class="stat-num">{ok_count}</div>
                <div class="stat-lbl">Frisch</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-label">Alle Produkte</div>', unsafe_allow_html=True)

        for row in data:
            added_date = str(row["added_at"]).split("T")[0]
            css_class = ""
            badge_class = "badge-none"
            badge_text = "Kein MHD"
            days_left = None

            try:
                mhd_date = datetime.fromisoformat(row["mhd"]).date()
                days_left = (mhd_date - today).days
                if days_left <= 2:
                    css_class = "danger"
                    badge_class = "badge-danger"
                    badge_text = f"{'Heute!' if days_left <= 0 else f'{days_left}d'}"
                elif days_left <= 5:
                    css_class = "warn"
                    badge_class = "badge-warn"
                    badge_text = f"{days_left}d"
                else:
                    css_class = "ok"
                    badge_class = "badge-ok"
                    badge_text = f"{days_left}d"
            except:
                pass

            mhd_display = row["mhd"] or "—"
            emoji = food_emoji(row["food_name"])

            col_card, col_del = st.columns([9, 1])
            with col_card:
                st.markdown(f"""
                <div class="inv-card {css_class}">
                    <div class="inv-icon">{emoji}</div>
                    <div class="inv-info">
                        <div class="inv-name">{row['food_name']}</div>
                        <div class="inv-meta">MHD: {mhd_display} · Hinzugefügt: {added_date}</div>
                    </div>
                    <div class="inv-badge {badge_class}">{badge_text}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_del:
                if st.button("🗑", key=f"del_{row['id']}", help="Löschen"):
                    supabase.table("fridge_inventory").delete().eq("id", row["id"]).execute()
                    st.rerun()

    else:
        st.markdown("""
        <div class="empty-inv">
            <div class="e-icon">🧺</div>
            <div class="e-txt">Dein Kühlschrank ist leer.<br>Scanne dein erstes Lebensmittel!</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
