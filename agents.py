# -*- coding: utf-8 -*-
"""
🤖 ΟΙ ΠΡΑΚΤΟΡΕΣ (multi-agent, με RAG πάνω στα σχολικά βιβλία)

  1. RetrievalAgent      — βρίσκει σχετικό απόσπασμα από τη ΒΑΣΗ ΓΝΩΣΗΣ (τα βιβλία)
  2. QuestionDesigner    — φτιάχνει ερώτηση + απάντηση ΖΩΝΤΑΝΑ, βασισμένη στο απόσπασμα
  3. InteractionDesigner — διαλέγει μορφή: χάρτης/χρονογραμμή/αριθμογραμμή/κουμπιά
  4. ImageAgent          — φτιάχνει εικόνα με DALL·E όταν βοηθάει
  5. Tutor               — υποδείξεις & εξηγήσεις
"""
import json, random

RENDERABLE_TYPES = ["choice", "map", "timeline", "number_line"]


def _chat(client, system, user, max_tokens=900, temperature=0.7):
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        max_tokens=max_tokens, temperature=temperature)
    return r.choices[0].message.content.strip()


def _json(raw):
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


# ── 1. Retrieval: διάλεξε σχετικό απόσπασμα από τα βιβλία ──
def retrieve(knowledge_base, subject, k=1):
    chunks = knowledge_base.get(subject, [])
    if not chunks:
        return []
    return random.sample(chunks, min(k, len(chunks)))


# ── 2+3. Φτιάξε ΜΙΑ διαδραστική ερώτηση από το απόσπασμα ──
def make_question(client, subject, passage):
    system = ("Είσαι έμπειρος δάσκαλος & σχεδιαστής εκπαιδευτικών παιχνιδιών για "
              "παιδιά Ε' Δημοτικού (10-11 ετών). Φτιάχνεις ΜΙΑ διαδραστική ερώτηση "
              "ΑΥΣΤΗΡΑ βασισμένη στο απόσπασμα του σχολικού βιβλίου που σου δίνεται. "
              "Διαθέσιμες μορφές: " + ", ".join(RENDERABLE_TYPES) + ".")
    user = (
        f"Μάθημα: {subject}\n\n"
        f"Απόσπασμα από το σχολικό βιβλίο:\n\"\"\"{passage[:1500]}\"\"\"\n\n"
        "Φτιάξε ΜΙΑ ερώτηση πολλαπλής επιλογής βασισμένη ΣΕ ΑΥΤΟ το απόσπασμα.\n"
        "Διάλεξε την πιο διασκεδαστική μορφή:\n"
        "• map → μόνο για γνωστά γεωγραφικά μέρη με σίγουρες συντεταγμένες.\n"
        "• timeline → για 'πότε' με χρονολογίες (αύξουσα σειρά).\n"
        "• number_line → για αριθμητική απάντηση με λογικό min/max.\n"
        "• choice → για όλα τα υπόλοιπα (4 επιλογές).\n\n"
        "Επίστρεψε ΜΟΝΟ JSON με ΕΝΑ από αυτά τα σχήματα:\n"
        '{"q":"...","type":"choice","opts":["Α","Β","Γ","Δ"],"correct":0,"image_hint":""}\n'
        '{"q":"...","type":"map","center":[lat,lon],"zoom":5,"opts":[{"name":"...","lat":0,"lon":0}],"correct":0,"image_hint":""}\n'
        '{"q":"...","type":"timeline","opts":["1453","1821","1912"],"correct":1,"image_hint":""}\n'
        '{"q":"...","type":"number_line","correct_value":50,"min":0,"max":100,"step":1,"tolerance":0,"unit":"","image_hint":""}\n'
        "Το correct = δείκτης (0-3) της σωστής. Το image_hint = σύντομη περιγραφή για "
        "παιδική εικονογράφηση αν ταιριάζει (αλλιώς κενό). Όλα στα ελληνικά."
    )
    return _json(_chat(client, system, user, max_tokens=700, temperature=0.8))


# ── 4. Εικόνα με DALL·E ──
def make_image(client, hint):
    prompt = (f"Παιδική, χαρούμενη, εκπαιδευτική εικονογράφηση για βιβλίο Δημοτικού. "
              f"Καθαρό στιλ καρτούν, φωτεινά χρώματα, χωρίς κείμενο/γράμματα. Θέμα: {hint}")
    r = client.images.generate(model="dall-e-3", prompt=prompt, size="1024x1024", n=1)
    return r.data[0].url


# ── 5. Δάσκαλος ──
def tutor_hint(client, subject, question, correct):
    return _chat(client,
        "Είσαι υπομονετικός, χαρούμενος δάσκαλος για παιδί 10-11 ετών.",
        f"Μάθημα: {subject}\nΕρώτηση: \"{question}\"\nΣωστή (ΜΥΣΤΙΚΟ): \"{correct}\"\n"
        f"Δώσε ΜΙΑ σύντομη παιχνιδιάρικη υπόδειξη (2-3 προτάσεις). Μην πεις τη σωστή.",
        max_tokens=180, temperature=0.85)


def tutor_explain(client, subject, question, correct):
    return _chat(client,
        "Είσαι ευγενικός δάσκαλος Ε' Δημοτικού.",
        f"Μάθημα: {subject}\nΕρώτηση: \"{question}\"\nΣωστή: \"{correct}\"\n"
        f"Εξήγησε σε 1-2 απλές προτάσεις ΓΙΑΤΙ είναι σωστή, φιλικά.",
        max_tokens=140, temperature=0.6)


# ── Έλεγχος εγκυρότητας ──
def valid(q):
    t = q.get("type")
    if t not in RENDERABLE_TYPES:
        return False
    try:
        if t == "choice":
            return len(q["opts"]) >= 2 and 0 <= q["correct"] < len(q["opts"])
        if t == "map":
            return (isinstance(q["center"], list) and len(q["center"]) == 2
                    and len(q["opts"]) >= 2 and 0 <= q["correct"] < len(q["opts"])
                    and all("lat" in o and "lon" in o and "name" in o for o in q["opts"]))
        if t == "timeline":
            return len(q["opts"]) >= 2 and 0 <= q["correct"] < len(q["opts"])
        if t == "number_line":
            return q["min"] < q["max"] and q["min"] <= q["correct_value"] <= q["max"]
    except (KeyError, TypeError):
        return False
    return False


def normalize(q):
    if q.get("type") == "number_line":
        q.setdefault("step", 1); q.setdefault("tolerance", 0); q.setdefault("unit", "")
    q.setdefault("image_hint", "")
    return q


# ── Ενορχήστρωση: φτιάξε ΜΙΑ έγκυρη ερώτηση (ζωντανά) ──
def generate_one(client, knowledge_base, subject):
    passages = retrieve(knowledge_base, subject, 1)
    passage = passages[0] if passages else subject
    for _ in range(2):  # μία επανάληψη αν βγει άκυρη
        try:
            q = make_question(client, subject, passage)
            if valid(q):
                return normalize(q)
        except Exception:
            pass
    # ασφαλές fallback
    return {"q": f"Ποιο μάθημα παίζεις τώρα;", "type": "choice",
            "opts": [subject, "Άλλο", "Κανένα", "Δεν ξέρω"], "correct": 0, "image_hint": ""}
