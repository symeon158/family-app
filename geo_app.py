# -*- coding: utf-8 -*-
"""
🌍 Γεωγραφία Εξερευνητής — Ε' Δημοτικού
Διαδραστική εφαρμογή Γεωγραφίας βασισμένη στην πραγματική ύλη του σχολικού
βιβλίου (Γεωγραφία Ε' Δημοτικού — Μαθαίνω για την Ελλάδα).

Η Σοφούλα η κουκουβάγια οδηγεί το παιδί σε κουίζ, κάρτες γνώσης και 5 παιχνίδια,
ενώ κερδίζει XP, επίπεδα, αστέρια και παράσημα. Τα λάθη του μαζεύονται για εξάσκηση.

Streamlit + Folium (διαδραστικοί χάρτες) + Plotly (3D υδρόγειος) + gTTS (φωνή).
Όλο το βασικό περιεχόμενο είναι έτοιμο και δωρεάν. Προαιρετικά, αν υπάρχει
OpenAI API key, μπορεί να προστεθεί μία ζωντανή ερώτηση-μπόνους από τα
αποσπάσματα του πραγματικού βιβλίου (knowledge_base.json).
"""
import streamlit as st
import folium
from folium import plugins as folium_plugins
from streamlit_folium import st_folium
import plotly.graph_objects as go
from gtts import gTTS
import datetime, html, json, math, os, io, random, re, struct, wave

import geo_data as gd

try:
    import agents
except Exception:
    agents = None

