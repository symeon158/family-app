# -*- coding: utf-8 -*-
"""
🎓 Ο Ηλεκτρονικός Δάσκαλος — ΕΚΔΟΣΗ ΜΕ ΤΑ ΣΧΟΛΙΚΑ ΒΙΒΛΙΑ
Python + Streamlit + OpenAI (GPT-4o-mini + DALL·E) + gTTS + Folium

Οι πράκτορες φτιάχνουν ΖΩΝΤΑΝΑ ερωτήσεις βασισμένες στα ΠΡΑΓΜΑΤΙΚΑ
βιβλία της Ε' Δημοτικού (knowledge_base.json) και διαλέγουν μόνοι τους
την καλύτερη διαδραστική μορφή + εικόνες DALL·E.
"""
import streamlit as st
from openai import OpenAI
from gtts import gTTS
import folium
from streamlit_folium import st_folium
import agents
import random, json, io, os

st.set_page_config(page_title="Ο Ηλεκτρονικός Δάσκαλος", page_icon="🎓", layout="centered")
SCORES_FILE = "highscores.json"
KB_FILE = "knowledge_base.json"
SUBJECTS = {"Γεωγραφία": "🗺️", "Ιστορία": "📜", "Φυσικά": "🔬", "Μαθηματικά": "📐"}

@st.cache_resource
def get_client():
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

@st.cache_resource
def load_kb():
    return json.load(open(KB_FILE, encoding="utf-8"))

@st.cache_data(show_spinner=False)
def text_to_speech(text):
    tts = gTTS(text=text, lang="el"); buf = io.BytesIO(); tts.write_to_fp(buf); return buf.getvalue()

@st.cache_data(show_spinner=False)
def gen_image(hint):
    return agents.make_image(get_client(), hint)

def opt_name(o):
    return o["name"] if isinstance(o, dict) else str(o)

def load_scores():
    if os.path.exists(SCORES_FILE):
        try: return json.load(open(SCORES_FILE, encoding="utf-8"))
        except Exception: return []
    return []