st.set_page_config(page_title="Γεωγραφία Εξερευνητής", page_icon="🌍", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCORES_FILE = os.path.join(BASE_DIR, "geo_highscores.json")
BADGES_FILE = os.path.join(BASE_DIR, "geo_badges.json")
PROFILES_FILE = os.path.join(BASE_DIR, "geo_profiles.json")
KB_FILE = os.path.join(BASE_DIR, "knowledge_base.json")

DEFAULT_PLAYER = "Εξερευνητής"
AVATARS = ["🦊", "🐢", "🐬", "🦅", "🦉", "🐙", "🦋", "🐱", "🐶", "🦄", "🐼", "🚀"]

BADGES = {
    "maps": "🧭 Μικρός Χαρτογράφος",
    "physical": "🏔️ Εξερευνητής της Φύσης",
    "human": "👥 Γνώστης της Ελλάδας",
    "world": "🤝 Πολίτης της Ευρώπης",
    "perfect": "💯 Τέλειο Κουίζ",
    "streak5": "🔥 Φλεγόμενο Σερί",
    "find": "📍 Μάτι Αετού",
    "compass": "🧭 Χρυσή Πυξίδα",
    "compare": "⚖️ Ξέρω τα Μεγέθη",
    "memory": "🧠 Ελεφαντίσια Μνήμη",
    "voyage": "🎈 Κυβερνήτης Αερόστατου",
    "daily3": "📅 Τρεις Μέρες στη Σειρά",
    "review": "🔁 Διορθώνω τα Λάθη μου",
}

BADGE_HOW = {
    "maps": "70% σωστά σε κουίζ της ενότητας «Χάρτες & Πυξίδα»",
    "physical": "70% σωστά σε κουίζ της ενότητας «Φυσικό Περιβάλλον»",
    "human": "70% σωστά σε κουίζ της ενότητας «Άνθρωπος & Περιφέρειες»",
    "world": "70% σωστά σε κουίζ της ενότητας «Ελλάδα, Ευρώπη & Κόσμος»",
    "perfect": "Όλες οι απαντήσεις σωστές σε ένα κουίζ",
    "streak5": "5 σωστές απαντήσεις στη σειρά",
    "find": "70% των πόντων στο «Ζεστά-Κρύα»",
    "compass": "70% σωστά στο «Κυνήγι Πυξίδας»",
    "compare": "70% σωστά στο «Ποιο είναι πιο...;»",
    "memory": "Τελείωσε το «Παιχνίδι Μνήμης» με λίγες κινήσεις",
    "voyage": "70% των πόντων στο «Ταξίδι με Αερόστατο»",
    "daily3": "Κάνε την αποστολή της ημέρας 3 μέρες στη σειρά",
    "review": "Διόρθωσε όλα τα λάθη σου στην εξάσκηση",
}

LEVELS = [
    (0, "🚣", "Βαρκούλα"), (100, "⛵", "Ιστιοφόρο"), (300, "🚢", "Καράβι"),
    (600, "🎈", "Αερόστατο"), (1000, "✈️", "Αεροπλάνο"), (1600, "🚀", "Πύραυλος"),
]

GAMES = {
    "find": {"icon": "📍", "title": "Ζεστά-Κρύα", "rounds": 5,
             "desc": "Βρες τον τόπο σε χάρτη χωρίς ονόματα. Η Σοφούλα σου λέει αν καίγεσαι!"},
    "compass": {"icon": "🧭", "title": "Κυνήγι Πυξίδας", "rounds": 6,
                "desc": "Προς τα πού πρέπει να πας; Μάθε τα 8 σημεία του ορίζοντα."},
    "compare": {"icon": "⚖️", "title": "Ποιο είναι πιο...;", "rounds": 8,
                "desc": "Ποιο βουνό είναι πιο ψηλό; Ποιο ποτάμι πιο μακρύ; Μάντεψε!"},
    "memory": {"icon": "🃏", "title": "Παιχνίδι Μνήμης", "rounds": 6,
               "desc": "Γύρνα τις κάρτες και βρες τα ζευγάρια."},
    "voyage": {"icon": "🎈", "title": "Ταξίδι με Αερόστατο", "rounds": 5,
               "desc": "Λύσε τους γρίφους και πέτα από τόπο σε τόπο σε όλη την Ελλάδα."},
}

MEMORY_SETS = {
    "regions": ("⭐ Περιφέρειες και πρωτεύουσες", "⭐"),
    "eu": ("🤝 Χώρες της Ε.Ε. και πρωτεύουσες", "🤝"),
    "words": ("📖 Λέξεις της Γεωγραφίας", "📖"),
}

CORRECT_MSGS = ["Μπράβο σου!", "Τέλεια απάντηση!", "Φοβερό! Το ήξερες!", "Ναι! Έτσι μπράβο!",
                "Απίθανο! Συνέχισε έτσι!", "Σωστά! Είμαι πολύ περήφανη!"]
WRONG_MSGS = ["Δεν πειράζει, έτσι μαθαίνουμε!", "Σχεδόν! Τώρα το ξέρεις για την επόμενη φορά.",
              "Κανένα πρόβλημα! Και οι εξερευνητές χάνονται κάποτε.",
              "Μην ανησυχείς, θα το ξαναδούμε μαζί!"]

STATIC_BANK = {
    "maps_skills": gd.MAPS_SKILLS_QUESTIONS,
    "location_shape": gd.LOCATION_SHAPE_QUESTIONS,
    "climate": gd.CLIMATE_QUESTIONS,
    "flora_fauna": gd.FLORA_FAUNA_QUESTIONS,
    "disasters": gd.DISASTERS_QUESTIONS,
    "population": gd.POPULATION_QUESTIONS,
    "economy": gd.ECONOMY_QUESTIONS,
    "transport": gd.TRANSPORT_QUESTIONS,
    "eu": gd.EU_FACT_QUESTIONS,
    "cyprus": gd.CYPRUS_QUESTIONS,
    "coasts_seas": gd.SEAS_FACT_QUESTIONS,
    "diaspora": gd.DIASPORA_FACT_QUESTIONS,
}

TOPIC_MAP_CONFIG = {
    "location_shape": (gd.NEIGHBORS + gd.SEAS, [39.5, 23.0], 5, None),
    "coasts_seas": (gd.SEAS, [37.5, 23.5], 5, None),
    "islands": (gd.ISLANDS, [37.3, 24.5], 6, None),
    "mountains_plains": (gd.MOUNTAINS + gd.PLAINS, [39.5, 21.8], 6, "terrain"),
    "rivers_lakes": (gd.RIVERS + gd.LAKES, [39.5, 22.0], 6, None),
    "regions": (gd.REGIONS, [38.8, 22.5], 6, None),
    "cities": (gd.CITIES, [38.8, 22.5], 6, None),
    "eu": (gd.EU_COUNTRIES, [50, 15], 3, None),
    "cyprus": ([{"name": gd.CYPRUS["name"], "lat": gd.CYPRUS["lat"], "lon": gd.CYPRUS["lon"],
                 "fact": " · ".join(gd.CYPRUS["facts"][:2])}], [gd.CYPRUS["lat"], gd.CYPRUS["lon"]], 8, None),
    "diaspora": (gd.DIASPORA, [20, 10], 1, None),
}
GLOBE_TOPICS = {"eu", "diaspora"}

SPECIAL_QUIZZES = {
    "daily": {"icon": "🎯", "title": "Η Αποστολή της Ημέρας"},
    "review": {"icon": "🔁", "title": "Εξάσκηση στα Δύσκολα"},
}

GREECE_BOUNDS = [[34.8, 19.3], [41.8, 28.4]]
# Χάρτης με ανάγλυφο και χωρίς ονόματα, που δεν χρειάζεται κλειδί (φτάνει ως το επίπεδο 8).
NOLABEL_TILES = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}"
TILES_ATTR = "Tiles &copy; Esri &mdash; Source: US National Park Service"
NOLABEL_MAX_ZOOM = 8

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Comfortaa:wght@600;700&family=Manrope:wght@500;700;800&display=swap');
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp button { font-family: 'Manrope', 'Segoe UI', sans-serif; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { font-family: 'Comfortaa', 'Segoe UI', sans-serif; }
.stApp .stButton button { border-radius: 14px; min-height: 3rem; font-weight: 700; transition: transform .12s ease, box-shadow .12s ease; }
.stApp .stButton button p { font-size: 1.02rem; font-weight: 700; }
.stApp [data-testid="stSidebar"] .stButton button p { font-size: .92rem; }
.stApp .stButton button:hover:enabled { transform: translateY(-2px); box-shadow: 0 5px 12px rgba(30, 80, 120, .22); }
.stApp [data-testid="stBaseButton-primary"] { background: #0f8b8d; border-color: #0f8b8d; color: #fff; }
.stApp [data-testid="stBaseButton-primary"]:hover { background: #0b6f71; border-color: #0b6f71; color: #fff; }

.hero { background: linear-gradient(120deg, #0f8b8d, #1b6ca8); color: #fff; border-radius: 22px; padding: 22px 26px; margin-bottom: 14px; }
.hero h1 { color: #fff; padding: 0; margin: 0 0 4px; font-size: 1.95rem; }
.hero p { color: #e8f7f7; margin: 0; font-size: 1.05rem; }
.xp-row { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-top: 14px; font-weight: 800; }
.xp-track { background: rgba(255,255,255,.28); border-radius: 99px; height: 14px; overflow: hidden; margin-top: 6px; }
.xp-fill { background: #ffd166; height: 100%; border-radius: 99px; }

.owl-row { display: flex; align-items: flex-start; gap: 12px; margin: 8px 0 14px; }
.owl { font-size: 2.7rem; line-height: 1; animation: owl-bob 2.6s ease-in-out infinite; }
.bubble { position: relative; background: #fff8e1; color: #3d3524; border: 2px solid #ffd166; border-radius: 16px; padding: 11px 15px; font-size: 1.04rem; font-weight: 600; }
.bubble.good { background: #e6f8ec; border-color: #4cc27a; color: #17492b; animation: pop .3s ease-out; }
.bubble.oops { background: #fff0ea; border-color: #f4976c; color: #5e2c16; animation: pop .3s ease-out; }
@keyframes owl-bob { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }
@keyframes pop { 0% { transform: scale(.92); } 70% { transform: scale(1.03); } 100% { transform: scale(1); } }

.tile-icon { font-size: 2.5rem; line-height: 1.1; }
.tile-title { font-family: 'Comfortaa', 'Segoe UI', sans-serif; font-weight: 700; font-size: 1.1rem; margin: 2px 0; }
.tile-desc { font-size: .92rem; opacity: .82; min-height: 3.9em; }

.question { background: #eaf4fb; color: #16384f; border-left: 7px solid #1b6ca8; border-radius: 12px; padding: 14px 18px; font-size: 1.26rem; font-weight: 800; margin: 8px 0; }
.fact-card { background: #f3effc; color: #352a58; border: 2px solid #b9a7ec; border-radius: 18px; padding: 22px; min-height: 130px; font-size: 1.12rem; font-weight: 600; animation: pop .25s ease-out; }
.fact-card small { display: block; font-weight: 800; color: #6a4fc0; margin-bottom: 7px; }
.big-stars { text-align: center; font-size: 3.1rem; margin: 6px 0; animation: pop .45s ease-out; }
.badge-card { border-radius: 14px; padding: 12px 14px; margin-bottom: 10px; background: #fff4cc; color: #4b3b00; border: 2px solid #ffd166; font-weight: 800; }
.badge-card small { display: block; font-weight: 600; margin-top: 3px; }
.badge-card.locked { background: #eef0f2; color: #6a737b; border: 2px dashed #b7bec5; }
.value-card { text-align: center; border-radius: 16px; padding: 14px; font-size: 1.3rem; font-weight: 800; background: #eaf4fb; color: #16384f; animation: pop .3s ease-out; }
.value-card.win { background: #e6f8ec; color: #17492b; }
.compass-svg { display: block; margin: 0 auto; }
.compass-needle { transform-origin: 60px 60px; animation: needle 5s ease-in-out infinite; }
@keyframes needle { 0%, 100% { transform: rotate(-9deg); } 50% { transform: rotate(9deg); } }

[class*="st-key-sfx"] { position: absolute; width: 0; height: 0; overflow: hidden; opacity: 0; }
.st-key-memory-board .stButton button { min-height: 5.6rem; }
.st-key-memory-board .stButton button p { font-size: .94rem; }
.st-key-memory-board [data-testid="stHorizontalBlock"], .st-key-compass-rose [data-testid="stHorizontalBlock"] { flex-wrap: nowrap; gap: .4rem; }
.st-key-memory-board [data-testid="stColumn"], .st-key-compass-rose [data-testid="stColumn"] { min-width: 0; flex: 1 1 0; }
@media (prefers-reduced-motion: reduce) { .owl, .bubble, .compass-needle, .fact-card, .big-stars, .value-card { animation: none !important; } }
</style>
"""

COMPASS_SVG = """
<svg class="compass-svg" viewBox="0 0 120 120" width="150" height="150" role="img" aria-label="Πυξίδα">
<circle cx="60" cy="60" r="56" fill="#fff8e1" stroke="#c9972b" stroke-width="5"/>
<g font-family="sans-serif" font-weight="800" font-size="14" text-anchor="middle" fill="#3d3524">
<text x="60" y="22" fill="#c8102e">Β</text><text x="60" y="110">Ν</text><text x="104" y="65">Α</text><text x="16" y="65">Δ</text>
</g>
<g class="compass-needle"><polygon points="60,27 67,60 53,60" fill="#c8102e"/><polygon points="60,93 67,60 53,60" fill="#7c8791"/></g>
<circle cx="60" cy="60" r="5" fill="#3d3524"/>
</svg>
"""


# ═══════════════════════════ ΒΟΗΘΗΤΙΚΑ ═══════════════════════════

@st.cache_resource(show_spinner=False)
def get_client():
    try:
        from openai import OpenAI
        key = st.secrets.get("OPENAI_API_KEY")
        return OpenAI(api_key=key) if key else None
    except Exception:
        return None


@st.cache_resource(show_spinner=False)
def load_kb():
    try:
        with open(KB_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


@st.cache_data(show_spinner=False)
def text_to_speech(text):
    # Τα emoji μπερδεύουν τη φωνή, οπότε κρατάμε μόνο γράμματα και στίξη.
    clean = re.sub(r"[^\w\s,.;:!?«»'·%()\-–—]", "", text)
    tts = gTTS(text=clean, lang="el")
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    return buf.getvalue()


def speak(text):
    try:
        st.audio(text_to_speech(text), format="audio/mp3", autoplay=True)
    except Exception:
        st.warning("🔇 Η φωνή χρειάζεται σύνδεση στο ίντερνετ. Δοκίμασε ξανά σε λίγο!")


@st.cache_data(show_spinner=False)
def tone_wav(kind):
    notes = {"ok": [(523, .09), (659, .09), (784, .17)], "no": [(294, .14), (247, .23)],
             "win": [(523, .1), (659, .1), (784, .1), (1047, .32)], "flip": [(660, .05)]}[kind]
    rate = 22050
    frames = bytearray()
    for freq, dur in notes:
        total = int(rate * dur)
        for i in range(total):
            fade = min(1, i / 200, (total - i) / 400)  # χωρίς απότομα «κλικ» στην αρχή και στο τέλος
            frames += struct.pack("<h", int(9000 * fade * math.sin(2 * math.pi * freq * i / rate)))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))
    return buf.getvalue()


def play_sfx(kind):
    if st.session_state.get("sound_on", True):
        st.session_state.sfx = kind


def flush_sfx():
    kind = st.session_state.pop("sfx", None)
    if kind:
        st.session_state.sfx_n = st.session_state.get("sfx_n", 0) + 1
        with st.container(key=f"sfx_{st.session_state.sfx_n}"):
            st.audio(tone_wav(kind), format="audio/wav", autoplay=True)


def owl(text, tone=""):
    st.markdown(f'<div class="owl-row"><div class="owl">🦉</div>'
                f'<div class="bubble {tone}">{html.escape(text)}</div></div>', unsafe_allow_html=True)


def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def load_scores():
    d = load_json(SCORES_FILE)
    return d if isinstance(d, list) else []


def save_score(name, pts, topic_title):
    s = load_scores()
    s.append({"name": name, "points": pts, "topic": topic_title})
    s = sorted(s, key=lambda x: x["points"], reverse=True)[:10]
    save_json(SCORES_FILE, s)


def save_badge(name, badge_key):
    """Επιστρέφει True μόνο όταν το παράσημο κερδίζεται για πρώτη φορά."""
    d = load_json(BADGES_FILE)
    if not isinstance(d, dict):
        d = {}
    earned = set(d.get(name, []))
    if badge_key in earned:
        return False
    earned.add(badge_key)
    d[name] = sorted(earned)
    save_json(BADGES_FILE, d)
    return True


def get_badges(name):
    d = load_json(BADGES_FILE)
    return d.get(name, []) if isinstance(d, dict) else []


def load_profiles():
    d = load_json(PROFILES_FILE)
    return d if isinstance(d, dict) else {}


def get_profile(name=None):
    p = load_profiles().get(name or st.session_state.player_name, {})
    p.setdefault("avatar", "🦊")
    p.setdefault("xp", 0)
    p.setdefault("stars", {})
    p.setdefault("best", {})
    p.setdefault("mistakes", [])
    p.setdefault("daily", {"last": None, "streak": 0})
    return p


def save_profile(p):
    d = load_profiles()
    d[st.session_state.player_name] = p
    save_json(PROFILES_FILE, d)


def known_players():
    badges = load_json(BADGES_FILE)
    names = list(load_profiles())
    if isinstance(badges, dict):
        names += [n for n in badges if n not in names]
    return names


def level_info(xp):
    idx = max(i for i, lvl in enumerate(LEVELS) if xp >= lvl[0])
    start, icon, title = LEVELS[idx]
    if idx + 1 < len(LEVELS):
        nxt = LEVELS[idx + 1][0]
        return {"idx": idx, "icon": icon, "title": title, "next": nxt, "progress": (xp - start) / (nxt - start)}
    return {"idx": idx, "icon": icon, "title": title, "next": None, "progress": 1.0}


def unit_of_topic(topic_key):
    for u in gd.UNITS:
        if topic_key in u["topics"]:
            return u
    return gd.UNITS[0]


def opt_name(o):
    return o["name"] if isinstance(o, dict) else str(o)


def stars_for(ratio):
    if ratio >= 0.85:
        return 3
    if ratio >= 0.6:
        return 2
    return 1 if ratio >= 0.35 else 0


def stars_text(n):
    return "⭐" * n + "☆" * (3 - n)


# ═══════════════════════════ ΚΑΤΑΣΤΑΣΗ ═══════════════════════════

def init_state():
    st.session_state.setdefault("player_name", None)
    st.session_state.setdefault("voice_on", True)
    st.session_state.setdefault("sound_on", True)
    st.session_state.setdefault("easy_map", False)
    st.session_state.setdefault("ai_bonus_on", False)
    st.session_state.setdefault("n_questions", 6)
    st.session_state.setdefault("view", "home")   # home | explore | quiz | game | trophies
    st.session_state.setdefault("cur_topic", None)
    st.session_state.setdefault("cur_game", None)
    st.session_state.setdefault("g_playing", False)


def go_to(view):
    st.session_state.view = view
    st.rerun()


def shuffled_choice(q):
    """Ανακατεύει τις επιλογές, ώστε να μη μαθαίνεται η θέση της σωστής απάντησης."""
    if q.get("type", "choice") != "choice":
        return q
    order = list(range(len(q["opts"])))
    random.shuffle(order)
    return {**q, "opts": [q["opts"][i] for i in order], "correct": order.index(q["correct"])}


def _draw_from_bank(bank_orig, pool_holder):
    """Παίρνει το επόμενο στοιχείο από ανακατεμένη «πισίνα»· την ξαναγεμίζει όταν αδειάσει."""
    if not pool_holder:
        pool_holder.extend(bank_orig)
        random.shuffle(pool_holder)
    return shuffled_choice(pool_holder.pop())


def build_quiz(topic_key, n):
    map_fn = gd.MAP_QUESTION_FN.get(topic_key)
    bank_orig = list(STATIC_BANK.get(topic_key, []))
    pool = []
    qs = []
    used_names = set()  # avoids asking about the same correct entity twice in one quiz

    def draw_map():
        q = map_fn(exclude_names=used_names)
        used_names.add(q["opts"][q["correct"]]["name"])
        return q

    if map_fn and bank_orig:
        for i in range(n):
            qs.append(draw_map() if i % 2 == 0 else _draw_from_bank(bank_orig, pool))
    elif map_fn:
        qs = [draw_map() for _ in range(n)]
    else:
        qs = [_draw_from_bank(bank_orig, pool) for _ in range(n)]
    random.shuffle(qs)

    if st.session_state.ai_bonus_on and agents is not None:
        client = get_client()
        kb = load_kb()
        if client and kb.get("Γεωγραφία"):
            try:
                ai_q = agents.generate_one(client, kb, "Γεωγραφία")
                # Ο πράκτορας μπορεί να φτιάξει και άλλες μορφές ή μια εφεδρική ερώτηση χωρίς γεωγραφία.
                if ai_q.get("type") == "choice" and not ai_q["q"].startswith("Ποιο μάθημα παίζεις"):
                    ai_q["ai"] = True
                    qs[-1] = ai_q
            except Exception:
                pass
    return qs


def build_daily():
    """Ίδιες ερωτήσεις για όλη την ημέρα, από όλη την ύλη."""
    rng = random.Random(datetime.date.today().isoformat())
    topics = rng.sample(sorted(STATIC_BANK), 5)
    return [shuffled_choice(rng.choice(STATIC_BANK[t])) for t in topics]


def start_quiz(topic_key):
    if topic_key == "daily":
        queue = build_daily()
    elif topic_key == "review":
        queue = [shuffled_choice(q) for q in get_profile()["mistakes"][-8:]]
        random.shuffle(queue)
    else:
        queue = build_quiz(topic_key, st.session_state.n_questions)
    st.session_state.update(dict(
        cur_topic=topic_key, view="quiz",
        g_queue=queue, g_index=0, g_total=len(queue),
        g_points=0, g_streak=0, g_best_streak=0, g_lives=3, g_correct_count=0,
        g_has_lives=topic_key not in SPECIAL_QUIZZES,
        g_finished=False, g_playing=True, g_score_saved=False, g_eliminated=set(),
        hint_msg=None, last_result=None,
    ))
    load_next_question()


def load_next_question():
    idx = st.session_state.g_index
    queue = st.session_state.g_queue
    st.session_state.q = queue[idx] if idx < len(queue) else queue[-1]
    st.session_state.g_answered = False
    st.session_state.g_selected = None
    st.session_state.g_used_hint = False
    st.session_state.g_eliminated = set()
    st.session_state.g_last_gain = 0


def remember_mistake(q, is_correct):
    if q.get("ai"):
        return
    # Ένα λάθος σβήνεται μόνο όταν απαντηθεί σωστά μέσα στην εξάσκηση.
    if is_correct and st.session_state.cur_topic != "review":
        return
    p = get_profile()
    p["mistakes"] = [m for m in p["mistakes"] if m["q"] != q["q"]]
    if not is_correct:
        p["mistakes"] = (p["mistakes"] + [q])[-30:]
    save_profile(p)


def register(is_correct):
    st.session_state.g_answered = True
    if is_correct:
        st.session_state.g_streak += 1
        st.session_state.g_best_streak = max(st.session_state.g_best_streak, st.session_state.g_streak)
        gain = 10 + (5 if st.session_state.g_streak >= 3 else 0)
        if st.session_state.g_used_hint:
            gain = max(5, gain - 5)
        st.session_state.g_points += gain
        st.session_state.g_last_gain = gain
        st.session_state.g_correct_count += 1
        st.session_state.g_praise = random.choice(CORRECT_MSGS)
        play_sfx("ok")
    else:
        st.session_state.g_streak = 0
        if st.session_state.g_has_lives:
            st.session_state.g_lives -= 1
        st.session_state.g_last_gain = 0
        st.session_state.g_praise = random.choice(WRONG_MSGS)
        play_sfx("no")
    remember_mistake(st.session_state.q, is_correct)


def correct_display(q):
    if q.get("type") == "number_line":
        return f'{q["correct_value"]} {q.get("unit", "")}'.strip()
    return opt_name(q["opts"][q["correct"]])


def record_result(title, points, ratio, badge_keys=(), bonus_note=None):
    """Κρατά XP, ρεκόρ και παράσημα μία φορά στο τέλος κάθε παιχνιδιού και ετοιμάζει την οθόνη τέλους."""
    name = st.session_state.player_name
    p = get_profile()
    before = level_info(p["xp"])["idx"]
    p["xp"] += points
    save_profile(p)
    after = level_info(p["xp"])
    save_score(name, points, title)
    new_badges = [b for b in badge_keys if save_badge(name, b)]
    st.session_state.last_result = dict(
        stars=stars_for(ratio), points=points, new_badges=new_badges, bonus_note=bonus_note,
        level_up=after if after["idx"] > before else None,
    )
    play_sfx("win")
    if ratio >= 0.6 or new_badges:
        st.balloons()


def show_result():
    r = st.session_state.last_result
    st.markdown(f'<div class="big-stars">{stars_text(r["stars"])}</div>', unsafe_allow_html=True)
    if r["level_up"]:
        owl(f'Ανέβηκες επίπεδο! Τώρα ταξιδεύεις με: {r["level_up"]["icon"]} {r["level_up"]["title"]}!', "good")
    for b in r["new_badges"]:
        st.success(f"🏅 Νέο παράσημο: **{BADGES[b]}**!")
    if r["bonus_note"]:
        st.info(r["bonus_note"])


def game_nav(replay_label, replay_fn):
    b1, b2 = st.columns(2)
    if b1.button(replay_label, type="primary", width="stretch"):
        replay_fn()
        st.rerun()
    if b2.button("🏠 Στην αρχική", width="stretch"):
        go_to("home")


# ═══════════════════════════ FOLIUM ΧΑΡΤΕΣ ═══════════════════════════

def base_map(center, zoom, terrain=False, add_layer_control=True):
    m = folium.Map(location=center, zoom_start=zoom, tiles=None)
    folium.TileLayer("OpenStreetMap", name="🗺️ Κλασικός χάρτης").add_to(m)
    if terrain:
        folium.TileLayer(
            tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
            attr="OpenTopoMap", name="⛰️ Ανάγλυφο (ύψη)").add_to(m)
    folium_plugins.Fullscreen(position="topleft").add_to(m)
    folium_plugins.MiniMap(toggle_display=True).add_to(m)
    if add_layer_control:
        folium.LayerControl(collapsed=True).add_to(m)
    return m


def fit_to(m, points, max_zoom=None):
    """Ζουμάρει ώστε να φαίνονται όλα τα σημεία, όποιο κι αν είναι το μέγεθος της οθόνης."""
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding=(30, 30), max_zoom=max_zoom)


def game_map():
    """Χάρτης χωρίς ονόματα: εδώ η απάντηση δεν πρέπει να φαίνεται πάνω στο υπόβαθρο."""
    m = folium.Map(location=[38.3, 23.9], zoom_start=6, tiles=NOLABEL_TILES, attr=TILES_ATTR, max_zoom=NOLABEL_MAX_ZOOM)
    m.fit_bounds(GREECE_BOUNDS)
    return m


def emoji_marker(lat, lon, emoji, tooltip=None, permanent=False, popup=None, interactive=True):
    icon = folium.DivIcon(html=f'<div style="font-size:25px;line-height:30px;text-align:center;'
                               f'filter:drop-shadow(0 1px 2px rgba(0,0,0,.45))">{emoji}</div>',
                          icon_size=(30, 30), icon_anchor=(15, 15))
    return folium.Marker([lat, lon], icon=icon, popup=popup, interactive=interactive,
                         tooltip=folium.Tooltip(tooltip, permanent=permanent) if tooltip else None)


def explore_map(entities, center, zoom, emoji, terrain=False):
    m = base_map(center, zoom, terrain)
    for e in entities:
        popup_html = f"<b>{e['name']}</b><br>{e.get('fact', '')}"
        emoji_marker(e["lat"], e["lon"], emoji, tooltip=e["name"],
                     popup=folium.Popup(popup_html, max_width=250)).add_to(m)
    if len(entities) > 1:
        fit_to(m, [(e["lat"], e["lon"]) for e in entities], max_zoom=zoom)
    return m


def overview_map():
    m = base_map([38.8, 23.5], 6, terrain=True, add_layer_control=False)
    colors = {"regions": "red", "mountains": "darkgreen", "rivers": "cadetblue",
              "lakes": "blue", "islands": "orange", "seas": "purple"}
    for key, (label, entities) in gd.ALL_LAYERS.items():
        fg = folium.FeatureGroup(name=label, show=(key == "regions"))
        for e in entities:
            if key == "regions":
                folium.CircleMarker(
                    [e["lat"], e["lon"]], radius=max(6, min(22, e["pop_k"] / 200)),
                    color=colors[key], fill=True, fill_opacity=0.7,
                    tooltip=f"{e['capital']} ({e['name']})",
                    popup=folium.Popup(f"<b>⭐ {e['capital']}</b> — {e['name']}<br>"
                                        f"Πληθυσμός περιφέρειας: ~{e['pop_k']:,}χιλ.<br>{e['fact']}",
                                        max_width=260),
                ).add_to(fg)
            else:
                folium.Marker(
                    [e["lat"], e["lon"]], tooltip=e["name"],
                    popup=folium.Popup(f"<b>{e['name']}</b><br>{e.get('fact', '')}", max_width=250),
                    icon=folium.Icon(color=colors[key], icon="info-sign"),
                ).add_to(fg)
        fg.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m


def letter_marker(lat, lon, letter, color):
    icon = folium.DivIcon(html=f'<div style="width:32px;height:32px;line-height:28px;border-radius:50%;'
                               f'background:{color};color:#fff;border:2px solid #fff;text-align:center;'
                               f'font:800 16px sans-serif;box-shadow:0 1px 4px rgba(0,0,0,.5)">{letter}</div>',
                          icon_size=(32, 32), icon_anchor=(16, 16))
    return folium.Marker([lat, lon], icon=icon)


PIN_LETTERS = "ΑΒΓΔΕΖ"


def quiz_map(q, answered, sel, eliminated):
    easy = st.session_state.easy_map
    m = folium.Map(location=q["center"], zoom_start=q.get("zoom", 5), tiles=NOLABEL_TILES, attr=TILES_ATTR,
                   max_zoom=NOLABEL_MAX_ZOOM)
    fit_to(m, [(o["lat"], o["lon"]) for o in q["opts"]], max_zoom=q.get("zoom", 5))
    for i, o in enumerate(q["opts"]):
        if i in eliminated and not answered:
            continue
        color = "#1b6ca8"
        if answered:
            color = "#2e9e5b" if i == q["correct"] else ("#d1495b" if i == sel else "#7c8791")
        marker = letter_marker(o["lat"], o["lon"], PIN_LETTERS[i], color)
        # Το όνομα φαίνεται μόνο μετά την απάντηση, αλλιώς το ποντίκι αποκαλύπτει τη λύση.
        if answered or easy:
            folium.Tooltip(o["name"], permanent=answered).add_to(marker)
        marker.add_to(m)
    return m


def globe_figure(entities, highlight_idx=None):
    lats = [e["lat"] for e in entities]
    lons = [e["lon"] for e in entities]
    names = [e["name"] for e in entities]
    colors = ["crimson" if i == highlight_idx else "royalblue" for i in range(len(entities))]
    fig = go.Figure(go.Scattergeo(
        lat=lats, lon=lons, text=names, mode="markers+text",
        textposition="top center", textfont=dict(size=10),
        marker=dict(size=9, color=colors, line=dict(width=1, color="white")),
    ))
    fig.update_geos(
        projection_type="orthographic", showland=True, landcolor="rgb(235, 245, 230)",
        showocean=True, oceancolor="rgb(200, 230, 245)", showcountries=True,
        countrycolor="rgb(160,160,160)", showlakes=True, lakecolor="rgb(200,230,245)",
    )
    fig.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0))
    return fig


# ═══════════════════════════ ΣΕΛΙΔΑ: ΚΑΛΩΣΟΡΙΣΜΑ ═══════════════════════════

def enter_as(name):
    st.session_state.player_name = name
    st.session_state.view = "home"
    st.rerun()


def render_welcome():
    st.markdown('<div class="hero"><h1>🌍 Γεωγραφία Εξερευνητής</h1>'
                '<p>Ταξίδεψε σε όλη την Ελλάδα παίζοντας — με την ύλη της Ε\' Δημοτικού!</p></div>',
                unsafe_allow_html=True)
    owl("Γεια σου! Είμαι η Σοφούλα, η κουκουβάγια της Αθηνάς, και θα είμαι η ξεναγός σου. Πώς σε λένε;")

    players = known_players()
    if players:
        st.subheader("👋 Έχεις ξαναπαίξει;")
        cols = st.columns(min(len(players), 4))
        for i, name in enumerate(players):
            p = get_profile(name)
            if cols[i % len(cols)].button(f'{p["avatar"]} {name}', key=f"player_{i}", width="stretch"):
                enter_as(name)
        st.subheader("✨ Ή φτιάξε νέο εξερευνητή")

    name = st.text_input("Το όνομά σου", max_chars=20, placeholder="Γράψε το όνομά σου εδώ").strip()
    avatar = st.pills("Διάλεξε τον σύντροφό σου", AVATARS, default=AVATARS[0])
    if st.button("🚀 Πάμε στην περιπέτεια!", type="primary", width="stretch"):
        name = name or DEFAULT_PLAYER
        st.session_state.player_name = name
        p = get_profile(name)
        p["avatar"] = avatar or p["avatar"]
        save_profile(p)
        enter_as(name)


# ═══════════════════════════ ΣΕΛΙΔΑ: HOME ═══════════════════════════

def all_facts():
    return [f'{e["name"]}: {e["fact"]}' for _, entities in gd.ALL_LAYERS.values() for e in entities if e.get("fact")]


def render_hero(p):
    lvl = level_info(p["xp"])
    goal = f'{p["xp"]} / {lvl["next"]} XP' if lvl["next"] else f'{p["xp"]} XP · Ανώτατο επίπεδο!'
    streak = f' · 🔥 {p["daily"]["streak"]} μέρες στη σειρά' if p["daily"]["streak"] > 1 else ""
    st.markdown(
        f'<div class="hero"><h1>{p["avatar"]} Γεια σου, {html.escape(st.session_state.player_name)}!</h1>'
        f'<p>Πού θα ταξιδέψουμε σήμερα;</p>'
        f'<div class="xp-row"><span>{lvl["icon"]} Επίπεδο: {lvl["title"]}{streak}</span><span>{goal}</span></div>'
        f'<div class="xp-track"><div class="xp-fill" style="width:{lvl["progress"] * 100:.0f}%"></div></div></div>',
        unsafe_allow_html=True)


def render_home():
    p = get_profile()
    render_hero(p)
    facts = all_facts()
    today_fact = random.Random(datetime.date.today().isoformat()).choice(facts)
    owl(f"Ήξερες ότι... {today_fact}")

    today = datetime.date.today().isoformat()
    done_today = p["daily"]["last"] == today
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown('<div class="tile-title">🎯 Η Αποστολή της Ημέρας</div>', unsafe_allow_html=True)
            st.caption("✅ Την έκανες σήμερα! Ξαναπαίξε για εξάσκηση." if done_today
                       else "5 ερωτήσεις από όλη την ύλη, χωρίς ζωές. Μπόνους +30 XP!")
            if st.button("Ξεκίνα την αποστολή", key="start_daily", type="primary", width="stretch"):
                start_quiz("daily")
                st.rerun()
    with c2:
        with st.container(border=True):
            n = len(p["mistakes"])
            st.markdown('<div class="tile-title">🔁 Εξάσκηση στα Δύσκολα</div>', unsafe_allow_html=True)
            st.caption(f"Έχεις {n} ερωτήσεις για να τις ξαναδείς. Χωρίς ζωές, χωρίς άγχος!" if n
                       else "Κανένα λάθος για διόρθωση. Μπράβο σου!")
            if st.button("Ξαναδές τες", key="start_review", disabled=not n, width="stretch"):
                start_quiz("review")
                st.rerun()

    st.subheader("🎮 Παιχνίδια")
    keys = list(GAMES)
    for row_start in range(0, len(keys), 3):
        cols = st.columns(3)
        for col, key in zip(cols, keys[row_start:row_start + 3]):
            g = GAMES[key]
            with col:
                with st.container(border=True):
                    best = p["best"].get(key)
                    st.markdown(f'<div class="tile-icon">{g["icon"]}</div><div class="tile-title">{g["title"]}</div>'
                                f'<div class="tile-desc">{g["desc"]}</div>', unsafe_allow_html=True)
                    st.caption(f"🏅 Ρεκόρ: {best} πόντοι" if best is not None else "✨ Δεν το έχεις παίξει ακόμα")
                    if st.button("Παίξε", key=f"play_{key}", width="stretch"):
                        start_game(key)
                        st.rerun()

    st.subheader("📚 Η ύλη του βιβλίου")
    tabs = st.tabs([f"{u['icon']} {u['title']}" for u in gd.UNITS])
    for tab, u in zip(tabs, gd.UNITS):
        with tab:
            st.caption(u["sub"])
            cols = st.columns(3)
            for i, topic_key in enumerate(u["topics"]):
                meta = gd.TOPIC_META[topic_key]
                stars = stars_text(p["stars"].get(topic_key, 0))
                if cols[i % 3].button(f"{meta['icon']} {meta['title']}  \n{stars}",
                                      key=f"home_topic_{topic_key}", width="stretch"):
                    st.session_state.cur_topic = topic_key
                    go_to("explore")

    st.subheader("🗺️ Ο μεγάλος χάρτης")
    st.caption("🖱️ Κάνε κλικ σε ένα σημείο για να μάθεις κάτι νέο, και άναψε ή σβήσε ό,τι θέλεις από το μενού του χάρτη.")
    st_folium(overview_map(), width=None, height=480, key="home_map", returned_objects=[], use_container_width=True)


# ═══════════════════════════ ΣΕΛΙΔΑ: EXPLORE ═══════════════════════════

def topic_facts(topic_key):
    facts = []
    if topic_key == "cyprus":
        facts += gd.CYPRUS["facts"]
    elif topic_key in TOPIC_MAP_CONFIG:
        facts += [f'{e["name"]}: {e["fact"]}' for e in TOPIC_MAP_CONFIG[topic_key][0] if e.get("fact")]
    facts += [q["fact"] for q in STATIC_BANK.get(topic_key, []) if q.get("fact")]
    return list(dict.fromkeys(facts))


def render_fact_cards(topic_key):
    facts = topic_facts(topic_key)
    if not facts:
        return
    st.subheader("💡 Κάρτες γνώσης")
    key = f"fc_{topic_key}"
    idx = st.session_state.get(key, 0) % len(facts)
    st.markdown(f'<div class="fact-card"><small>Κάρτα {idx + 1} από {len(facts)}</small>'
                f'{html.escape(facts[idx])}</div>', unsafe_allow_html=True)
    st.write("")
    c1, c2, c3 = st.columns(3)
    if c1.button("⬅️ Προηγούμενη", key=f"{key}_prev", width="stretch"):
        st.session_state[key] = idx - 1
        st.rerun()
    if st.session_state.voice_on and c2.button("🔊 Διάβασέ τη", key=f"{key}_say", width="stretch"):
        speak(facts[idx])
    if c3.button("Επόμενη ➡️", key=f"{key}_next", width="stretch"):
        st.session_state[key] = idx + 1
        st.rerun()


def render_scale_lab():
    st.subheader("📏 Το εργαστήριο της κλίμακας")
    owl("Διάλεξε κλίμακα και εκατοστά πάνω στον χάρτη, και θα σου δείξω πόσο μακριά είναι στην πραγματικότητα!")
    c1, c2, c3 = st.columns([2, 2, 1])
    scale = c1.selectbox("Κλίμακα χάρτη", [100_000, 500_000, 1_000_000, 5_000_000], index=2,
                         format_func=lambda s: f"1:{s:,}".replace(",", "."))
    cm = c2.slider("Εκατοστά στον χάρτη", 1, 20, 5)
    km = cm * scale / 100_000
    c3.metric("Πραγματικά", f"{km:g} χλμ.")
    st.caption(f"{cm} εκ. × {scale:,} = {cm * scale:,} εκ. = {km:g} χλμ.".replace(",", "."))


def render_explore(topic_key):
    meta = gd.TOPIC_META[topic_key]
    st.title(f"{meta['icon']} {meta['title']}")
    st.caption(f"📖 {meta['chapters']} · Από το σχολικό βιβλίο Γεωγραφίας")
    owl(meta["intro"])
    if st.session_state.voice_on and st.button("🔊 Διάβασέ το"):
        speak(meta["intro"])

    if topic_key == "maps_skills":
        c1, c2 = st.columns([1, 2], vertical_alignment="center")
        with c1:
            st.html(COMPASS_SVG)
        with c2:
            st.markdown("**Η κόκκινη βελόνα δείχνει πάντα τον Βορρά!**  \n"
                        "Αν κοιτάς Βορρά, έχεις την Ανατολή στα δεξιά σου, τη Δύση στα αριστερά και τον Νότο πίσω σου.")
        render_scale_lab()

    if topic_key in TOPIC_MAP_CONFIG:
        entities, center, zoom, terrain_flag = TOPIC_MAP_CONFIG[topic_key]
        st.caption("🖱️ Κάνε κλικ σε ένα σημείο του χάρτη για να δεις πληροφορίες!")
        st_folium(explore_map(entities, center, zoom, meta["icon"], terrain=(terrain_flag == "terrain")),
                   width=None, height=440, key=f"explore_{topic_key}", returned_objects=[], use_container_width=True)
        if topic_key in GLOBE_TOPICS:
            with st.expander("🌐 Δες το σε 3D Υδρόγειο! (σύρε για να το γυρίσεις)"):
                st.plotly_chart(globe_figure(entities), width="stretch", key=f"globe_{topic_key}")

    render_fact_cards(topic_key)

    st.write("")
    b1, b2 = st.columns(2)
    if b1.button("🎯 Παίξε κουίζ σ' αυτό το θέμα!", type="primary", width="stretch"):
        start_quiz(topic_key)
        st.rerun()
    if b2.button("⬅️ Πίσω στην αρχική", width="stretch"):
        go_to("home")


# ═══════════════════════════ ΣΕΛΙΔΑ: QUIZ ═══════════════════════════

def r_choice(q, answered, sel, eliminated):
    for i, o in enumerate(q["opts"]):
        if i in eliminated and not answered:
            continue
        lbl = opt_name(o)
        if answered:
            if i == q["correct"]:
                lbl = f"✅ {lbl}"
            elif i == sel:
                lbl = f"❌ {lbl}"
        if st.button(lbl, key=f"opt_{st.session_state.g_index}_{i}", disabled=answered, width="stretch"):
            st.session_state.g_selected = i
            register(i == q["correct"])
            st.rerun()


def r_number(q, answered):
    lo, hi, step = float(q["min"]), float(q["max"]), float(q.get("step", 1))
    tol = q.get("tolerance", 0)
    unit = q.get("unit", "")
    # Ξεκινά από το ελάχιστο: η μέση της κλίμακας μπορεί να συμπίπτει με τη σωστή απάντηση.
    guess = st.slider("Σύρε στον σωστό αριθμό:", lo, hi, lo, step,
                       disabled=answered, key=f"nl_{st.session_state.g_index}")
    shown = int(guess) if float(guess).is_integer() else round(guess, 2)
    st.markdown(f"<h2 style='text-align:center'>{shown} {unit}</h2>", unsafe_allow_html=True)
    if not answered and st.button("✅ Απάντησε", type="primary", width="stretch"):
        st.session_state.g_selected = 0
        register(abs(guess - q["correct_value"]) <= tol)
        st.rerun()


def r_map(q, answered, sel, eliminated):
    st.caption("🖱️ Κάνε κλικ στη σωστή πινέζα του χάρτη, ή στο γράμμα της από κάτω.")
    idx = st.session_state.g_index
    if answered:
        st_folium(quiz_map(q, answered, sel, eliminated), width=None, height=400,
                   key=f"map_{idx}_done", returned_objects=[], use_container_width=True)
    else:
        out = st_folium(quiz_map(q, answered, sel, eliminated), width=None, height=400,
                         key=f"map_{idx}_{len(eliminated)}", returned_objects=["last_object_clicked"],
                         use_container_width=True)
        if out and out.get("last_object_clicked"):
            c = out["last_object_clicked"]
            candidates = [i for i in range(len(q["opts"])) if i not in eliminated]
            _, near = min(((q["opts"][i]["lat"] - c["lat"]) ** 2 + (q["opts"][i]["lon"] - c["lng"]) ** 2, i)
                          for i in candidates)
            st.session_state.g_selected = near
            register(near == q["correct"])
            st.rerun()
    cc = st.columns(len(q["opts"]))
    for i, o in enumerate(q["opts"]):
        if i in eliminated and not answered:
            continue
        lbl = f"📍 {PIN_LETTERS[i]}"
        if answered:
            mark = "✅" if i == q["correct"] else ("❌" if i == sel else PIN_LETTERS[i])
            lbl = f"{mark} {o['name']}"
        if cc[i].button(lbl, key=f"mopt_{idx}_{i}", disabled=answered, width="stretch"):
            st.session_state.g_selected = i
            register(i == q["correct"])
            st.rerun()


def finish_daily(p):
    """Μετρά το σερί ημερών και δίνει το μπόνους μία φορά τη μέρα. Επιστρέφει το μήνυμα ή None."""
    today = datetime.date.today()
    last = p["daily"]["last"]
    if last == today.isoformat():
        return None
    yesterday = (today - datetime.timedelta(days=1)).isoformat()
    p["daily"] = {"last": today.isoformat(), "streak": p["daily"]["streak"] + 1 if last == yesterday else 1}
    p["xp"] += 30
    save_profile(p)
    return f'🎁 Μπόνους αποστολής +30 XP · 🔥 {p["daily"]["streak"]} μέρες στη σειρά!'


def save_quiz_result(topic_key, title):
    correct, total = st.session_state.g_correct_count, st.session_state.g_total
    ratio = correct / total if total else 0
    p = get_profile()
    badges = []
    note = None
    if topic_key == "daily":
        note = finish_daily(p)
        p = get_profile()
        if p["daily"]["streak"] >= 3:
            badges.append("daily3")
    elif topic_key == "review":
        if not p["mistakes"]:
            badges.append("review")
    else:
        p["stars"][topic_key] = max(p["stars"].get(topic_key, 0), stars_for(ratio))
        save_profile(p)
        if ratio >= 0.7:
            badges.append(unit_of_topic(topic_key)["key"])
        if correct == total:
            badges.append("perfect")
    if st.session_state.g_best_streak >= 5:
        badges.append("streak5")
    record_result(title, st.session_state.g_points, ratio, badges, note)


def render_finish(topic_key):
    meta = quiz_meta(topic_key)
    total = st.session_state.g_total
    if not st.session_state.g_score_saved:
        save_quiz_result(topic_key, meta["title"])
        st.session_state.g_score_saved = True

    ran_out = st.session_state.g_has_lives and st.session_state.g_lives <= 0
    stars = st.session_state.last_result["stars"]
    if ran_out:
        owl("Τελείωσαν οι ζωές, αλλά έμαθες νέα πράγματα! Τα λάθη σου σε περιμένουν στην «Εξάσκηση στα Δύσκολα».", "oops")
    else:
        owl(["Κάθε εξερευνητής ξεκινά κάπως! Πάμε ξανά μαζί;", "Καλή προσπάθεια! Με λίγη εξάσκηση θα τα καταφέρεις ακόμα καλύτερα.",
             "Πολύ καλά! Είσαι πολύ κοντά στα 3 αστέρια!", "Καταπληκτικό! Ξέρεις αυτό το θέμα απ' έξω!"][stars], "good")
    show_result()
    c1, c2, c3 = st.columns(3)
    c1.metric("🏅 Πόντοι", st.session_state.g_points)
    c2.metric("✅ Σωστές", f"{st.session_state.g_correct_count}/{total}")
    c3.metric("🔥 Καλύτερο σερί", st.session_state.g_best_streak)

    b1, b2 = st.columns(2)
    has_review = bool(get_profile()["mistakes"])
    if topic_key != "review" or has_review:
        if b1.button("🔄 Ξαναπαίξε", type="primary", width="stretch"):
            start_quiz(topic_key)
            st.rerun()
    if topic_key in gd.TOPIC_META and b2.button("🗺️ Εξερεύνησε ξανά το θέμα", width="stretch"):
        go_to("explore")
    if st.button("🏠 Στην αρχική", width="stretch"):
        go_to("home")


def quiz_meta(topic_key):
    return SPECIAL_QUIZZES.get(topic_key) or gd.TOPIC_META.get(topic_key, {"title": topic_key, "icon": "🎯"})


def render_quiz(topic_key):
    meta = quiz_meta(topic_key)
    if st.session_state.g_finished:
        st.title(f"{meta['icon']} {meta['title']} — Τέλος!")
        render_finish(topic_key)
        return

    q = st.session_state.q
    answered = st.session_state.g_answered
    sel = st.session_state.g_selected
    eliminated = st.session_state.g_eliminated
    total = st.session_state.g_total

    t1, t2, t3 = st.columns(3)
    if st.session_state.g_has_lives:
        t1.markdown("**" + "❤️" * st.session_state.g_lives + "🤍" * (3 - st.session_state.g_lives) + "**")
    else:
        t1.markdown("**🕊️ Χωρίς ζωές, χωρίς άγχος**")
    t2.markdown(f"🏅 **{st.session_state.g_points}** π.")
    t3.markdown(f"🔥 **{st.session_state.g_streak}**")
    st.progress(st.session_state.g_index / total,
                text=f"{meta['icon']} {meta['title']} · Ερώτηση {st.session_state.g_index + 1}/{total}")

    if q.get("ai"):
        st.caption("🤖 Ζωντανή ερώτηση-μπόνους, φτιαγμένη από τον πράκτορα με βάση το πραγματικό βιβλίο!")
    st.markdown(f'<div class="question">{html.escape(q["q"])}</div>', unsafe_allow_html=True)

    if st.session_state.voice_on and st.button("🔊 Διάβασέ μου την ερώτηση"):
        speak(q["q"])
    st.write("")

    qtype = q.get("type", "choice")
    if qtype == "map":
        r_map(q, answered, sel, eliminated)
    elif qtype == "number_line":
        r_number(q, answered)
    else:
        r_choice(q, answered, sel, eliminated)

    if not answered:
        st.write("")
        can_hint = qtype in ("choice", "map") and len(eliminated) < len(q["opts"]) - 2
        if st.button("🤔 Σοφούλα, βοήθεια! (−5 πόντοι)", width="stretch", disabled=not can_hint and qtype != "number_line"):
            st.session_state.g_used_hint = True
            if qtype == "number_line":
                st.session_state.hint_msg = "Θυμήσου: πραγματική απόσταση = απόσταση στον χάρτη × κλίμακα (ή αντίστροφα, για να βρεις την απόσταση πάνω στον χάρτη)."
            else:
                wrong = [i for i in range(len(q["opts"])) if i != q["correct"] and i not in eliminated]
                if wrong:
                    eliminated.add(random.choice(wrong))
                    st.session_state.g_eliminated = eliminated
                st.session_state.hint_msg = "Έκρυψα μία λανθασμένη επιλογή. Τώρα είναι πιο εύκολο!"
            st.rerun()
        if st.session_state.get("hint_msg") and st.session_state.g_used_hint:
            owl(st.session_state.hint_msg)

    if answered:
        cd = correct_display(q)
        if st.session_state.g_last_gain > 0:
            bonus = " Σερί μπόνους +5! 🔥" if st.session_state.g_last_gain > 10 else ""
            owl(f"{st.session_state.g_praise} +{st.session_state.g_last_gain} πόντοι.{bonus}", "good")
        else:
            owl(f"{st.session_state.g_praise} Η σωστή απάντηση είναι: {cd}.", "oops")
        fact = q.get("fact")
        if fact:
            st.info(f"📖 {fact}")
        if st.button("Επόμενη ερώτηση →", type="primary", width="stretch"):
            st.session_state.g_index += 1
            st.session_state.hint_msg = None
            if st.session_state.g_index >= total or (st.session_state.g_has_lives and st.session_state.g_lives <= 0):
                st.session_state.g_finished = True
            else:
                load_next_question()
            st.rerun()


# ═══════════════════════════ ΠΑΙΧΝΙΔΙΑ ═══════════════════════════

def start_game(key):
    state = dict(view="game", cur_game=key, a_i=0, a_score=0, a_correct=0, a_done=False,
                 a_saved=False, a_answered=False, a_sel=None, last_result=None)
    if key == "find":
        state.update(f_targets=gd.find_targets(GAMES[key]["rounds"]), f_guesses=[], f_msg=None, f_hit=False)
    elif key == "compass":
        state.update(a_items=gd.compass_rounds(GAMES[key]["rounds"]))
    elif key == "compare":
        state.update(a_items=gd.compare_rounds(GAMES[key]["rounds"]))
    elif key == "memory":
        state.update(m_set=None, m_cards=[], m_open=[], m_found=[], m_moves=0)
    elif key == "voyage":
        state.update(a_items=gd.voyage_stops(GAMES[key]["rounds"]), v_out=[],
                     v_path=[[gd.VOYAGE_START["lat"], gd.VOYAGE_START["lon"]]])
    st.session_state.update(state)


def game_header(game, rounds_done, total):
    st.title(f'{game["icon"]} {game["title"]}')
    st.progress(min(rounds_done / total, 1.0), text=f"Γύρος {min(rounds_done + 1, total)}/{total} · 🏅 {st.session_state.a_score} πόντοι")


def next_round(total):
    st.session_state.a_i += 1
    st.session_state.a_answered = False
    st.session_state.a_sel = None
    if st.session_state.a_i >= total:
        st.session_state.a_done = True
    st.rerun()


def render_game_end(key, max_score, detail, badge_threshold=0.7):
    game = GAMES[key]
    score = st.session_state.a_score
    ratio = score / max_score if max_score else 0
    st.title(f'{game["icon"]} {game["title"]} — Τέλος!')
    if not st.session_state.a_saved:
        p = get_profile()
        p["best"][key] = max(p["best"].get(key, 0), score)
        save_profile(p)
        record_result(game["title"], score, ratio, [key] if ratio >= badge_threshold else [])
        st.session_state.a_saved = True
    r = st.session_state.last_result
    owl(["Έκανες την αρχή, και αυτό μετράει! Πάμε άλλη μία;", "Ωραία προσπάθεια! Κάθε φορά θα θυμάσαι περισσότερα.",
         "Πολύ καλά! Λίγο ακόμα και πιάνεις τα 3 αστέρια!", "Απίστευτο! Τα ξέρεις όλα σαν αληθινός χαρτογράφος!"][r["stars"]], "good")
    show_result()
    c1, c2 = st.columns(2)
    c1.metric("🏅 Πόντοι", score)
    c2.metric(*detail)
    game_nav("🔄 Ξαναπαίξε", lambda: start_game(key))


# ─────────── Ζεστά-Κρύα ───────────

def heat_word(km):
    if km <= 60:
        return "🔥 Καίγεσαι!"
    if km <= 150:
        return "☀️ Ζεστά!"
    if km <= 300:
        return "🌤️ Χλιαρά."
    return "❄️ Κρύο!"


def render_find():
    game = GAMES["find"]
    targets = st.session_state.f_targets
    total = len(targets)
    max_tries = 3
    if st.session_state.a_done:
        render_game_end("find", total * 20, ("🎯 Βρέθηκαν", f"{st.session_state.a_correct}/{total}"))
        return

    game_header(game, st.session_state.a_i, total)
    t = targets[st.session_state.a_i]
    emoji, article = gd.KIND_LABEL[t["kind"]]
    st.markdown(f'<div class="question">{emoji} Βρες {article}: {html.escape(t["name"])}</div>', unsafe_allow_html=True)
    guesses = st.session_state.f_guesses
    answered = st.session_state.a_answered

    m = game_map()
    for g in guesses:
        # Το ❌ αφήνει το κλικ να περάσει στον χάρτη, για να μπορεί το παιδί να ξαναδοκιμάσει κοντά του.
        emoji_marker(g[0], g[1], "❌", interactive=False).add_to(m)
    if answered:
        if guesses:
            folium.PolyLine([guesses[-1], [t["lat"], t["lon"]]], color="#d1495b", dash_array="6", weight=3).add_to(m)
        emoji_marker(t["lat"], t["lon"], "🎯", tooltip=t["name"], permanent=True).add_to(m)

    if st.session_state.f_msg:
        msg, tone = st.session_state.f_msg
        owl(msg, tone)
    else:
        owl(f"Κάνε κλικ στον χάρτη! Έχεις {max_tries} προσπάθειες, και θα σου λέω προς τα πού να ψάξεις.")

    if answered:
        st_folium(m, width=None, height=470, key=f"find_{st.session_state.a_i}_done",
                  returned_objects=[], use_container_width=True)
        if t.get("fact"):
            st.info(f"📖 {t['fact']}")
        if st.button("Επόμενος τόπος →", type="primary", width="stretch"):
            st.session_state.f_guesses = []
            st.session_state.f_msg = None
            next_round(total)
        return

    out = st_folium(m, width=None, height=470, key=f"find_{st.session_state.a_i}_{len(guesses)}",
                    returned_objects=["last_clicked"], use_container_width=True)
    click = out.get("last_clicked") if out else None
    if click:
        lat, lon = click["lat"], ((click["lng"] + 180) % 360) - 180
        guesses.append([lat, lon])
        radius = gd.BIG_TARGET_RADIUS_KM.get(t["name"], gd.FIND_RADIUS_KM)
        km = max(0, gd.distance_km(lat, lon, t["lat"], t["lon"]) - radius)
        if km == 0:
            pts = {1: 20, 2: 12, 3: 6}[len(guesses)]
            st.session_state.a_score += pts
            st.session_state.a_correct += 1
            st.session_state.a_answered = True
            st.session_state.f_msg = (f"{random.choice(CORRECT_MSGS)} Το βρήκες! +{pts} πόντοι.", "good")
            play_sfx("ok")
        elif len(guesses) >= max_tries:
            st.session_state.a_answered = True
            st.session_state.f_msg = (f"Ήσουν περίπου {round(km + radius)} χλμ. μακριά. Δες πού βρίσκεται, για την επόμενη φορά!", "oops")
            play_sfx("no")
        else:
            word = gd.DIRECTION_WORDS[gd.direction_name(lat, lon, t["lat"], t["lon"])]
            st.session_state.f_msg = (f"{heat_word(km)} Ψάξε πιο {word}. Σου μένουν {max_tries - len(guesses)} προσπάθειες.", "")
            play_sfx("flip")
        st.rerun()


# ─────────── Κυνήγι Πυξίδας ───────────

def render_compass():
    game = GAMES["compass"]
    items = st.session_state.a_items
    total = len(items)
    if st.session_state.a_done:
        render_game_end("compass", total * 10, ("✅ Σωστές", f"{st.session_state.a_correct}/{total}"))
        return

    game_header(game, st.session_state.a_i, total)
    r = items[st.session_state.a_i]
    a, b = r["start"], r["target"]
    answered = st.session_state.a_answered
    st.markdown(f'<div class="question">🧭 Είσαι στο σημείο «{html.escape(a["name"])}». Προς τα πού θα πας για «{html.escape(b["name"])}»;</div>',
                unsafe_allow_html=True)

    left, right = st.columns([3, 2])
    with left:
        m = game_map()
        emoji_marker(a["lat"], a["lon"], "🚩", tooltip=a["name"], permanent=True).add_to(m)
        emoji_marker(b["lat"], b["lon"], "📍", tooltip=b["name"], permanent=True).add_to(m)
        if answered:
            folium.PolyLine([[a["lat"], a["lon"]], [b["lat"], b["lon"]]], color="#0f8b8d", weight=4).add_to(m)
        st_folium(m, width=None, height=450, key=f"compass_{st.session_state.a_i}_{answered}",
                  returned_objects=[], use_container_width=True)
    with right:
        st.caption("⬆️ Στον χάρτη, ο Βορράς είναι πάντα προς τα πάνω.")
        with st.container(key="compass-rose"):
            for row in (["ΒΔ", "Β", "ΒΑ"], ["Δ", None, "Α"], ["ΝΔ", "Ν", "ΝΑ"]):
                cols = st.columns(3)
                for col, d in zip(cols, row):
                    if d is None:
                        col.markdown("<div style='text-align:center;font-size:2rem'>🧭</div>", unsafe_allow_html=True)
                        continue
                    lbl = d
                    if answered:
                        lbl = f"✅ {d}" if d == r["dir"] else (f"❌ {d}" if d == st.session_state.a_sel else d)
                    if col.button(lbl, key=f"dir_{st.session_state.a_i}_{d}", disabled=answered, width="stretch"):
                        st.session_state.a_answered = True
                        st.session_state.a_sel = d
                        if d == r["dir"]:
                            st.session_state.a_score += 10
                            st.session_state.a_correct += 1
                            play_sfx("ok")
                        else:
                            play_sfx("no")
                        st.rerun()

    if answered:
        word = gd.DIRECTION_WORDS[r["dir"]]
        text = f'Για να πας εκεί ταξιδεύεις {word} ({r["dir"]}), περίπου {r["km"]} χλμ. σε ευθεία γραμμή.'
        if st.session_state.a_sel == r["dir"]:
            owl(f"{random.Random(st.session_state.a_i).choice(CORRECT_MSGS)} {text}", "good")
        else:
            owl(f"Σχεδόν! {text}", "oops")
        if st.button("Επόμενο →", type="primary", width="stretch"):
            next_round(total)


# ─────────── Ποιο είναι πιο...; ───────────

def render_compare():
    game = GAMES["compare"]
    items = st.session_state.a_items
    total = len(items)
    if st.session_state.a_done:
        render_game_end("compare", total * 10, ("✅ Σωστές", f"{st.session_state.a_correct}/{total}"))
        return

    game_header(game, st.session_state.a_i, total)
    r = items[st.session_state.a_i]
    field, unit = r["field"], r["unit"]
    winner = 0 if r["a"][field] > r["b"][field] else 1
    answered = st.session_state.a_answered
    st.markdown(f'<div class="question">{html.escape(r["q"])}</div>', unsafe_allow_html=True)
    st.write("")

    cols = st.columns(2)
    for i, (col, e) in enumerate(zip(cols, (r["a"], r["b"]))):
        with col:
            lbl = e["name"]
            if answered:
                lbl = f"✅ {lbl}" if i == winner else (f"❌ {lbl}" if i == st.session_state.a_sel else lbl)
            if st.button(lbl, key=f"cmp_{st.session_state.a_i}_{i}", disabled=answered, width="stretch"):
                st.session_state.a_answered = True
                st.session_state.a_sel = i
                if i == winner:
                    st.session_state.a_score += 10
                    st.session_state.a_correct += 1
                    play_sfx("ok")
                else:
                    play_sfx("no")
                st.rerun()
            if answered:
                value = f"{e[field]:,}".replace(",", ".")
                cls = "value-card win" if i == winner else "value-card"
                st.markdown(f'<div class="{cls}">{value} {unit}</div>', unsafe_allow_html=True)

    if answered:
        st.write("")
        win = (r["a"], r["b"])[winner]
        if st.session_state.a_sel == winner:
            owl(random.Random(st.session_state.a_i).choice(CORRECT_MSGS), "good")
        else:
            owl(f'Νικητής είναι: {win["name"]}. Τώρα το ξέρεις!', "oops")
        if win.get("fact"):
            st.info(f"📖 {win['fact']}")
        if st.button("Επόμενο →", type="primary", width="stretch"):
            next_round(total)


# ─────────── Παιχνίδι Μνήμης ───────────

def memory_score(moves, pairs):
    return max(20, 100 - max(0, moves - pairs) * 6)


def start_memory_set(set_key):
    pairs = gd.memory_pairs(set_key, GAMES["memory"]["rounds"])
    cards = [{"pair": i, "text": t} for i, pair in enumerate(pairs) for t in pair]
    random.shuffle(cards)
    st.session_state.update(m_set=set_key, m_cards=cards, m_open=[], m_found=[], m_moves=0)


def memory_click(i):
    cards = st.session_state.m_cards
    opened = st.session_state.m_open
    if len(opened) == 2:  # το προηγούμενο λάθος ζευγάρι κλείνει με το επόμενο κλικ
        opened.clear()
    if i in opened or i in st.session_state.m_found:
        return
    opened.append(i)
    if len(opened) < 2:
        play_sfx("flip")
        return
    st.session_state.m_moves += 1
    a, b = opened
    if cards[a]["pair"] == cards[b]["pair"]:
        st.session_state.m_found += [a, b]
        opened.clear()
        play_sfx("ok")
        if len(st.session_state.m_found) == len(cards):
            st.session_state.a_score = memory_score(st.session_state.m_moves, len(cards) // 2)
            st.session_state.a_done = True
    else:
        play_sfx("no")


def render_memory():
    game = GAMES["memory"]
    if st.session_state.a_done:
        pairs = len(st.session_state.m_cards) // 2
        # Μέχρι 5 άστοχες κινήσεις δίνουν το παράσημο (70 πόντοι).
        render_game_end("memory", 100, ("🃏 Κινήσεις", f"{st.session_state.m_moves} (για {pairs} ζευγάρια)"))
        return

    st.title(f'{game["icon"]} {game["title"]}')
    if not st.session_state.m_set:
        owl("Τι θα ήθελες να θυμηθούμε σήμερα; Διάλεξε τις κάρτες σου!")
        cols = st.columns(len(MEMORY_SETS))
        for col, (key, (label, _)) in zip(cols, MEMORY_SETS.items()):
            if col.button(label, key=f"set_{key}", width="stretch"):
                start_memory_set(key)
                st.rerun()
        return

    cards = st.session_state.m_cards
    opened = st.session_state.m_open
    found = st.session_state.m_found
    back = MEMORY_SETS[st.session_state.m_set][1]
    st.progress(len(found) / len(cards), text=f"Βρέθηκαν {len(found) // 2}/{len(cards) // 2} ζευγάρια · 🃏 Κινήσεις: {st.session_state.m_moves}")
    if len(opened) == 2:
        owl("Δεν ταιριάζουν! Θυμήσου πού είναι, και κάνε κλικ σε άλλη κάρτα.", "oops")
    elif found:
        owl("Βρες το επόμενο ζευγάρι!", "good")
    else:
        owl("Κάνε κλικ σε δύο κάρτες. Αν ταιριάζουν, μένουν ανοιχτές!")

    with st.container(key="memory-board"):
        per_row = 4
        for row_start in range(0, len(cards), per_row):
            cols = st.columns(per_row)
            for offset, col in enumerate(cols):
                i = row_start + offset
                if i >= len(cards):
                    continue
                if i in found:
                    lbl = f"✅ {cards[i]['text']}"
                elif i in opened:
                    lbl = cards[i]["text"]
                else:
                    lbl = back
                if col.button(lbl, key=f"card_{i}", disabled=i in found, width="stretch"):
                    memory_click(i)
                    st.rerun()


# ─────────── Ταξίδι με Αερόστατο ───────────

def render_voyage():
    game = GAMES["voyage"]
    stops = st.session_state.a_items
    total = len(stops)
    if st.session_state.a_done:
        render_game_end("voyage", total * 20, ("🎈 Στάσεις", f"{total}/{total}"))
        return

    game_header(game, st.session_state.a_i, total)
    s = stops[st.session_state.a_i]
    answered = st.session_state.a_answered
    path = st.session_state.v_path
    out = st.session_state.v_out

    left, right = st.columns([3, 2])
    with left:
        m = game_map()
        emoji_marker(gd.VOYAGE_START["lat"], gd.VOYAGE_START["lon"], "🚩", tooltip=gd.VOYAGE_START["name"]).add_to(m)
        for visited in stops[:st.session_state.a_i + (1 if answered else 0)]:
            emoji_marker(visited["entity"]["lat"], visited["entity"]["lon"], "⭐", tooltip=visited["name"]).add_to(m)
        if len(path) > 1:
            folium_plugins.AntPath(path, color="#d1495b", pulse_color="#ffd166", weight=4, delay=900).add_to(m)
        emoji_marker(path[-1][0], path[-1][1], "🎈").add_to(m)
        st_folium(m, width=None, height=450, key=f"voyage_{st.session_state.a_i}_{answered}",
                  returned_objects=[], use_container_width=True)
    with right:
        if st.session_state.a_i == 0 and not answered and not out:
            owl("Ανέβα στο αερόστατο! Ξεκινάμε από τον Πειραιά. Λύσε τον γρίφο για να φυσήξει ούριος άνεμος!")
        st.markdown(f'<div class="question">🧩 {html.escape(s["clue"])}<br><br>Ποιος τόπος είμαι;</div>', unsafe_allow_html=True)
        st.write("")
        for i, name in enumerate(s["opts"]):
            if i in out:
                continue
            lbl = f"✅ {name}" if answered and i == s["correct"] else name
            if st.button(lbl, key=f"voy_{st.session_state.a_i}_{i}", disabled=answered, width="stretch"):
                if i == s["correct"]:
                    pts = 20 if not out else 10
                    st.session_state.a_score += pts
                    st.session_state.a_correct += 1
                    st.session_state.a_answered = True
                    st.session_state.v_gain = pts
                    path.append([s["entity"]["lat"], s["entity"]["lon"]])
                    play_sfx("ok")
                else:
                    out.append(i)
                    play_sfx("no")
                st.rerun()
        if out and not answered:
            owl("Μια φουρτούνα μάς παρέσυρε! Διάβασε ξανά τον γρίφο και δοκίμασε άλλη απάντηση.", "oops")
        if answered:
            owl(f'Φτάσαμε: {s["name"]}! +{st.session_state.v_gain} πόντοι.', "good")
            if s["entity"].get("fact"):
                st.info(f'📖 {s["entity"]["fact"]}')
            if st.button("Φύσα, αεράκι! 🎈→", type="primary", width="stretch"):
                st.session_state.v_out = []
                next_round(total)


GAME_RENDERERS = {"find": render_find, "compass": render_compass, "compare": render_compare,
                  "memory": render_memory, "voyage": render_voyage}


# ═══════════════════════════ ΣΕΛΙΔΑ: ΤΑ ΕΠΙΤΕΥΓΜΑΤΑ ΜΟΥ ═══════════════════════════

def render_trophies():
    p = get_profile()
    name = st.session_state.player_name
    render_hero(p)

    st.subheader("🏅 Τα παράσημά μου")
    earned = set(get_badges(name))
    st.caption(f"Έχεις κερδίσει {len(earned & set(BADGES))} από τα {len(BADGES)} παράσημα.")
    cols = st.columns(3)
    for i, (key, label) in enumerate(BADGES.items()):
        cls, shown = ("badge-card", label) if key in earned else ("badge-card locked", f"🔒 {label}")
        cols[i % 3].markdown(f'<div class="{cls}">{shown}<small>{BADGE_HOW[key]}</small></div>', unsafe_allow_html=True)

    st.subheader("⭐ Η πρόοδός μου στο βιβλίο")
    for u in gd.UNITS:
        got = sum(p["stars"].get(t, 0) for t in u["topics"])
        most = 3 * len(u["topics"])
        st.progress(got / most, text=f"{u['icon']} {u['title']} · {got}/{most} ⭐")

    st.subheader("🏆 Πίνακας ρεκόρ")
    scores = load_scores()
    if scores:
        medals = ["🥇", "🥈", "🥉"]
        for i, s in enumerate(scores):
            mark = medals[i] if i < 3 else f"{i + 1}."
            st.write(f"{mark} **{html.escape(str(s['name']))}** — {s['points']}π ({s['topic']})")
    else:
        st.caption("Παίξε και γράψε το πρώτο ρεκόρ!")

    if st.button("🏠 Στην αρχική", width="stretch"):
        go_to("home")


# ═══════════════════════════ SIDEBAR ═══════════════════════════

def render_sidebar():
    with st.sidebar:
        st.header("🌍 Γεωγραφία Εξερευνητής")
        p = get_profile()
        lvl = level_info(p["xp"])
        st.markdown(f'**{p["avatar"]} {html.escape(st.session_state.player_name)}** · {lvl["icon"]} {lvl["title"]}')
        st.progress(lvl["progress"], text=f'{p["xp"]} XP')

        c1, c2 = st.columns(2)
        if c1.button("🏠 Αρχική", width="stretch"):
            go_to("home")
        if c2.button("🏅 Τρόπαια", width="stretch"):
            go_to("trophies")

        st.divider()
        st.subheader("📚 Ύλη (όπως στο βιβλίο)")
        default_unit = st.session_state.get("sidebar_unit", gd.UNITS[0]["key"])
        unit_labels = [f"{u['icon']} {u['title']}" for u in gd.UNITS]
        idx = next((i for i, u in enumerate(gd.UNITS) if u["key"] == default_unit), 0)
        choice = st.radio("Ενότητα", unit_labels, index=idx, label_visibility="collapsed")
        unit = gd.UNITS[unit_labels.index(choice)]
        st.session_state.sidebar_unit = unit["key"]
        st.caption(unit["sub"])

        for topic_key in unit["topics"]:
            meta = gd.TOPIC_META[topic_key]
            if st.button(f"{meta['icon']} {meta['title']}", key=f"nav_{topic_key}", width="stretch"):
                st.session_state.cur_topic = topic_key
                go_to("explore")

        st.divider()
        st.subheader("🎛️ Ρυθμίσεις")
        st.session_state.sound_on = st.toggle("🎵 Ήχοι παιχνιδιού", st.session_state.sound_on)
        st.session_state.voice_on = st.toggle("🔊 Φωνή", st.session_state.voice_on)
        st.session_state.easy_map = st.toggle("🗺️ Εύκολος χάρτης στα κουίζ", st.session_state.easy_map,
                                              help="Δείχνει το όνομα κάθε πινέζας όταν περνάς το ποντίκι από πάνω της.")
        st.session_state.n_questions = st.slider("Ερωτήσεις/κουίζ", 4, 8, min(st.session_state.n_questions, 8))
        if get_client():
            st.session_state.ai_bonus_on = st.toggle(
                "🤖 AI ερώτηση-μπόνους", st.session_state.ai_bonus_on,
                help="Προσθέτει 1 ζωντανή ερώτηση από το πραγματικό βιβλίο μέσω OpenAI (μικρό κόστος).")
        else:
            st.session_state.ai_bonus_on = False

        st.divider()
        if st.button("👋 Αλλαγή παίκτη", width="stretch"):
            st.session_state.player_name = None
            go_to("home")


# ═══════════════════════════ MAIN ═══════════════════════════

st.markdown(CSS, unsafe_allow_html=True)
init_state()

if not st.session_state.player_name:
    render_welcome()
else:
    render_sidebar()
    view = st.session_state.view
    if view == "quiz" and st.session_state.get("g_playing"):
        render_quiz(st.session_state.cur_topic)
    elif view == "game" and st.session_state.get("cur_game"):
        GAME_RENDERERS[st.session_state.cur_game]()
    elif view == "explore" and st.session_state.get("cur_topic"):
        render_explore(st.session_state.cur_topic)
    elif view == "trophies":
        render_trophies()
    else:
        render_home()
flush_sfx()