def save_score(name, pts, subj):
    s = load_scores(); s.append({"name": name, "points": pts, "subject": subj})
    s = sorted(s, key=lambda x: x["points"], reverse=True)[:10]
    json.dump(s, open(SCORES_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def init_state():
    st.session_state.setdefault("player_name", "Παίκτης")
    st.session_state.setdefault("n_questions", 8)
    st.session_state.setdefault("voice_on", True)
    st.session_state.setdefault("images_on", True)
    st.session_state.setdefault("playing", False)

def new_question():
    """Ζητά ΖΩΝΤΑΝΑ μια νέα ερώτηση από τους πράκτορες."""
    with st.spinner("🤖 Ο πράκτορας φτιάχνει μια ερώτηση από το βιβλίο..."):
        q = agents.generate_one(get_client(), load_kb(), st.session_state.subject)
    st.session_state.q = q
    st.session_state.answered = False
    st.session_state.selected = None
    st.session_state.hint = None
    st.session_state.used_hint = False
    st.session_state.explanation = None
    st.session_state.img_url = None
    st.session_state.last_gain = 0

def start_round(subject):
    st.session_state.update(dict(
        subject=subject, index=0, total=st.session_state.n_questions,
        points=0, streak=0, best_streak=0, lives=3, correct_count=0,
        finished=False, playing=True, score_saved=False))
    new_question()

def register(is_correct, chosen):
    st.session_state.answered = True
    st.session_state.selected_disp = chosen
    if is_correct:
        st.session_state.streak += 1
        st.session_state.best_streak = max(st.session_state.best_streak, st.session_state.streak)
        gain = 10 + (5 if st.session_state.streak >= 3 else 0)
        if st.session_state.used_hint: gain = max(5, gain - 5)
        st.session_state.points += gain; st.session_state.last_gain = gain
        st.session_state.correct_count += 1
    else:
        st.session_state.streak = 0; st.session_state.lives -= 1; st.session_state.last_gain = 0

def correct_display(q):
    if q.get("type") == "number_line":
        return f'{q["correct_value"]} {q.get("unit","")}'.strip()
    return opt_name(q["opts"][q["correct"]])

init_state()

# ─────────── SIDEBAR ───────────
with st.sidebar:
    st.header("⚙️ Μενού")
    st.session_state.player_name = st.text_input("👤 Όνομα", st.session_state.player_name)
    st.subheader("📚 Μάθημα")
    st.caption("Φρέσκες ερωτήσεις από τα σχολικά βιβλία!")
    for subj, ic in SUBJECTS.items():
        if st.button(f"{ic} {subj}", use_container_width=True, key=f"sb_{subj}"):
            start_round(subj); st.rerun()
    st.divider()
    st.subheader("🎛️ Ρυθμίσεις")
    st.session_state.n_questions = st.slider("Ερωτήσεις/παιχνίδι", 4, 12, st.session_state.n_questions)
    st.session_state.voice_on = st.toggle("🔊 Φωνή", st.session_state.voice_on)
    st.session_state.images_on = st.toggle("🎨 Εικόνες DALL·E", st.session_state.images_on)
    st.caption("Οι εικόνες κοστίζουν ~4 σεντς η καθεμία.")
    st.divider()
    st.subheader("🏆 Ρεκόρ")
    for i, s in enumerate(load_scores()[:5], 1):
        st.write(f"{i}. **{s['name']}** — {s['points']}π ({s['subject']})")

# ─────────── ΤΙΤΛΟΣ ───────────
st.title("🎓 Ο Ηλεκτρονικός Δάσκαλος")
st.caption("🤖 Οι πράκτορες φτιάχνουν ερωτήσεις από τα πραγματικά βιβλία της Ε' Δημοτικού!")

if not st.session_state.playing:
    st.info("👈 Διάλεξε μάθημα από το μενού!\n\n"
            "Οι πράκτορες διαβάζουν το σχολικό βιβλίο, φτιάχνουν ερωτήσεις και "
            "διαλέγουν μόνοι τους τη μορφή: 🗺️ χάρτη, 📅 χρονογραμμή, 🔢 αριθμογραμμή ή κουμπιά — "
            "με 🎨 εικόνες DALL·E!")
    st.stop()

# ─────────── ΤΕΛΟΣ ───────────
if st.session_state.finished:
    pts, total = st.session_state.points, st.session_state.total
    maxp = total * 10
    if pts >= maxp*0.9:   stars, msg, badge = "⭐⭐⭐", "🏆 ΤΕΛΕΙΟΣ!", "Χρυσό"
    elif pts >= maxp*0.6: stars, msg, badge = "⭐⭐", "🎉 Πολύ καλά!", "Αργυρό"
    elif pts >= maxp*0.35:stars, msg, badge = "⭐", "👍 Καλή προσπάθεια!", "Χάλκινο"
    else:                 stars, msg, badge = "✨", "📚 Συνέχισε!", "Προσπάθειας"
    st.error("💔 Τελείωσαν οι ζωές!") if st.session_state.lives <= 0 else st.success(msg)
    st.markdown(f"<h1 style='text-align:center'>{stars}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center'>🏅 Παράσημο {badge}</h3>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("🏅 Πόντοι", pts); c2.metric("✅ Σωστές", f"{st.session_state.correct_count}/{total}")
    c3.metric("🔥 Σερί", st.session_state.best_streak)
    if not st.session_state.score_saved:
        save_score(st.session_state.player_name, pts, st.session_state.subject)
        st.session_state.score_saved = True
    b1, b2 = st.columns(2)
    if b1.button("🔄 Νέο παιχνίδι", use_container_width=True):
        start_round(st.session_state.subject); st.rerun()
    if b2.button("📚 Άλλο μάθημα", use_container_width=True):
        st.session_state.playing = False; st.rerun()
    st.stop()

# ─────────── ΠΑΙΧΝΙΔΙ ───────────
q = st.session_state.q
subject = st.session_state.subject
total = st.session_state.total
qtype = q.get("type", "choice")
answered = st.session_state.answered
sel = st.session_state.selected

hearts = "❤️"*st.session_state.lives + "🤍"*(3-st.session_state.lives)
t1, t2, t3 = st.columns(3)
t1.markdown(f"**{hearts}**"); t2.markdown(f"🏅 **{st.session_state.points}** π."); t3.markdown(f"🔥 **{st.session_state.streak}**")
st.progress(st.session_state.index/total, text=f"📚 {subject} · Ερώτηση {st.session_state.index+1}/{total}")

badges = {"map":"🗺️ Χάρτης","timeline":"📅 Χρονογραμμή","number_line":"🔢 Αριθμογραμμή","choice":"🔘 Επιλογές"}
st.caption(f"Μορφή: {badges.get(qtype,'🔘')}")
st.markdown(f"### {q['q']}")

# Εικόνα DALL·E (αν υπάρχει hint & είναι ενεργές)
if st.session_state.images_on and q.get("image_hint"):
    if st.session_state.img_url is None:
        try:
            with st.spinner("🎨 Ζωγραφίζω μια εικόνα..."):
                st.session_state.img_url = gen_image(q["image_hint"])
        except Exception:
            st.session_state.img_url = ""
    if st.session_state.img_url:
        st.image(st.session_state.img_url, use_container_width=True)

if st.session_state.voice_on and st.button("🔊 Διάβασέ μου την ερώτηση"):
    st.audio(text_to_speech(q["q"]), format="audio/mp3", autoplay=True)
st.write("")

# ─── RENDERERS ───
def r_choice():
    for i, o in enumerate(q["opts"]):
        lbl = opt_name(o)
        if answered:
            if i == q["correct"]: lbl = f"✅ {lbl}"
            elif i == sel:        lbl = f"❌ {lbl}"
        if st.button(lbl, key=f"opt_{i}", disabled=answered, use_container_width=True):
            st.session_state.selected = i; register(i == q["correct"], opt_name(o)); st.rerun()

def r_timeline():
    st.caption("🖱️ Κλικ στη σωστή χρονολογία (παλιά → νέα):")
    cols = st.columns(len(q["opts"]))
    for i, o in enumerate(q["opts"]):
        lbl = str(o)
        if answered:
            if i == q["correct"]: lbl = f"✅ {lbl}"
            elif i == sel:        lbl = f"❌ {lbl}"
        with cols[i]:
            if st.button(lbl, key=f"tl_{i}", disabled=answered, use_container_width=True):
                st.session_state.selected = i; register(i == q["correct"], str(o)); st.rerun()

def r_number():
    lo, hi, step = float(q["min"]), float(q["max"]), float(q.get("step", 1))
    tol = q.get("tolerance", 0); unit = q.get("unit", "")
    guess = st.slider("Σύρε στον σωστό αριθμό:", lo, hi, (lo+hi)//2, step,
                      disabled=answered, key=f"nl_{st.session_state.index}")
    shown = int(guess) if float(guess).is_integer() else round(guess, 2)
    st.markdown(f"<h2 style='text-align:center'>{shown} {unit}</h2>", unsafe_allow_html=True)
    if not answered and st.button("✅ Απάντησε", type="primary", use_container_width=True):
        st.session_state.selected = 0
        register(abs(guess - q["correct_value"]) <= tol, f"{shown} {unit}".strip()); st.rerun()

def r_map():
    st.caption("🖱️ Κλικ στο σωστό σημείο (ή στα κουμπιά κάτω).")
    m = folium.Map(location=q["center"], zoom_start=q.get("zoom", 4), tiles="OpenStreetMap")
    for i, o in enumerate(q["opts"]):
        color = ("green" if i == q["correct"] else ("red" if i == sel else "gray")) if answered else "blue"
        folium.Marker([o["lat"], o["lon"]], tooltip=o["name"],
                      icon=folium.Icon(color=color, icon="info-sign")).add_to(m)
    out = st_folium(m, width=700, height=380, key=f"map_{st.session_state.index}")
    if not answered and out and out.get("last_object_clicked"):
        c = out["last_object_clicked"]
        _, near = min(((o["lat"]-c["lat"])**2+(o["lon"]-c["lng"])**2, i) for i, o in enumerate(q["opts"]))
        st.session_state.selected = near; register(near == q["correct"], opt_name(q["opts"][near])); st.rerun()
    st.write("**Ή διάλεξε εδώ:**")
    cc = st.columns(2)
    for i, o in enumerate(q["opts"]):
        with cc[i % 2]:
            if st.button(opt_name(o), key=f"mopt_{i}", disabled=answered, use_container_width=True):
                st.session_state.selected = i; register(i == q["correct"], opt_name(o)); st.rerun()

if qtype == "map":            r_map()
elif qtype == "timeline":     r_timeline()
elif qtype == "number_line":  r_number()
else:                         r_choice()

# ─── Βοήθεια ───
if not answered:
    st.write("")
    if st.button("🤔 Χρειάζομαι βοήθεια (−5 πόντοι)", use_container_width=True):
        with st.spinner("Ο δάσκαλος σκέφτεται..."):
            st.session_state.hint = agents.tutor_hint(get_client(), subject, q["q"], correct_display(q))
            st.session_state.used_hint = True
        st.rerun()
    if st.session_state.hint:
        st.info(f"💡 **Υπόδειξη:**\n\n{st.session_state.hint}")
        if st.session_state.voice_on and st.button("🔊 Διάβασέ μου την υπόδειξη"):
            st.audio(text_to_speech(st.session_state.hint), format="audio/mp3", autoplay=True)

# ─── Ανατροφοδότηση ───
if answered:
    cd = correct_display(q)
    if st.session_state.last_gain > 0:
        bonus = " (+5 bonus σερί! 🔥)" if st.session_state.last_gain > 10 else ""
        st.success(f"🎉 Σωστά! +{st.session_state.last_gain} πόντοι{bonus}"); st.balloons()
    else:
        st.error(f"💔 Όχι ακριβώς. Σωστή απάντηση: **{cd}**")
        if st.session_state.explanation is None:
            with st.spinner("Ο δάσκαλος εξηγεί..."):
                st.session_state.explanation = agents.tutor_explain(get_client(), subject, q["q"], cd)
        st.info(f"📖 {st.session_state.explanation}")
    if st.button("Επόμενη ερώτηση →", type="primary", use_container_width=True):
        st.session_state.index += 1
        if st.session_state.index >= total or st.session_state.lives <= 0:
            st.session_state.finished = True
        else:
            new_question()
        st.rerun()
