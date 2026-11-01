import csv, getpass, hashlib, hmac, io, json, os, re, secrets, sqlite3, sys, threading, time, datetime as dt, pathlib
import collections, statistics, traceback, urllib.parse, unicodedata
import cv2, numpy as np
from flask import Flask, Response, jsonify, redirect, request, send_file, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import pokescan as ps

AUTH = pathlib.Path("pokedata/auth.json")
if __name__ == "__main__" and "--setpw" in sys.argv:      # python app.py --setpw
    u = input("Nome utente: ").strip()
    p1 = getpass.getpass("Password (almeno 8 caratteri): ")
    if not u or len(p1) < 8 or p1 != getpass.getpass("Ripeti la password: "):
        sys.exit("Dati non validi o password diverse: non e' cambiato nulla.")
    AUTH.write_text(json.dumps({"user": u, "hash": generate_password_hash(p1)}))
    sys.exit("Password salvata. Il login e' attivo.")

KEYF = pathlib.Path("pokedata/justtcg.key")
CTKEYF = pathlib.Path("pokedata/cardtrader.key")
CTMAPF = pathlib.Path("pokedata/cardtrader_blueprints.json")
CTINFOF = pathlib.Path("pokedata/cardtrader_blueprint_info.json")
if __name__ == "__main__" and "--setkey" in sys.argv:      # python app.py --setkey
    k = getpass.getpass("Chiave API JustTCG (non viene mostrata): ").strip()
    if len(k) < 10:
        sys.exit("Chiave non valida: non e' cambiato nulla.")
    KEYF.write_text(k)
    sys.exit("Chiave salvata in pokedata/justtcg.key.")

if __name__ == "__main__" and "--set-cardtrader-key" in sys.argv:
    k = getpass.getpass("Token API CardTrader (non viene mostrato): ").strip()
    if len(k) < 10:
        sys.exit("Token non valido: non e' cambiato nulla.")
    CTKEYF.parent.mkdir(parents=True, exist_ok=True)
    CTKEYF.write_text(k)
    sys.exit("Token CardTrader salvato.")

app = Flask(__name__, static_folder="static")

# ---------- LOGIN ----------
def _key():
    f = pathlib.Path("pokedata/secret.key")
    if not f.exists():
        f.write_text(secrets.token_hex(32))
    return f.read_text().strip()


app.secret_key = _key()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
app.permanent_session_lifetime = dt.timedelta(days=30)
FAIL = {}
LIBERE = {"/login", "/logout", "/static/icon-180.png", "/static/icon-512.png", "/static/pokeball.svg"}
LOGIN = '<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<meta name="theme-color" content="#000"><title>Pokescan - Accesso</title><link rel="apple-touch-icon" href="/static/icon-180.png">\n<style>*{box-sizing:border-box}body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;color:#202532;font:16px Inter,system-ui,-apple-system,"Segoe UI",sans-serif;background:radial-gradient(circle at 8% 0%,rgba(255,246,196,.95),transparent 30%),radial-gradient(circle at 100% 100%,rgba(255,239,180,.7),transparent 34%),linear-gradient(145deg,#fffdf4 0%,#f7f3df 100%);position:relative;overflow:hidden}form{position:relative;z-index:1;width:100%;max-width:390px;padding:30px 22px;border-radius:28px;background:rgba(255,255,255,.9);border:1px solid #f1dfa0;box-shadow:0 18px 50px rgba(154,119,35,.14);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);text-align:center}img{width:76px;height:76px;border-radius:22px;margin-bottom:10px}h1{margin:0 0 18px;font-size:28px;letter-spacing:-.7px}input{width:100%;margin-bottom:12px;background:#fffdf5;border:1px solid #eadcae;color:#202532;border-radius:14px;padding:14px;font-size:16px;outline:0}input:focus{border-color:#e0bd3d;box-shadow:0 0 0 3px rgba(242,201,76,.2)}button{width:100%;border:0;border-radius:14px;padding:14px;font-size:16px;font-weight:750;background:#f2c94c;color:#252b36;cursor:pointer;box-shadow:0 8px 18px rgba(190,151,34,.18)}.e{color:#c54d4d;min-height:22px;margin-bottom:8px;font-size:14px}</style></head><body>\n<form method="post"><img src="/static/pokeball.svg" alt="Poké Ball"><h1>Pokescan</h1><div class="e" role="alert">@@ERR@@</div>\n<input name="u" placeholder="Nome utente" autocomplete="username" autocapitalize="none" autocorrect="off" required>\n<input name="p" type="password" placeholder="Password" autocomplete="current-password" required><button>Accedi</button></form></body></html>'


def auth():
    try:
        return json.loads(AUTH.read_text())
    except Exception:
        return None


def _tok(a):
    return hashlib.sha256(a["hash"].encode()).hexdigest()[:16]


def _ip():
    return (request.headers.get("X-Forwarded-For") or request.remote_addr or "?").split(",")[0].strip()


def _bloccato(ip):
    ora = time.time()
    for k in list(FAIL):
        FAIL[k] = [t for t in FAIL[k] if ora - t < 600]
        if not FAIL[k]:
            del FAIL[k]
    return len(FAIL.get(ip, [])) >= 5 or sum(len(v) for v in FAIL.values()) >= 30


@app.before_request
def protezione():
    a = auth()
    if not a or request.path in LIBERE or session.get("h") == _tok(a):
        return None
    if request.path.startswith(("/api/", "/img/")):
        return jsonify(errore="non autorizzato"), 401
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    a = auth()
    if not a:
        return redirect("/")
    err = ""
    if request.method == "POST":
        ip = _ip()
        if _bloccato(ip):
            err = "Troppi tentativi. Riprova tra 10 minuti."
        else:
            ok_u = hmac.compare_digest(request.form.get("u", "").strip().lower().encode(), a["user"].lower().encode())
            ok_p = check_password_hash(a["hash"], request.form.get("p", ""))
            if ok_u and ok_p:
                FAIL.pop(ip, None)
                session.clear()
                session.permanent = True
                session["h"] = _tok(a)
                return redirect("/")
            FAIL.setdefault(ip, []).append(time.time())
            time.sleep(1)
            err = "Nome utente o password errati."
    r = Response(LOGIN.replace("@@ERR@@", err), mimetype="text/html")
    r.headers["Cache-Control"] = "no-store"
    return r


@app.get("/logout")
def logout():
    session.clear()
    return redirect("/login")

M = ps.Matcher()
lock = threading.Lock()


def _riscalda():
    """Giro a vuoto all'avvio: la prima lettura del modello e' piu' lenta (inizializzazione), cosi' la prima scansione vera e' gia' veloce."""
    try:
        time.sleep(3)
        from PIL import Image as _I
        with lock:
            M.model.encode([_I.new("RGB", (224, 224), (128, 128, 128))], normalize_embeddings=True, convert_to_numpy=True)
            M._feat(np.full((420, 300, 3), 128, np.uint8))
    except Exception as e:
        print("riscaldamento:", e)


threading.Thread(target=_riscalda, daemon=True).start()
DB = "pokedata/collezione.db"
MARK = pathlib.Path("pokedata/ultimo_agg.txt")
LANGS = {"en": "Inglese", "it": "Italiano", "fr": "Francese", "de": "Tedesco", "es": "Spagnolo", "es-mx": "Spagnolo (Messico)",
         "pt": "Portoghese", "pt-br": "Portoghese (Brasile)", "pt-pt": "Portoghese (Portogallo)", "nl": "Olandese", "pl": "Polacco",
         "ru": "Russo", "ja": "Giapponese", "ko": "Coreano", "zh-tw": "Cinese (trad.)", "zh-cn": "Cinese (semp.)",
         "th": "Thailandese", "id": "Indonesiano"}


def sid(cid):
    return cid.rsplit("-", 1)[0]


def cardtrader_key():
    try:
        return CTKEYF.read_text().strip() or None
    except OSError:
        return os.environ.get("CARDTRADER_API_TOKEN") or None


def cardtrader_map():
    try:
        data = json.loads(CTMAPF.read_text(encoding="utf-8"))
        return {str(k): int(v) for k, v in data.items()}
    except (OSError, ValueError, TypeError):
        return {}


def cardtrader_info():
    try:
        data = json.loads(CTINFOF.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _ct_props(blueprint):
    out = {}
    for prop in blueprint.get("editable_properties") or []:
        if isinstance(prop, dict) and prop.get("name"):
            out[prop["name"]] = prop.get("possible_values") or []
    return out


def _ct_save_info(blueprint_id, blueprint):
    data = cardtrader_info()
    data.setdefault("blueprints", {})[str(int(blueprint_id))] = {"props": _ct_props(blueprint)}
    CTINFOF.parent.mkdir(parents=True, exist_ok=True)
    CTINFOF.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def ensure_cardtrader_map():
    CTMAPF.parent.mkdir(parents=True, exist_ok=True)
    if not CTMAPF.exists():
        CTMAPF.write_text("{}\n", encoding="utf-8")


CT_MAP_LOCK = threading.Lock()
CT_RESOLVE_LOCK = threading.Lock()
CT_RESOLVE_RUNNING = False
CT_RESOLVE_STARTED = False
CT_EXPANSION_CACHE = None
CT_BLUEPRINT_CACHE = {}
CT_EXPANSION_ALIASES = {"30th": 4679}

CT_COND = {
    "NM": "Near Mint",
    "LP": "Slightly Played",
    "MP": "Moderately Played",
    "HP": "Played",
    "DMG": "Poor",
}
CT_COND_ALIAS = {v: k for k, v in CT_COND.items()}
CT_COND_ALIAS.update({
    "Lightly Played": "LP",
    "Moderately Played": "MP",
    "Heavily Played": "HP",
    "Damaged": "DMG",
})


def _ct_norm(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(c for c in text if not unicodedata.combining(c)).lower().strip()


def _ct_texts(value):
    if isinstance(value, str):
        return {_ct_norm(value)}
    if isinstance(value, dict):
        out = set()
        for child in value.values():
            out.update(_ct_texts(child))
        return out
    return set()


def _ct_number(value):
    value = _ct_norm(value).split("/", 1)[0].strip()
    return value.lstrip("0") or "0"


def _ct_version_numbers(value):
    text = str(value or "")
    return re.findall(r"(?:^|\|)\s*(\d+)\s*/\s*\d+", text)


def _ct_blueprint_numbers(blueprint):
    values = []
    values.extend(_ct_values(
        blueprint,
        {"number", "local_id", "collector_number", "card_number", "localId"},
    ))
    values.extend(_ct_values(
        blueprint.get("fixed_properties"),
        {"number", "local_id", "collector_number", "card_number", "localId"},
    ))
    values.extend(_ct_version_numbers(blueprint.get("version")))
    return values


def _ct_values(value, keys):
    if isinstance(value, dict):
        out = []
        for key, child in value.items():
            if key in keys:
                out.extend(_ct_values(child, keys))
            elif isinstance(child, (dict, list)):
                out.extend(_ct_values(child, keys))
        return out
    if isinstance(value, list):
        out = []
        for child in value:
            out.extend(_ct_values(child, keys))
        return out
    return [value] if value is not None else []


def _ct_set_code(value):
    return re.sub(r"[^a-z0-9]", "", _ct_norm(value)).lstrip("0")


def _ct_card_names(card_id):
    names = set()
    for meta in getattr(M, "meta", []):
        if meta.get("id") == card_id and meta.get("lang") in ("en", "it"):
            names.update(_ct_texts(meta.get("name")))
    return names


def _ct_set_names(card_id, set_name):
    names = {_ct_norm(set_name)}
    set_id = card_id.rsplit("-", 1)[0]
    for meta in getattr(M, "meta", []):
        if meta.get("id", "").rsplit("-", 1)[0] == set_id:
            names.update(_ct_texts(meta.get("set")))
    return {name for name in names if name}


def _ct_blueprints(expansion_id):
    if expansion_id not in CT_BLUEPRINT_CACHE:
        CT_BLUEPRINT_CACHE[expansion_id] = _ct_items(
            cardtrader_get("/blueprints/export?expansion_id=" + urllib.parse.quote(str(expansion_id)))
        )
    return CT_BLUEPRINT_CACHE[expansion_id]


def _ct_expansion_matches(expansion, set_name, set_code):
    if expansion.get("game_id") not in (None, 5):
        return False
    wanted_name = _ct_norm(set_name)
    wanted_code = _ct_set_code(set_code)
    normalized = set()
    for key in ("name", "title", "name_en", "code", "slug", "id"):
        normalized.update(_ct_texts(expansion.get(key)))
    codes = {_ct_set_code(value) for value in normalized}
    if wanted_code and wanted_code in codes:
        return True
    if wanted_code and any(wanted_code.rstrip("0") == code.rstrip("0") for code in codes if code):
        return True
    return bool(wanted_name and any(
        wanted_name in value or value in wanted_name
        for value in normalized
        if value
    ))


def _ct_expansion_score(expansion, names, set_code):
    if expansion.get("game_id") != 5:
        return 0
    values = set()
    for key in ("name", "title", "name_en", "code", "slug"):
        values.update(_ct_texts(expansion.get(key)))
    wanted = set(names)
    score = 0
    if _ct_set_code(set_code) in {_ct_set_code(value) for value in values}:
        score += 100
    for value in values:
        if any(value == name for name in wanted):
            score += 80
        elif any(name in value or value in name for name in wanted):
            score += 20
    if "30" in set_code and any("anniversary" in value or "30th" in value for value in values):
        score += 50
    return score


def _ct_items(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("blueprints", "data", "items"):
            if isinstance(data.get(key), list):
                return data[key]
        return [v for v in data.values() if isinstance(v, dict)]
    return []


def cardtrader_resolve(card_id, name, set_name, number, lang):
    """Trova e persiste il blueprint CardTrader quando la corrispondenza e' univoca."""
    if not cardtrader_key():
        return
    ensure_cardtrader_map()
    with CT_MAP_LOCK:
        mapping = cardtrader_map()
        if card_id in mapping:
            return
    try:
        global CT_EXPANSION_CACHE
        if CT_EXPANSION_CACHE is None:
            CT_EXPANSION_CACHE = [
                x for x in _ct_items(cardtrader_get("/expansions"))
                if x.get("game_id") == 5
            ]
        expansions = CT_EXPANSION_CACHE
        set_names = _ct_set_names(card_id, set_name)
        candidates = [
            x for x in expansions
            if _ct_expansion_score(x, set_names, card_id.rsplit("-", 1)[0])
        ]
        alias_id = CT_EXPANSION_ALIASES.get(card_id.rsplit("-", 1)[0])
        if alias_id is not None:
            candidates = [
                x for x in expansions if x.get("id") == alias_id
            ] or candidates
        candidates.sort(
            key=lambda x: _ct_expansion_score(x, set_names, card_id.rsplit("-", 1)[0]),
            reverse=True,
        )
        candidates = candidates[:3]
        matches = []
        card_names = _ct_card_names(card_id) | {_ct_norm(name)}
        for expansion in candidates:
            expansion_id = expansion.get("id")
            if expansion_id is None:
                continue
            blueprints = _ct_blueprints(expansion_id)
            for blueprint in blueprints:
                bp_names = set()
                for key in ("name", "title", "name_en", "name_it"):
                    bp_names.update(_ct_texts(blueprint.get(key)))
                bp_numbers = _ct_blueprint_numbers(blueprint)
                if card_names & bp_names and any(
                    _ct_number(value) == _ct_number(number) for value in bp_numbers
                ):
                    blueprint_id = blueprint.get("id") or blueprint.get("blueprint_id")
                    if blueprint_id is not None:
                        matches.append(int(blueprint_id))
        matches = sorted(set(matches))
        if len(matches) == 1:
            CT_MAP_LOCK.acquire()
            try:
                mapping = cardtrader_map()
                if card_id not in mapping:
                    mapping[card_id] = matches[0]
                    CTMAPF.parent.mkdir(parents=True, exist_ok=True)
                    CTMAPF.write_text(json.dumps(mapping, indent=2, sort_keys=True), encoding="utf-8")
                    matched = next(
                        (b for b in blueprints if int(b.get("id") or b.get("blueprint_id") or 0) == matches[0]),
                        None,
                    )
                    if matched:
                        _ct_save_info(matches[0], matched)
            finally:
                CT_MAP_LOCK.release()
        elif len(matches) > 1:
            jtl(f"CardTrader blueprint ambiguo {card_id}: {matches}")
        else:
            jtl(f"CardTrader blueprint non trovato {card_id} ({name}, {set_name}, {number}, {lang})")
    except Exception:
        jtl("ERRORE ricerca blueprint CardTrader " + traceback.format_exc()[-500:])


def cardtrader_resolve_all():
    global CT_RESOLVE_RUNNING, CT_RESOLVE_STARTED
    with CT_RESOLVE_LOCK:
        if CT_RESOLVE_RUNNING or CT_RESOLVE_STARTED:
            return
        CT_RESOLVE_STARTED = True
        CT_RESOLVE_RUNNING = True
    ensure_cardtrader_map()
    try:
        for row in q("select card_id, nome, set_nome, numero, lang from carte group by card_id, lang"):
            if card_id := row["card_id"]:
                cardtrader_resolve(card_id, row["nome"], row["set_nome"], row["numero"], row["lang"])
    finally:
        with CT_RESOLVE_LOCK:
            CT_RESOLVE_RUNNING = False


def cardtrader_post(path, payload):
    token = cardtrader_key()
    if not token:
        raise RuntimeError("Token CardTrader non configurato")
    import urllib.request
    req = urllib.request.Request(
        "https://api.cardtrader.com/api/v2" + path,
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.loads(res.read().decode())
    except Exception as e:
        raise RuntimeError("CardTrader: richiesta non riuscita") from e


CT_PRICE_CACHE = {}


def cardtrader_get(path):
    token = cardtrader_key()
    if not token:
        raise RuntimeError("Token CardTrader non configurato")
    import urllib.request
    req = urllib.request.Request(
        "https://api.cardtrader.com/api/v2" + path,
        headers={"Authorization": "Bearer " + token},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.loads(res.read().decode())
    except Exception as e:
        raise RuntimeError("CardTrader: prezzo non disponibile") from e


def cardtrader_recommended(blueprint_id):
    cached = CT_PRICE_CACHE.get(blueprint_id)
    if cached and time.time() - cached[0] < 600:
        return cached[1]
    try:
        data = cardtrader_get("/marketplace/products?blueprint_id=" + str(int(blueprint_id)))
        if isinstance(data, list):
            products = data
        elif isinstance(data, dict):
            products = data.get(str(int(blueprint_id)), data.get("products", []))
        else:
            products = []
        prices = []
        for product in products:
            price = product.get("price")
            if isinstance(price, dict):
                currency = price.get("currency")
                if currency and currency != "EUR":
                    continue
                if price.get("cents") is not None:
                    price = float(price["cents"]) / 100
                else:
                    price = price.get("value") or price.get("amount")
            if isinstance(price, (int, float)) and price > 0:
                prices.append(float(price))
        value = min(prices) if prices else None
    except RuntimeError:
        value = None
    CT_PRICE_CACHE[blueprint_id] = (time.time(), value)
    return value


def cardtrader_properties(blueprint_id, lang, condiz, fin):
    """Build CardTrader's editable properties for the selected copy."""
    info = cardtrader_info().get("blueprints", {}).get(str(int(blueprint_id)), {})
    allowed = info.get("props") or {}
    condition = CT_COND.get(condiz) or condiz
    accepted = allowed.get("condition") or []
    if accepted and condition not in accepted:
        raise RuntimeError(f"Condizione CardTrader non disponibile: {condition}")
    language = lang.lower()
    language_key = next((key for key in allowed if key.endswith("_language")), "pokemon_language")
    accepted = allowed.get(language_key) or []
    if accepted and language not in accepted:
        raise RuntimeError(f"Lingua CardTrader non disponibile: {language}")
    out = {"condition": condition, language_key: language}
    reverse_key = next((key for key in allowed if "reverse" in key.lower()), None)
    foil_key = next((key for key in allowed if key.lower() == "foil"), None)
    if reverse_key:
        out[reverse_key] = fin == "R"
    if foil_key:
        out[foil_key] = fin == "H"
    return out


SETS = {}


def costruisci_sets():
    global SETS
    d = {}
    for m in M.meta:
        s = d.setdefault(sid(m["id"]), {"id": sid(m["id"]), "names": {}, "langs": set()})
        s["langs"].add(m["lang"])
        s["names"][m["lang"]] = m["set"]
        s.setdefault("n", {})
        s["n"][m["lang"]] = s["n"].get(m["lang"], 0) + 1
    SETS = d


costruisci_sets()


def db():
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("pragma journal_mode=WAL")      # niente fsync a ogni scrittura: sul disco del NAS fa una grossa differenza
    c.execute("pragma synchronous=NORMAL")
    c.execute("create table if not exists carte(id integer primary key autoincrement, ts text, card_id text,"
              " nome text, set_nome text, numero text, lang text, valore real, valuta text, stato text)")
    cols = {r[1] for r in c.execute("pragma table_info(carte)")}
    for col, t in (("rarita", "text"), ("qta", "integer default 1"), ("condiz", "text default 'NM'"), ("fin", "text default ''")):
        if col not in cols:
            c.execute(f"alter table carte add column {col} {t}")
    c.execute("create table if not exists prezzi(card_id text, giorno text, valore real, valuta text,"
              " primary key(card_id, giorno))")
    c.execute("create table if not exists jlink(card_id text primary key, jid text, ts text)")
    c.execute("create table if not exists jprezzi(card_id text, cond text, giorno text, valore real, primary key(card_id, cond, giorno))")
    c.execute("create table if not exists jp2(card_id text, fin text, cond text, giorno text, valore real, primary key(card_id, fin, cond, giorno))")
    c.execute("create table if not exists jfin(card_id text, fin text, primary key(card_id, fin))")
    c.execute("create table if not exists setinfo(sid text, lang text, nome text, logo text, totale integer, primary key(sid, lang))")
    c.execute("create table if not exists sealed(id integer primary key autoincrement, ts text, blueprint_id integer, exp_id integer,"
              " nome text, set_nome text, categoria text, lang text, qta integer default 1, img_url text)")
    c.execute("create unique index if not exists sealed_bp_lang on sealed(blueprint_id, lang)")
    c.execute("create table if not exists sealed_prezzi(blueprint_id integer, lang text, giorno text, minimo real, mediana real,"
              " offerte integer, primary key(blueprint_id, lang, giorno))")
    c.execute("create table if not exists correzioni(id integer primary key autoincrement, ts text, proposta text, scelta text,"
              " lang text, esatta integer, pos integer, stato text, punti integer)")
    return c


def q(sql, a=(), w=False):
    c = db()
    try:
        cur = c.execute(sql, a)
        if w:
            c.commit()
            return cur.lastrowid
        return [dict(x) for x in cur.fetchall()]
    finally:
        c.close()


def q_molti(sql, rows):
    """Molte righe in una sola transazione (prima: una scrittura e un commit per riga)."""
    if not rows:
        return
    c = db()
    try:
        c.executemany(sql, rows)
        c.commit()
    finally:
        c.close()


def dettagli(cid, lang="en"):
    d = {}
    for l in (["en"] if lang in ("en", "it") else [lang, "en"]):
        try:
            r = ps.requests.get(f"{ps.BASE}/{l}/cards/{cid}", timeout=30)
            if r.ok:
                d = r.json()
                break
        except Exception:
            pass
    p = d.get("pricing") or {}
    cm = p.get("cardmarket") or {}
    val, valuta = None, ""
    for k in ("trend", "avg", "avg30"):
        if cm.get(k) is not None:
            val, valuta = cm[k], "EUR"
            break
    if val is None:
        for t in (p.get("tcgplayer") or {}).values():
            if isinstance(t, dict) and t.get("marketPrice"):
                val, valuta = t["marketPrice"], "USD"
                break
    return {"rarita": d.get("rarity") or "N/D", "valore": val, "valuta": valuta, "cm": cm}


def punto(cid, val, valuta, cm=None):
    oggi = dt.date.today()
    if cm and valuta == "EUR":    # primi punti dello storico dalle medie Cardmarket
        for k, g in (("avg30", 30), ("avg7", 7), ("avg1", 1)):
            if cm.get(k) is not None:
                q("insert or ignore into prezzi values(?,?,?,?)",
                  (cid, (oggi - dt.timedelta(g)).isoformat(), cm[k], "EUR"), True)
    if val is not None:
        q("insert or replace into prezzi values(?,?,?,?)", (cid, oggi.isoformat(), val, valuta), True)


JT = "https://api.justtcg.com/v1/cards"
CMAP = {"NM": "Near Mint", "LP": "Lightly Played", "MP": "Moderately Played", "HP": "Heavily Played", "DMG": "Damaged"}
PRINT = ("Normal", "Holofoil", "Reverse Holofoil")
FIN = ("S", "H", "R")      # Standard, Holo, Reverse Holo


def jt_key():
    try:
        return KEYF.read_text().strip() or None
    except Exception:
        return os.environ.get("JUSTTCG_API_KEY") or None


JTLOG = collections.deque(maxlen=80)
JTL = threading.Lock()
JTT = [0.0]


def jtl(msg):
    s = time.strftime("%H:%M:%S ") + str(msg)
    JTLOG.append(s)
    print("justtcg:", s, flush=True)


def jt_get(params=None, body=None, url=None):
    k = jt_key()
    if not k:
        return None
    for tentativo in range(2):
        with JTL:                                   # piano gratuito: circa 10 richieste al minuto
            time.sleep(max(0, 6.5 - (time.time() - JTT[0])))
            try:
                r = ps.requests.request("POST" if body is not None else "GET", url or JT, params=params, json=body,
                                        headers={"X-API-Key": k}, timeout=30)
            except Exception as e:
                jtl(f"errore di rete: {e}")
                return None
            finally:
                JTT[0] = time.time()
        if r.ok:
            return r.json().get("data") or []
        jtl(f"risposta {r.status_code}: {r.text[:200]}")
        if r.status_code == 429 and tentativo == 0:
            time.sleep(40)                          # troppe richieste: aspetto e riprovo una volta
            continue
        return None
    return None


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


JT_SETS = "https://api.justtcg.com/v1/sets"
JSETS = {"t": 0.0, "d": []}
JTDBG = {}


def numn(s):
    """Numero di collezione normalizzato: '023/128' -> '23', 'TG01/TG30' -> 'TG1', 'SV-P 005' -> 'SVP5'."""
    s = re.sub(r"[^A-Z0-9/]", "", str(s or "").upper()).split("/")[0]
    return re.sub(r"(?<![0-9])0+(?=[0-9])", "", s) or "0"


def jt_sets():
    """Elenco dei set Pokemon di JustTCG (una richiesta, in cache per 24 ore)."""
    if JSETS["d"] and time.time() - JSETS["t"] < 86400:
        return JSETS["d"]
    d = jt_get({"game": "pokemon"}, url=JT_SETS)
    if d:
        JSETS["d"], JSETS["t"] = d, time.time()
    return JSETS["d"]


def jt_collega(cid, lang, forza=False):
    """Cerca la carta su JustTCG (nome inglese + numero + set) e salva il collegamento; i fallimenti si ritentano dopo 3 giorni."""
    r = q("select jid, ts from jlink where card_id=?", (cid,))
    if r and not forza and (r[0]["jid"] or r[0]["ts"] >= (dt.date.today() - dt.timedelta(3)).isoformat()):
        return r[0]["jid"]
    if not jt_key():
        return None
    m = next((x for x in M.meta if x["id"] == cid and x["lang"] == "en"), None)
    if m:
        nome, num, sset = m["name"], m["number"], m["set"]
    else:      # carta senza equivalente inglese nell'indice: chiedo a TCGdex la scheda inglese
        d = ps.get_json(f"{ps.BASE}/en/cards/{cid}", tries=2, timeout=30) or {}
        m2 = next((x for x in M.meta if x["id"] == cid), {})
        nome, num = d.get("name") or m2.get("name"), d.get("localId") or m2.get("number")
        sset = (d.get("set") or {}).get("name") or m2.get("set")
    if not nome:
        return None
    n = numn(num)
    tok = set(norm(sset).split())

    def cod(s):      # "ME04" e "me04" -> stesso codice; "SWSH08" e "swsh8" idem
        return {re.sub(r"^([a-z]+)0+(?=\d)", r"\1", w) for w in norm(s).split()}

    sc = cod(sid(cid))

    def punti_nome(nm, extra=""):
        if sc & (cod(nm) | cod(extra)):
            return 1.0                       # il codice del set (es. me04) coincide: corrispondenza sicura
        t = set(norm(nm).split())
        return len(tok & t) / max(len(tok | t), 1) if tok else 0

    def punti(c):
        return punti_nome(c.get("set_name"), (c.get("set") or "").replace("-", " "))

    def cerca(extra):
        """Restituisce (candidate, esaustiva): esaustiva = ho letto tutti i risultati per quel nome (o per quel set)."""
        out, tutta = [], False
        for off in (0, 20, 40):      # guardo altre pagine solo se la carta giusta non e' ancora comparsa
            data = jt_get(dict({"game": "pokemon", "q": nome, "limit": 20, "offset": off}, **extra))
            if data is None:
                return None, False
            out += [c for c in data if norm(nome) in norm(c.get("name")) and numn(c.get("number")) == n]
            if len(data) < 20:
                tutta = True
                break
            if any(punti(c) >= 0.4 for c in out):
                break
        return out, tutta

    # 1) se riconosco il set tra quelli di JustTCG cerco solo li' (con nomi molto comuni, come Pikachu, la ricerca globale non basta)
    js, bs = None, 0
    for s in jt_sets():
        p = punti_nome(s.get("name"), str(s.get("id") or "").replace("-", " "))
        if p > bs:
            js, bs = s, p
    cands, tutta = cerca({"set": js["id"]}) if js and bs >= 0.5 else (None, False)
    if not cands:      # set non riconosciuto, parametro non accettato o nessun risultato: ricerca globale per nome
        cands, tutta = cerca({})
        if cands is None:
            return None              # errore di rete, di chiave o troppe richieste: non salvo nulla e riprovo piu' tardi
    cands.sort(key=lambda c: (punti(c), norm(c.get("name")) == norm(nome)), reverse=True)
    # una sola candidata senza conferma del set si accetta solo se ho letto TUTTI i risultati per quel nome (altrimenti, con nomi comuni, rischio la carta sbagliata)
    best = cands[0] if cands and (punti(cands[0]) >= 0.4 or (len(cands) == 1 and tutta)) else None
    trovate = [(c.get("name"), c.get("set_name"), c.get("number")) for c in cands[:5]]
    JTDBG[cid] = (f"{nome} n.{n} [{sset}] -> " + (f"collegata a {best.get('id')}" if best else f"nessuna corrispondenza; trovate: {trovate}"))
    if not best:
        print("justtcg: nessun collegamento per", cid, "|", nome, "|", sset, "|", n, "| trovate:", trovate, flush=True)
    q("insert or replace into jlink values(?,?,?)", (cid, best and best.get("id"), dt.date.today().isoformat()), True)
    return best and best.get("id")


q("delete from jlink where jid is null", (), True)      # ad ogni avvio ritenta i collegamenti falliti
q("insert or ignore into jp2 select card_id, '', cond, giorno, valore from jprezzi", (), True)      # vecchi prezzi: finitura non indicata


def fin_di(p):
    """Finitura di una variante JustTCG: S = Standard, H = Holo, R = Reverse Holo (le 1st Edition si ignorano)."""
    p = (p or "").lower()
    if "1st" in p:
        return None
    if "reverse" in p:
        return "R"
    if "holo" in p:
        return "H"
    return "S" if p in ("normal", "unlimited") else None


def jt_salva(cid, c, combos):
    """Salva il prezzo di oggi e lo storico per ogni (condizione, finitura) posseduta. Restituisce quanti prezzi ha salvato."""
    oggi, storico, oggi_s, vari = [], [], dt.date.today().isoformat(), c.get("variants", [])
    q_molti("insert or ignore into jfin values(?,?)", [(cid, f) for f in {fin_di(v.get("printing")) for v in vari} if f])
    for cd, fin in combos:
        vs = [v for v in vari if v.get("condition") == CMAP.get(cd) and v.get("price") is not None and (not fin or fin_di(v.get("printing")) == fin)]
        vs.sort(key=lambda v: PRINT.index(v["printing"]) if v.get("printing") in PRINT else 9)
        if not vs:
            jtl(f"{cid} {cd}{' ' + fin if fin else ''}: JustTCG non ha un prezzo per questa combinazione")
            continue
        v = vs[0]
        oggi.append((cid, fin, cd, oggi_s, v["price"]))
        for h in v.get("priceHistory") or []:
            if h.get("p") is not None and h.get("t"):
                g = dt.datetime.fromtimestamp(h["t"], dt.timezone.utc).date().isoformat()
                storico.append((cid, fin, cd, g, h["p"]))
    q_molti("insert or ignore into jp2 values(?,?,?,?,?)", storico)
    q_molti("insert or replace into jp2 values(?,?,?,?,?)", oggi)      # il prezzo di oggi vince sullo storico
    return len(oggi)


def combos_di(cid):
    return [(r["c"], r["f"]) for r in q("select distinct coalesce(condiz,'NM') c, coalesce(fin,'') f from carte where card_id=?", (cid,))]


def jt_card(cid, lang):
    try:
        jid = jt_collega(cid, lang)
        if not jid:
            jtl(f"{cid}: nessun collegamento")
            return
        data = jt_get({"cardId": jid, "include_price_history": "true", "priceHistoryDuration": "90d"}) or jt_get({"cardId": jid})
        if not data:
            jtl(f"{cid}: JustTCG non ha restituito la carta")
            return
        jtl(f"{cid}: salvati {jt_salva(cid, data[0], combos_di(cid))} prezzi")
    except Exception:
        jtl("ERRORE " + traceback.format_exc()[-400:])


def jt_tutte():
    """Aggiornamento giornaliero: carte raggruppate a 20 per richiesta (limite del piano gratuito)."""
    if not jt_key():
        jtl("chiave non impostata")
        return
    lk = []
    for r in q("select card_id, min(lang) lang from carte group by card_id"):
        try:
            j = jt_collega(r["card_id"], r["lang"])
        except Exception:
            jtl("ERRORE collegamento " + traceback.format_exc()[-400:])
            continue
        if j:
            lk.append((r["card_id"], j))
    jtl(f"aggiornamento: {len(lk)} carte collegate")
    salvati = 0
    for i in range(0, len(lk), 20):
        grp = lk[i:i + 20]
        data = jt_get({"include_price_history": "true", "priceHistoryDuration": "7d"}, [{"cardId": j} for _, j in grp])
        if data is None:
            jtl("richiesta a gruppi fallita")
            continue
        by = {c.get("id"): c for c in data}
        for cid, j in grp:
            if j in by:
                salvati += jt_salva(cid, by[j], combos_di(cid))
            else:
                jtl(f"{cid}: assente nella risposta")
    jtl(f"aggiornamento finito: {salvati} prezzi salvati")


def aggiorna():
    for r in q("select card_id, min(lang) lang from carte group by card_id"):
        x = dettagli(r["card_id"], r["lang"])
        if x["valore"] is not None:
            n = q("select count(*) c from prezzi where card_id=?", (r["card_id"],))[0]["c"]
            punto(r["card_id"], x["valore"], x["valuta"], x["cm"] if n < 2 else None)
        q("update carte set valore=coalesce(?,valore), valuta=case when ? is null then valuta else ? end, rarita=? where card_id=?",
          (x["valore"], x["valore"], x["valuta"], x["rarita"], r["card_id"]), True)
        time.sleep(0.3)
    try:
        jt_tutte()
    except Exception as e:
        print("justtcg:", e)
    MARK.write_text(dt.date.today().isoformat())


BK = pathlib.Path("pokedata/backup")


def backup(force=False):
    """Copia coerente del database in pokedata/backup (una al giorno, ultime 14)."""
    BK.mkdir(parents=True, exist_ok=True)
    f = BK / f"collezione-{dt.date.today().isoformat()}.db"
    if f.exists():
        if not force:
            return
        f.unlink()
    s, d = sqlite3.connect(DB), sqlite3.connect(f)
    try:
        s.backup(d)
    finally:
        d.close()
        s.close()
    for old in sorted(BK.glob("collezione-*.db"))[:-14]:
        old.unlink()


def _bk():
    try:
        backup()
    except Exception as e:
        print("backup:", e)


def ciclo():
    while True:
        try:
            _bk()
            sets_mancanti()
            oggi = dt.date.today().isoformat()
            vecchio = not MARK.exists() or MARK.read_text().strip() != oggi
            manca_rar = q("select 1 from carte where rarita is null limit 1")
            if (vecchio and q("select 1 from carte limit 1")) or manca_rar:
                aggiorna()
        except Exception as e:
            print("aggiornamento prezzi:", e)
        time.sleep(3600)


threading.Thread(target=ciclo, daemon=True).start()


MARK_IDX = pathlib.Path("pokedata/ultimo_indice.txt")
INFO = {"nuove": 0, "in_corso": False}


def aggiorna_carte():
    if INFO["in_corso"]:
        return
    INFO["in_corso"] = True
    try:
        tot = 0
        for lang in sorted({m["lang"] for m in M.meta}):
            try:
                tot += ps.aggiorna_indice(M, lang, lock)
            except Exception as e:
                print("aggiornamento carte", lang, e)
        if tot:
            with lock:
                M.carica()
            costruisci_sets()
        try:
            aggiorna_noimg()
        except Exception as e:
            print("carte senza immagine:", e)
        INFO["nuove"] = tot
        MARK_IDX.write_text(dt.date.today().isoformat())
    finally:
        INFO["in_corso"] = False


def ciclo_carte():
    while True:
        try:
            if not MARK_IDX.exists():
                MARK_IDX.write_text(dt.date.today().isoformat())    # indice appena creato: prima verifica tra 7 giorni
            elif (dt.date.today() - dt.date.fromisoformat(MARK_IDX.read_text().strip())).days >= 7:
                aggiorna_carte()
        except Exception as e:
            print("ciclo carte:", e)
        time.sleep(6 * 3600)


threading.Thread(target=ciclo_carte, daemon=True).start()


@app.post("/api/aggiorna-carte")
def aggiorna_carte_ora():
    threading.Thread(target=aggiorna_carte, daemon=True).start()
    return jsonify(ok=True)


@app.get("/api/stato")
def stato_info():
    rd = lambda f: f.read_text().strip() if f.exists() else ""
    bk = sorted(BK.glob("collezione-*.db"))
    c = q("select count(*) n, coalesce(sum(esatta),0) e from correzioni")[0]
    return jsonify(carte=rd(MARK_IDX), prezzi=rd(MARK), nuove=INFO["nuove"], in_corso=INFO["in_corso"], totale=len(M.meta),
                   backup=bk[-1].stem[-10:] if bk else "", ric_tot=c["n"], ric_ok=c["e"], versione="v16.2")


SETIMG = pathlib.Path("pokedata/setimg")
SET_TENT = {}
SET_LOCK = threading.Lock()
SETERR = collections.deque(maxlen=20)


def _set_file(s, lang):
    return SETIMG / (re.sub(r"[^A-Za-z0-9._+-]", "_", f"{lang}_{s}") + ".png")


def _scarica_logo(d, s, lang, f):
    """Cerca il logo del set e lo salva in locale. Il campo 'logo' dell'API spesso e' vuoto per i set nuovi anche se il file
    esiste: in quel caso si ricava l'indirizzo dalle immagini delle carte o dalla serie (es. assets.tcgdex.net/it/me/30th/logo.png)."""
    def norm_url(u):
        return u if not u or u.lower().endswith((".png", ".webp", ".jpg")) else u + ".png"
    base = None
    for c in d.get("cards") or []:
        if c.get("image"):
            base = c["image"].rsplit("/", 1)[0]
            break
    if not base and (d.get("serie") or {}).get("id"):
        base = f"https://assets.tcgdex.net/{lang}/{d['serie']['id']}/{s}"
    cand = [norm_url(d.get("logo"))]
    if base:
        cand += [base + "/logo.png"]
        if f"/{lang}/" in base and lang != "en":
            cand += [base.replace(f"/{lang}/", "/en/", 1) + "/logo.png"]
    cand += [norm_url(d.get("symbol"))]
    if base:
        cand += [base + "/symbol.png"]
    for u in dict.fromkeys(x for x in cand if x):
        try:
            x = ps.requests.get(u, timeout=30)
        except Exception as e:
            SETERR.append(f"{lang}/{s}: {u}: {e.__class__.__name__}")
            continue
        if x.ok and len(x.content) > 300 and "image" in ((getattr(x, "headers", None) or {}).get("content-type") or "image"):
            SETIMG.mkdir(parents=True, exist_ok=True)
            f.write_bytes(x.content)
            return u
    SETERR.append(f"{lang}/{s}: nessuna immagine trovata (provati {len(cand)} indirizzi)")
    return ""


def meta_set(s, lang):
    """Nome, numero totale di carte e immagine (logo o simbolo) del set da TCGdex. L'immagine viene scaricata in locale."""
    try:
        r = q("select totale, logo from setinfo where sid=? and lang=?", (s, lang))
        f = _set_file(s, lang)
        if r and r[0]["totale"] is not None and (f.exists() or r[0]["logo"] == "-2"):
            return
        if time.time() - SET_TENT.get((s, lang), 0) < 120:      # non insiste piu' di una volta ogni 2 minuti
            return
        SET_TENT[(s, lang)] = time.time()
        d = ps.get_json(f"{ps.BASE}/{lang}/sets/{urllib.parse.quote(s, safe='')}", tries=2, timeout=30) or {}
        if not d:
            SETERR.append(f"{lang}/{s}: TCGdex non ha risposto")
            return
        cc = d.get("cardCount") or {}
        url = ""
        if not f.exists():
            url = _scarica_logo(d, s, lang, f)
        else:
            url = (r[0]["logo"] if r else "") or "locale"
        q("insert or replace into setinfo values(?,?,?,?,?)",
          (s, lang, d.get("name"), url or "-2", cc.get("total") or cc.get("official")), True)
    except Exception as e:
        SETERR.append(f"{lang}/{s}: {e.__class__.__name__}: {e}")
        print("meta_set", s, lang, e)


def sets_mancanti():
    """Riprova le informazioni dei set in collezione che mancano (totale o immagine)."""
    for r in q("select distinct card_id, lang from carte"):
        meta_set(sid(r["card_id"]), r["lang"])


@app.get("/setimg/<lang>/<s>")
def setimg(lang, s):
    f = _set_file(s, lang)
    if not f.exists():
        return Response(status=404)
    return send_file(f, max_age=86400)


@app.get("/api/set")
def set_list():
    g = {}
    for r in q("select card_id, lang, set_nome, qta, numero from carte"):
        k = (sid(r["card_id"]), r["lang"])
        e = g.setdefault(k, {"nome": r["set_nome"], "ids": set(), "copie": 0, "prima": None})
        e["ids"].add(r["card_id"])
        e["copie"] += r["qta"] or 1
        chiave = (len(str(r["numero"] or "")), str(r["numero"] or ""))
        if e["prima"] is None or chiave < e["prima"][0]:
            e["prima"] = (chiave, r["card_id"])
    info = {(x["sid"], x["lang"]): x for x in q("select * from setinfo")}
    conta = collections.Counter((sid(m["id"]), m["lang"]) for m in M.meta)
    conta.update((sid(m["id"]), m["lang"]) for m in getattr(M, "noimg", []))
    out = []
    for k, e in g.items():
        i = info.get(k, {})
        tot, approx = i.get("totale"), False
        if tot is None and conta.get(k):          # totale ufficiale non ancora scaricato: si usa l'elenco carte del NAS
            tot, approx = conta[k], True
        out.append({"sid": k[0], "lang": k[1], "nome": i.get("nome") or e["nome"], "possedute": len(e["ids"]), "totale": tot,
                    "approx": approx, "copie": e["copie"],
                    "logo": f"/setimg/{k[1]}/{k[0]}" if _set_file(k[0], k[1]).exists() else "",
                    "img": f"/img/{k[1]}/{e['prima'][1]}" if e["prima"] else ""})      # senza logo: una carta posseduta del set
    manca = [k for k in g if info.get(k, {}).get("totale") is None or (not _set_file(*k).exists() and info.get(k, {}).get("logo") != "-2")]
    if manca and SET_LOCK.acquire(blocking=False):
        def lavora():
            try:
                for k in manca:
                    meta_set(*k)
            finally:
                SET_LOCK.release()
        threading.Thread(target=lavora, daemon=True).start()
    return jsonify(sorted(out, key=lambda x: (x["nome"] or "").lower()))


@app.get("/api/mancanti")
def mancanti_list():
    """Restituisce le carte mancanti dei soli set gia' presenti in collezione."""
    possedute = collections.defaultdict(set)
    for r in q("select card_id, lang from carte"):
        possedute[(sid(r["card_id"]), r["lang"])].add(r["card_id"])

    info = {(x["sid"], x["lang"]): x for x in q("select * from setinfo")}
    catalogo = collections.defaultdict(dict)
    for m in list(M.meta) + list(getattr(M, "noimg", [])):
        k = (sid(m["id"]), m["lang"])
        if k in possedute:
            catalogo[k].setdefault(m["id"], m)

    out = []
    for k, owned in possedute.items():
        cards = [m for cid, m in catalogo[k].items() if cid not in owned]
        if not cards:
            continue
        i = info.get(k, {})
        cards.sort(key=lambda m: (len(str(m.get("number") or "")), str(m.get("number") or "")))
        out.append({
            "sid": k[0],
            "lang": k[1],
            "nome": i.get("nome") or cards[0].get("set") or k[0],
            "possedute": len(owned),
            "totale": len(owned) + len(catalogo[k]),
            "mancanti": len(cards),
            "logo": f"/setimg/{k[1]}/{k[0]}" if _set_file(k[0], k[1]).exists() else "",
            "cards": [{
                "card_id": m["id"],
                "nome": m.get("name") or m["id"],
                "set": m.get("set") or i.get("nome") or k[0],
                "numero": m.get("number") or "",
                "lang": m["lang"],
                "rarita": m.get("rarity") or "N/D",
            } for m in cards],
        })
    return jsonify(sorted(out, key=lambda x: (x["nome"] or "").lower()))


def aggiorna_noimg():
    """Elenco delle carte che TCGdex ha SENZA immagine (per esempio le promo MEP): cercabili per nome, non riconoscibili."""
    for lang in sorted({m["lang"] for m in M.meta} | {"it", "en"}):
        sets = ps.get_json(f"{ps.BASE}/{lang}/sets", tries=3) or []
        senza, ok = [], bool(sets)
        for s in sets:
            d = ps.get_json(f"{ps.BASE}/{lang}/sets/{urllib.parse.quote(s['id'], safe='')}", tries=3)
            if d is None:
                ok = False
                continue
            for c in d.get("cards") or []:
                if not c.get("image"):
                    senza.append({"id": c["id"], "name": c.get("name", ""), "number": c.get("localId", ""),
                                  "set": s.get("name", s["id"]), "lang": lang})
            time.sleep(0.05)
        if ok:      # se un set non ha risposto, si tiene l'elenco precedente
            (ps.DATA / f"noimg_{lang}.json").write_text(json.dumps(senza, ensure_ascii=False), encoding="utf-8")
    carica_noimg()


def carica_noimg():
    ids = {m["id"] + "|" + m["lang"] for m in M.meta}
    out = []
    for f in sorted(ps.DATA.glob("noimg_*.json")):
        try:
            out += [m for m in json.loads(f.read_text(encoding="utf-8")) if m["id"] + "|" + m["lang"] not in ids]
        except Exception:
            pass
    M.noimg = out


carica_noimg()


def _primo_noimg():
    """Al primo avvio genera da solo l'elenco delle carte senza immagine (poi si aggiorna con il resto delle carte)."""
    time.sleep(90)
    try:
        if not list(ps.DATA.glob("noimg_*.json")):
            aggiorna_noimg()
    except Exception as e:
        print("elenco carte senza immagine:", e)


threading.Thread(target=_primo_noimg, daemon=True).start()


@app.post("/api/impara")
def impara():
    """Usa la foto appena scattata come immagine di riferimento di una carta che TCGdex ha senza immagine."""
    cid, lang = request.form.get("card_id", ""), request.form.get("lang", "")
    m = next((x for x in getattr(M, "noimg", []) if x["id"] == cid and x["lang"] == lang), None)
    if not m:      # carta salvata in una lingua in cui TCGdex non la elenca: i dati arrivano dall'app
        nome = request.form.get("nome", "")
        if not (cid and lang and nome):
            return jsonify(errore="dati della carta mancanti"), 400
        if any(x["id"] == cid and x["lang"] == lang for x in M.meta):
            return jsonify(errore="la carta e' gia' nell'indice di questa lingua"), 409
        m = {"id": cid, "name": nome, "number": request.form.get("numero", ""), "set": request.form.get("set", ""), "lang": lang}
    ims = imgs_in()
    if not ims:
        return jsonify(errore="immagine non valida"), 400
    qd = ps.trova_carta(ims[0], SFONDO[0])
    if qd is None:
        return jsonify(errore="carta non rilevata nella foto: riprova con la carta ferma su sfondo scuro"), 422
    card = ps.raddrizza(ims[0], qd)
    from PIL import Image
    p = ps.percorso(m)
    p.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(p), card)
    with lock:
        v = M.model.encode([Image.fromarray(cv2.cvtColor(ps.riduci_riflessi(card), cv2.COLOR_BGR2RGB))], normalize_embeddings=True, convert_to_numpy=True)
    f_emb, f_meta = ps.file_indice(lang)
    fe, fm = ps.DATA / f_emb, ps.DATA / f_meta
    meta = json.loads(fm.read_text(encoding="utf-8")) if fm.exists() else []
    E = np.load(fe) if fe.exists() else np.zeros((0, v.shape[1]), v.dtype)
    meta.append({"id": m["id"], "name": m["name"], "number": m["number"], "set": m["set"], "lang": lang})
    with open(str(fe) + ".tmp", "wb") as fh:
        np.save(fh, np.vstack([E, v]))
    pathlib.Path(str(fm) + ".tmp").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    os.replace(str(fe) + ".tmp", fe)
    os.replace(str(fm) + ".tmp", fm)
    with lock:
        M.carica()
    costruisci_sets()
    carica_noimg()
    M.noimg = [x for x in M.noimg if not (x["id"] == cid and x["lang"] == lang)]
    return jsonify(ok=True)


COND = ("NM", "LP", "MP", "HP", "DMG")


def _sposta(i, cond=None, fin=None):
    """Sposta UNA copia in un'altra condizione e/o finitura (unendola a una riga uguale, se esiste)."""
    r = q("select * from carte where id=?", (i,))
    if not r:
        return False
    r = r[0]
    c0, f0 = (r.get("condiz") or "NM"), (r.get("fin") or "")
    c1, f1 = (cond or c0), (f0 if fin is None else fin)
    if (c1, f1) == (c0, f0):
        return True
    dest = q("select id from carte where card_id=? and lang=? and coalesce(condiz,'NM')=? and coalesce(fin,'')=? and id!=?",
             (r["card_id"], r["lang"], c1, f1, i))
    if (r.get("qta") or 1) > 1:
        q("update carte set qta=qta-1 where id=?", (i,), True)
        if dest:
            q("update carte set qta=coalesce(qta,1)+1 where id=?", (dest[0]["id"],), True)
        else:
            q("insert into carte(ts,card_id,nome,set_nome,numero,lang,valore,valuta,stato,rarita,qta,condiz,fin) "
              "select ts,card_id,nome,set_nome,numero,lang,valore,valuta,stato,rarita,1,?,? from carte where id=?", (c1, f1, i), True)
    elif dest:
        q("update carte set qta=coalesce(qta,1)+1 where id=?", (dest[0]["id"],), True)
        q("delete from carte where id=?", (i,), True)
    else:
        q("update carte set condiz=?, fin=? where id=?", (c1, f1, i), True)
    threading.Thread(target=jt_card, args=(r["card_id"], r["lang"]), daemon=True).start()
    return True


@app.post("/api/condizione/<int:i>")
def condizione(i):
    c = (request.get_json() or {}).get("c")
    if c not in COND or not _sposta(i, cond=c):
        return jsonify(errore="richiesta non valida"), 400
    return jsonify(ok=True)


@app.post("/api/finitura/<int:i>")
def finitura(i):
    f = (request.get_json() or {}).get("f")
    if f not in FIN or not _sposta(i, fin=f):
        return jsonify(errore="richiesta non valida"), 400
    return jsonify(ok=True)


@app.get("/api/correzioni")
def correzioni():
    t = q("select count(*) n, coalesce(sum(esatta),0) e from correzioni")[0]
    err = q("select proposta, scelta, count(*) n from correzioni where esatta=0 group by proposta, scelta order by n desc limit 20")
    return jsonify(totale=t["n"], esatte=t["e"], errori=err)


@app.post("/api/backup")
def backup_ora():
    backup(True)
    return jsonify(ok=True)


def imgs_in():
    out = []
    for f in request.files.getlist("foto")[:3]:
        im = cv2.imdecode(np.frombuffer(f.read(), np.uint8), cv2.IMREAD_COLOR)
        if im is not None:
            s = 1280 / max(im.shape[:2])
            out.append(cv2.resize(im, None, fx=s, fy=s) if s < 1 else im)
    return out


def fondi(tutti):
    """Unisce i risultati di piu' fotogrammi: medie di punti SIFT e similarita', piu' accordo sul primo posto."""
    n = len(tutti)
    acc = {}
    for top in tutti:
        for r in top:
            a = acc.setdefault(r["m"]["id"], {"m": r["m"], "inl": 0.0, "sim": 0.0, "primo": 0})
            a["inl"] += r["inl"] / n
            a["sim"] += r["sim"] / n
        acc[top[0]["m"]["id"]]["primo"] += 1
    v = list(acc.values())
    v.sort(key=(lambda a: (a["inl"], a["sim"])) if max(a["inl"] for a in v) >= 10 else (lambda a: a["sim"]), reverse=True)
    st = stato_di(v)
    if n > 1 and v[0]["primo"] * 2 <= n:
        st = "verifica"
    return v[:6], st


def stato_di(top):
    b = top[0]
    s = top[1] if len(top) > 1 else {"inl": 0, "sim": 0}
    if b["inl"] >= 15 and b["inl"] >= 1.5 * max(s["inl"], 1):
        return "ok"
    if b["inl"] < 10 and b["sim"] >= ps.SOGLIA_SCORE and b["sim"] - s["sim"] >= ps.SOGLIA_MARGINE:
        return "ok"
    return "verifica"


def cand(m, inl=0, sim=0):
    return {"card_id": m["id"], "nome": m["name"], "set": m["set"], "numero": m["number"],
            "lang": m["lang"], "punti": int(round(inl)), "sim": round(float(sim), 3)}


def img_in():
    f = request.files.get("foto")
    im = cv2.imdecode(np.frombuffer(f.read(), np.uint8), cv2.IMREAD_COLOR) if f else None
    if im is None:
        return None
    s = 1280 / max(im.shape[:2])
    return cv2.resize(im, None, fx=s, fy=s) if s < 1 else im


@app.get("/")
def home():
    return send_from_directory("static", "index.html")


@app.get("/img/<lang>/<cid>")
def img(lang, cid):
    for l in dict.fromkeys([secure_filename(lang), "en", "it", "fr", "de", "es"]):      # se manca nella lingua, si mostra la stessa carta di un'altra lingua
        p = ps.percorso({"id": secure_filename(cid), "lang": l})
        if p.exists():
            return send_file(p, max_age=86400 if l == secure_filename(lang) else 300)
    import html
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 250 350"><rect x="2" y="2" width="246" height="346" rx="16" fill="#1d1d22" stroke="#58585e" stroke-width="3"/>'
           '<text x="125" y="165" fill="#a0a0a8" font-family="sans-serif" font-size="18" text-anchor="middle">Senza immagine</text>'
           f'<text x="125" y="195" fill="#76767c" font-family="sans-serif" font-size="14" text-anchor="middle">{html.escape(secure_filename(cid))}</text></svg>')
    return Response(svg, mimetype="image/svg+xml", headers={"Cache-Control": "max-age=300"})      # segnaposto per le carte senza immagine


@app.get("/api/filtri")
def filtri():
    langs = sorted({m["lang"] for m in M.meta})
    return jsonify(langs=[{"id": l, "nome": LANGS.get(l, l.upper())} for l in langs],
                   sets=[{"id": s["id"], "names": s["names"], "langs": sorted(s["langs"]), "n": s["n"]} for s in SETS.values()])


SFONDO = [None]


@app.errorhandler(Exception)
def errore_json(e):
    """Per le chiamate /api rispondo sempre in JSON (e annoto l'errore nel log), cosi' la pagina mostra la causa vera."""
    from werkzeug.exceptions import HTTPException
    if not request.path.startswith("/api/"):
        if isinstance(e, HTTPException):
            return e
        raise e
    codice = e.code if isinstance(e, HTTPException) else 500
    if codice >= 500:
        jtl(f"ERRORE {request.path}: " + traceback.format_exc()[-400:])
    return jsonify(errore=f"{type(e).__name__}: {e}"[:200]), codice


@app.route("/api/sfondo", methods=["POST", "DELETE"])
def sfondo():
    if request.method == "DELETE":
        SFONDO[0] = None
        return jsonify(ok=True)
    im = img_in()
    if im is None:
        return jsonify(errore="immagine non valida"), 400
    SFONDO[0] = im
    return jsonify(ok=True)


@app.post("/api/rileva")
def rileva():
    im = img_in()
    if im is None:
        return jsonify(errore="immagine non valida"), 400
    qd = ps.trova_carta(im, SFONDO[0])
    h, w = im.shape[:2]
    firma = None
    if qd is not None:      # miniatura 16x22 della carta: serve a capire se e' arrivata una carta diversa
        firma = cv2.resize(cv2.cvtColor(ps.raddrizza(im, qd), cv2.COLOR_BGR2GRAY), (16, 22),
                           interpolation=cv2.INTER_AREA).flatten().tolist()
    return jsonify(trovata=qd is not None, firma=firma,
                   quad=(qd / np.float32([w, h])).tolist() if qd is not None else None)


def aggiungi_fins(lista):
    """Per ogni candidata, le finiture che esistono su JustTCG (se la carta e' gia' stata collegata)."""
    ids = [c["card_id"] for c in lista]
    d = {}
    if ids:
        for r in q("select card_id, fin from jfin where card_id in (%s)" % ",".join("?" * len(ids)), tuple(ids)):
            d.setdefault(r["card_id"], []).append(r["fin"])
    for c in lista:
        c["fins"] = [f for f in FIN if f in d.get(c["card_id"], [])]
    return lista


@app.post("/api/scan")
def scan():
    t0 = time.time()
    ims = imgs_in()
    if not ims:
        return jsonify(errore="immagine non valida"), 400
    lang, s_ = request.form.get("lang") or None, request.form.get("set") or None
    tutti, trovata = [], False
    for im in ims:
        qd = ps.trova_carta(im, SFONDO[0])
        trovata = trovata or qd is not None
        card = ps.raddrizza(im, qd) if qd is not None else cv2.resize(im, (ps.W, ps.H))
        card = ps.riduci_riflessi(card)
        with lock:
            top = M.match(card, lang, s_, 6)
        if top:
            tutti.append(top)
            if len(top) > 1 and top[0]["inl"] >= 25 and top[0]["inl"] >= 2 * max(top[1]["inl"], 1):
                break      # risultato netto al primo fotogramma: inutile elaborare gli altri
    if not tutti:
        return jsonify(errore="nessuna carta con questi filtri"), 404
    top, st = fondi(tutti)
    jtl(f"riconoscimento: {int((time.time() - t0) * 1000)} ms totali, {len(tutti)}/{len(ims)} fotogrammi elaborati | {getattr(M, 'ult', {})}")
    return jsonify(trovata=trovata, stato=st, frames=len(tutti), candidati=aggiungi_fins([cand(r["m"], r["inl"], r["sim"]) for r in top]))


@app.get("/api/cerca")
def cerca():
    t = request.args.get("q", "").strip().lower()
    lang, s = request.args.get("lang"), request.args.get("set")
    out = []
    if len(t) < 2:
        return jsonify(out)
    toks = t.split()
    num = next((x.lstrip("0") or "0" for x in toks if x.isdigit()), None)       # "zapdos 098" cerca per nome E numero
    nome_q = " ".join(x for x in toks if not x.isdigit()) or t

    def ok(m):
        return nome_q in (m.get("name") or "").lower() and (num is None or str(m.get("number", "")).lstrip("0") == num) \
            and (not s or sid(m["id"]) == s)

    for m in M.meta:
        if ok(m) and (not lang or m["lang"] == lang):
            out.append(cand(m))
            if len(out) >= 30:
                break
    noimg = list(getattr(M, "noimg", []))
    for m in noimg:      # carte senza immagine in TCGdex: solo per nome (poi si possono 'imparare' dalla foto)
        if len(out) >= 40:
            break
        if ok(m) and (not lang or m["lang"] == lang):
            c = cand(m)
            c["senza_img"] = True
            out.append(c)
    if lang:      # carte che TCGdex ha solo in altre lingue (es. promo uscite in italiano ma elencate solo in inglese): salvabili nella lingua scelta
        gia = {m["id"] for m in M.meta if m["lang"] == lang} | {m["id"] for m in noimg if m["lang"] == lang}
        visti = set()
        for senza, lista in ((True, noimg), (False, M.meta)):
            for m in lista:
                if len(out) >= 120:
                    break
                if m["lang"] != lang and m["id"] not in gia and m["id"] not in visti and ok(m):
                    visti.add(m["id"])
                    c = cand(m)
                    c["altra_lingua"] = True
                    if senza:
                        c["senza_img"] = True
                    out.append(c)
    return jsonify(aggiungi_fins(out))


def dopo_salvataggio(cid, lang):
    """Prezzo Cardmarket e rarita' da TCGdex: in background, cosi' il salvataggio risponde subito."""
    try:
        primo = not q("select 1 from prezzi where card_id=?", (cid,))
        x = dettagli(cid, lang)
        if x["valore"] is not None:
            q("update carte set valore=?, valuta=? where card_id=? and lang=?", (x["valore"], x["valuta"], cid, lang), True)
        if x["rarita"] != "N/D":
            q("update carte set rarita=? where card_id=? and lang=?", (x["rarita"], cid, lang), True)
        punto(cid, x["valore"], x["valuta"], x["cm"] if primo else None)
    except Exception:
        jtl("ERRORE dopo salvataggio " + traceback.format_exc()[-300:])


@app.post("/api/salva")
def salva():
    t0 = time.time()
    d = request.get_json()
    cid = d["card_id"]
    cd = d.get("condiz") if d.get("condiz") in COND else "NM"
    fn = d.get("fin") if d.get("fin") in FIN else "S"
    ts = time.strftime("%Y-%m-%d %H:%M")
    r = q("select id from carte where card_id=? and lang=? and coalesce(condiz,'NM')=? and coalesce(fin,'')=?", (cid, d["lang"], cd, fn))
    if r:
        q("update carte set qta=coalesce(qta,1)+1, ts=? where id=?", (ts, r[0]["id"]), True)
    else:
        q("insert into carte(ts,card_id,nome,set_nome,numero,lang,valore,valuta,stato,rarita,qta,condiz,fin) values(?,?,?,?,?,?,?,?,?,?,1,?,?)",
          (ts, cid, d["nome"], d["set"], d["numero"], d["lang"], None, "", d.get("stato", "ok"), "N/D", cd, fn), True)
    qta = q("select qta from carte where card_id=? and lang=? and coalesce(condiz,'NM')=? and coalesce(fin,'')=?", (cid, d["lang"], cd, fn))[0]["qta"]
    if d.get("proposta"):      # registro delle correzioni: la proposta era giusta?
        q("insert into correzioni(ts,proposta,scelta,lang,esatta,pos,stato,punti) values(?,?,?,?,?,?,?,?)",
          (ts, d["proposta"], cid, d["lang"], int(d["proposta"] == cid),
           d.get("pos", 0), d.get("stato", ""), d.get("punti", 0)), True)
    for f, args in (
        (dopo_salvataggio, (cid, d["lang"])),
        (meta_set, (sid(cid), d["lang"])),
        (jt_card, (cid, d["lang"])),
    ):
        threading.Thread(target=f, args=args, daemon=True).start()
    jtl(f"salvataggio {cid}: {int((time.time() - t0) * 1000)} ms")
    return jsonify(qta=qta)


PRZ_CACHE = {}
INV_CMAP = {v: k for k, v in CMAP.items()}


@app.get("/api/prezzo")
def prezzo():
    """Prezzo di una carta SENZA salvarla: TCG (JustTCG, per finitura e condizione, in dollari) e Cardmarket (euro)."""
    cid, lang = request.args.get("card_id", ""), request.args.get("lang", "en")
    if not cid:
        return jsonify(errore="carta mancante"), 400
    x = dettagli(cid, lang)
    cmx = x.get("cm") or {}
    out = {"cm": {k: cmx.get(k) for k in ("trend", "low", "avg7", "avg30") if cmx.get(k) is not None}, "rarita": x.get("rarita"), "tcg": None, "motivo": ""}
    if not jt_key():
        out["motivo"] = "chiave JustTCG non impostata"
        return jsonify(out)
    hit = PRZ_CACHE.get(cid)
    if hit and time.time() - hit[0] < 1800:      # le richieste a JustTCG sono limitate: per mezz'ora si riusa il risultato
        out["tcg"], out["motivo"] = hit[1], hit[2]
        return jsonify(out)
    try:
        jid = jt_collega(cid, lang)
        if not jid:
            out["motivo"] = "carta non trovata su JustTCG"
        else:
            data = jt_get({"cardId": jid})
            if not data:
                out["motivo"] = "JustTCG non ha risposto (limite di richieste o rete)"
            else:
                tcg = {}
                for v in data[0].get("variants") or []:
                    f, c = fin_di(v.get("printing")), INV_CMAP.get(v.get("condition"))
                    if f and c and v.get("price") is not None:
                        tcg.setdefault(f, {})[c] = v["price"]
                out["tcg"] = tcg or None
                out["motivo"] = "" if tcg else "JustTCG non ha prezzi per questa carta"
                PRZ_CACHE[cid] = (time.time(), out["tcg"], out["motivo"])
    except Exception as e:
        jtl("ERRORE prezzo " + traceback.format_exc()[-300:])
        out["motivo"] = "errore: " + e.__class__.__name__
    return jsonify(out)


@app.get("/api/collezione")
def collezione():
    righe = q("select * from carte order by id desc")
    for r in righe:
        r["qta"] = r.get("qta") or 1
        r["rarita"] = r.get("rarita") or "N/D"
        r["condiz"] = r.get("condiz") or "NM"
    ult = {(r["card_id"], r["fin"], r["cond"]): r["valore"] for r in q(
        "select card_id, fin, cond, valore from jp2 where giorno=(select max(giorno) from jp2 j "
        "where j.card_id=jp2.card_id and j.fin=jp2.fin and j.cond=jp2.cond)")}
    for r in righe:
        r["fin"] = r.get("fin") or ""
        r["usd"] = ult.get((r["card_id"], r["fin"], r["condiz"]))
        r["eur"] = r["valore"] if (r.get("valuta") == "EUR" and r.get("valore") is not None) else None      # Cardmarket: si usa solo se manca il prezzo TCG
    tot = sum((r["usd"] or 0) * r["qta"] for r in righe)
    tot_cm = sum((r["eur"] or 0) * r["qta"] for r in righe if r["usd"] is None)
    return jsonify(righe=righe, totale_usd=round(tot, 2), totale_eur_cm=round(tot_cm, 2), chiave=bool(jt_key()),
                   senza_prezzo=sum(r["qta"] for r in righe if r["usd"] is None and r["eur"] is None))


@app.get("/api/vendi")
def vendi():
    """Raggruppa le copie vendibili distinguendo lingua, condizione e finitura."""
    if cardtrader_key():
        threading.Thread(target=cardtrader_resolve_all, daemon=True).start()
    righe = q("select * from carte order by nome, numero")
    gruppi = {}
    for r in righe:
        k = (r["card_id"], r["lang"], r.get("condiz") or "NM", r.get("fin") or "")
        e = gruppi.setdefault(k, {
            "card_id": r["card_id"], "lang": r["lang"], "nome": r["nome"],
            "set": r["set_nome"], "numero": r["numero"], "rarita": r.get("rarita") or "N/D",
            "condiz": k[2], "fin": k[3], "qta": 0,
        })
        e["qta"] += r.get("qta") or 1
    mapping = cardtrader_map()
    for e in gruppi.values():
        e["blueprint_id"] = mapping.get(e["card_id"])
        e["prezzo_consigliato"] = cardtrader_recommended(e["blueprint_id"]) if e["blueprint_id"] else None
        e["img"] = f"/img/{e['lang']}/{e['card_id']}"
    return jsonify(configurato=bool(cardtrader_key()), blueprint_in_corso=CT_RESOLVE_RUNNING,
                   righe=sorted(gruppi.values(), key=lambda x: (x["set"], x["numero"], x["nome"])))


@app.post("/api/vendi/pubblica")
def pubblica_vendita():
    d = request.get_json() or {}
    card_id, lang = d.get("card_id"), d.get("lang")
    condiz = d.get("condiz") or "NM"
    fin = d.get("fin") or ""
    blueprint_id = d.get("blueprint_id")
    quantity = int(d.get("quantity") or 0)
    price = float(d.get("price") or 0)
    if not blueprint_id or quantity < 1 or price <= 0:
        return jsonify(errore="Carta non mappata o prezzo/quantita' non validi"), 400
    condiz_cod = condiz if condiz in CT_COND else CT_COND_ALIAS.get(condiz, condiz)
    available = q("select coalesce(sum(qta), 0) qta from carte where card_id=? and lang=? "
                   "and coalesce(condiz,'NM')=? and coalesce(fin,'')=?",
                   (card_id, lang, condiz_cod, fin))[0]["qta"]
    if quantity >= available:
        return jsonify(errore=f"Puoi vendere al massimo {max(available - 1, 0)} copie: una deve restare nella collezione"), 400
    try:
        properties = cardtrader_properties(int(blueprint_id), lang, condiz_cod, fin)
        payload = {
            "blueprint_id": int(blueprint_id),
            "quantity": quantity,
            "price": price,
            "properties": properties,
            "user_data_field": f"pokescan:{card_id or ''}:{lang or ''}:{fin}",
        }
        result = cardtrader_post("/products", payload)
    except (RuntimeError, ValueError) as e:
        return jsonify(errore=str(e)), 502
    return jsonify(ok=True, prodotto=result)


# ---------- SEALED (v16) ----------
# Prodotti sigillati (booster, box, ETB, blister...) presi dal catalogo CardTrader: raccolta personale con prezzi
# di mercato per lingua e pubblicazione degli annunci. Le carte singole non vengono toccate.
SEAL_IMG = pathlib.Path("pokedata/sealed_img")
SEAL_RE = re.compile(r"\b(tins?|box set|booster|bundle|preconstructed|blisters?|cases?|displays?)\b")
SEAL_EXP = {"t": 0.0, "d": []}
SEAL_CAT = {"t": 0.0, "d": {}}
SEAL_BPS = {}
SEAL_AGG = {"in_corso": False, "tot": 0, "fatte": 0}
SEAL_ERR = {}
SEAL_LOCK = threading.Lock()
SEAL_THR = threading.Lock()
SEAL_LAST = [0.0]
SEAL_LANGS = ["en", "it", "fr", "de", "es", "pt"]


def sl(msg):
    print("sealed:", time.strftime("%H:%M:%S "), msg, flush=True)


def ct_lento(path):
    """GET CardTrader (stesso metodo dello script di diagnostica) con almeno 1,1 secondi tra una richiesta e l'altra."""
    token = cardtrader_key()
    if not token:
        raise RuntimeError("Token CardTrader non configurato")
    with SEAL_THR:
        time.sleep(max(0, 1.1 - (time.time() - SEAL_LAST[0])))
        try:
            r = ps.requests.get("https://api.cardtrader.com/api/v2" + path, headers={"Authorization": "Bearer " + token}, timeout=60)
        except Exception as e:
            raise RuntimeError(f"errore di rete ({e.__class__.__name__})") from e
        finally:
            SEAL_LAST[0] = time.time()
    if r.status_code != 200:
        raise RuntimeError(f"CardTrader {r.status_code} su {path.split('?')[0]}: {r.text[:120]}")
    try:
        return r.json()
    except ValueError:
        raise RuntimeError("risposta CardTrader non valida")


def _seal_espansioni(forza=False):
    if forza or time.time() - SEAL_EXP["t"] > 43200 or not SEAL_EXP["d"]:
        SEAL_EXP["d"] = [x for x in _ct_items(ct_lento("/expansions")) if x.get("game_id") == 5]
        SEAL_EXP["t"] = time.time()
    return SEAL_EXP["d"]


def _seal_categorie():
    if time.time() - SEAL_CAT["t"] > 43200 or not SEAL_CAT["d"]:
        SEAL_CAT["d"] = {c["id"]: str(c.get("name") or "") for c in _ct_items(ct_lento("/categories?game_id=5")) if "id" in c}
        SEAL_CAT["t"] = time.time()
    return SEAL_CAT["d"]


def _seal_bps(exp, forza=False):
    c = SEAL_BPS.get(exp)
    if forza or not c or time.time() - c[0] > 21600:
        SEAL_BPS[exp] = (time.time(), _ct_items(ct_lento("/blueprints/export?expansion_id=" + str(int(exp)))))
    return SEAL_BPS[exp][1]


def _seal_cat_ok(nome, tutti):
    n = _ct_norm(nome)
    if tutti:
        return not any(k in n for k in ("single", "oversized", "complete set"))
    return bool(SEAL_RE.search(n))


def _seal_cat_nome(nome):
    return re.sub(r"^pok[eé]mon\s+", "", str(nome).strip(), flags=re.I)


def _seal_img_url(b):
    """Indirizzo dell'immagine di un prodotto (stessa logica dello script di diagnostica)."""
    for k in ("image_url", "image", "img", "picture"):
        v = b.get(k)
        if isinstance(v, dict):
            v = v.get("url") or v.get("original") or next(iter(v.values()), None)
        if v:
            return v if str(v).startswith("http") else "https://www.cardtrader.com" + str(v)
    return None


def _seal_lang_key(props):
    return next((k for k in props if k.endswith("_language")), None)


def _seal_scarica_img(bp, url):
    try:
        if not url or not (urllib.parse.urlparse(url).hostname or "").endswith("cardtrader.com"):
            return
        r = ps.requests.get(url, timeout=30)
        if r.ok and r.headers.get("content-type", "").startswith("image/") and len(r.content) < 3_000_000:
            SEAL_IMG.mkdir(parents=True, exist_ok=True)
            (SEAL_IMG / f"{int(bp)}.img").write_bytes(r.content)
    except Exception as e:
        sl(f"immagine {bp} non scaricata: {e.__class__.__name__}")


def _seal_stats(bp):
    """Minimo e mediana (EUR) per lingua delle offerte attive (vedi sotto come si trattano flag sealed e venditori in vacanza)."""
    data = ct_lento("/marketplace/products?blueprint_id=" + str(int(bp)))
    if isinstance(data, list):
        offerte = data
    elif isinstance(data, dict):
        offerte = data.get(str(int(bp)), data.get("products", []))
    else:
        offerte = []
    per = {}
    for o in offerte or []:
        pr = o.get("price")
        if isinstance(pr, dict):
            if pr.get("currency") and pr["currency"] != "EUR":
                continue
            cent = pr.get("cents")
            val = cent / 100 if cent is not None else pr.get("value")
        else:
            val = pr
        ph = o.get("properties_hash") or {}
        if not isinstance(val, (int, float)) or val <= 0:
            continue
        lingua = next((str(v).lower() for k, v in ph.items() if k.endswith("_language")), "?")
        per.setdefault(lingua, []).append((float(val), bool(o.get("on_vacation")), ph.get("sealed") is False))
    out = {}
    for lingua, v in per.items():
        # Se ci sono offerte marcate sealed si usano solo quelle; se il flag e' falso su tutte (capita su alcuni
        # prodotti) non e' affidabile e si usano tutte. I venditori in vacanza contano solo se non c'e' altro.
        pool = [x for x in v if not x[2]] or v
        attivi = [p for p, vac, _ in pool if not vac] or [p for p, _, _ in pool]
        out[lingua] = (min(attivi), statistics.median(attivi), len(attivi))
    return out


def sealed_prezzi_bp(bp):
    try:
        oggi = dt.date.today().isoformat()
        righe = [(int(bp), lingua, oggi, round(mn, 2), round(md, 2), n) for lingua, (mn, md, n) in _seal_stats(bp).items()]
        q_molti("insert or replace into sealed_prezzi values(?,?,?,?,?,?)", righe)
        if righe:
            SEAL_ERR.pop(int(bp), None)
        else:
            SEAL_ERR[int(bp)] = "nessuna offerta attiva su CardTrader"
            sl(f"prodotto {bp}: nessuna offerta attiva")
        return True
    except Exception as e:
        SEAL_ERR[int(bp)] = str(e) or e.__class__.__name__
        sl(f"ERRORE prezzi {bp}: {SEAL_ERR[int(bp)]}")
        return False


def sealed_aggiorna_prezzi():
    with SEAL_LOCK:
        if SEAL_AGG["in_corso"]:
            return
        SEAL_AGG.update(in_corso=True, tot=0, fatte=0)
    try:
        bps = [r["blueprint_id"] for r in q("select distinct blueprint_id from sealed")]
        SEAL_AGG["tot"] = len(bps)
        for bp in bps:
            sealed_prezzi_bp(bp)
            SEAL_AGG["fatte"] += 1
    finally:
        SEAL_AGG["in_corso"] = False


def ciclo_sealed():
    time.sleep(90)
    while True:
        try:
            if cardtrader_key() and q("select 1 from sealed limit 1"):
                ult = q("select max(giorno) g from sealed_prezzi")[0]["g"]
                if ult != dt.date.today().isoformat():
                    sealed_aggiorna_prezzi()
        except Exception:
            sl("ERRORE aggiornamento " + traceback.format_exc()[-300:])
        time.sleep(3600)


threading.Thread(target=ciclo_sealed, daemon=True).start()


def _seal_err(e):
    return jsonify(errore=str(e) or e.__class__.__name__), 502


@app.get("/api/sealed/set")
def sealed_set():
    """Cerca espansioni Pokemon su CardTrader per nome o codice. Senza testo: le ultime uscite."""
    if not cardtrader_key():
        return jsonify(errore="Token CardTrader non configurato"), 400
    try:
        es = _seal_espansioni(forza=bool(request.args.get("agg")))
    except RuntimeError as e:
        return _seal_err(e)
    t = _ct_norm(request.args.get("q", ""))
    parole = t.split()
    ris = []
    for e in es:
        nome, cod = _ct_norm(e.get("name")), _ct_norm(e.get("code"))
        if not parole or t == cod or all(p in nome or p in cod for p in parole):
            ris.append({"id": e["id"], "code": e.get("code"), "name": e.get("name"), "_s": (t == cod, nome.startswith(t) if t else False, e["id"])})
    ris.sort(key=lambda x: x["_s"], reverse=True)
    for x in ris:
        del x["_s"]
    return jsonify(risultati=ris[:40])


@app.get("/api/sealed/prodotti")
def sealed_prodotti():
    try:
        exp = int(request.args.get("exp", 0))
        tutti = request.args.get("tutti") == "1"
        cats = _seal_categorie()
        bps = _seal_bps(exp, forza=bool(request.args.get("agg")))
    except (RuntimeError, ValueError) as e:
        return _seal_err(e)
    out = []
    for b in bps:
        cn = cats.get(b.get("category_id"), "")
        if not _seal_cat_ok(cn, tutti):
            continue
        props = _ct_props(b)
        lk = _seal_lang_key(props)
        out.append({"id": b["id"], "nome": b.get("name"), "categoria": _seal_cat_nome(cn), "img": _seal_img_url(b),
                    "lingue": props.get(lk) or SEAL_LANGS if lk else SEAL_LANGS})
    out.sort(key=lambda x: (x["categoria"], x["nome"] or ""))
    return jsonify(prodotti=out, totale=len(bps))


@app.post("/api/sealed/aggiungi")
def sealed_aggiungi():
    d = request.get_json() or {}
    try:
        bp, exp = int(d.get("blueprint_id") or 0), int(d.get("exp_id") or 0)
        n = max(1, min(int(d.get("qta") or 1), 999))
    except (TypeError, ValueError):
        return jsonify(errore="Dati non validi"), 400
    lang = str(d.get("lang") or "").lower()
    try:
        b = next((x for x in _seal_bps(exp) if int(x.get("id") or 0) == bp), None)
        nome_set = next((str(e.get("name")) for e in _seal_espansioni() if e.get("id") == exp), "")
        cats = _seal_categorie()
    except RuntimeError as e:
        return _seal_err(e)
    if not b:
        return jsonify(errore="Prodotto non trovato su CardTrader"), 404
    props = _ct_props(b)
    lk = _seal_lang_key(props)
    if lk and props.get(lk) and lang not in props[lk]:
        return jsonify(errore=f"Lingua non disponibile per questo prodotto: {lang}"), 400
    esiste = q("select id from sealed where blueprint_id=? and lang=?", (bp, lang))
    if esiste:
        q("update sealed set qta=qta+? where id=?", (n, esiste[0]["id"]), True)
    else:
        q("insert into sealed(ts, blueprint_id, exp_id, nome, set_nome, categoria, lang, qta, img_url) values(?,?,?,?,?,?,?,?,?)",
          (dt.datetime.now().isoformat(timespec="seconds"), bp, exp, b.get("name"), nome_set,
           _seal_cat_nome(cats.get(b.get("category_id"), "")), lang, n, _seal_img_url(b)), True)
    if not (SEAL_IMG / f"{bp}.img").exists():
        threading.Thread(target=_seal_scarica_img, args=(bp, _seal_img_url(b)), daemon=True).start()
    if not q("select 1 from sealed_prezzi where blueprint_id=? limit 1", (bp,)):
        threading.Thread(target=sealed_prezzi_bp, args=(bp,), daemon=True).start()
    return jsonify(ok=True)


@app.get("/api/sealed")
def sealed_elenco():
    righe = q("select * from sealed order by set_nome, categoria, nome, lang")
    ult = {(r["blueprint_id"], r["lang"]): r for r in q(
        "select * from sealed_prezzi p where giorno=(select max(giorno) from sealed_prezzi x "
        "where x.blueprint_id=p.blueprint_id and x.lang=p.lang)")}
    tot, pezzi, senza = 0.0, 0, 0
    con_prezzi = {k[0] for k in ult}
    for r in righe:
        p = ult.get((r["blueprint_id"], r["lang"]))
        r["min"], r["med"], r["offerte"], r["giorno"] = (p["minimo"], p["mediana"], p["offerte"], p["giorno"]) if p else (None, None, 0, None)
        r["img"] = f"/api/sealed/img/{r['blueprint_id']}"
        r["errore_prezzo"] = None if p else (SEAL_ERR.get(r["blueprint_id"]) or (
            "nessuna offerta in questa lingua" if r["blueprint_id"] in con_prezzi else None))
        pezzi += r["qta"]
        if r["min"] is None:
            senza += r["qta"]
        else:
            tot += r["min"] * r["qta"]
    ultimo = q("select max(giorno) g from sealed_prezzi")[0]["g"]
    return jsonify(righe=righe, totale_eur=round(tot, 2), pezzi=pezzi, senza_prezzo=senza, ultimo_agg=ultimo,
                   aggiornamento=dict(SEAL_AGG), configurato=bool(cardtrader_key()))


@app.get("/api/sealed/storico/<int:bp>/<lang>")
def sealed_storico(bp, lang):
    return jsonify(q("select giorno, minimo, mediana, offerte from sealed_prezzi where blueprint_id=? and lang=? order by giorno",
                     (bp, lang.lower())))


@app.post("/api/sealed/aggiorna-prezzi")
def sealed_aggiorna_ora():
    if not cardtrader_key():
        return jsonify(errore="Token CardTrader non configurato"), 400
    if not SEAL_AGG["in_corso"]:
        threading.Thread(target=sealed_aggiorna_prezzi, daemon=True).start()
    return jsonify(ok=True)


@app.post("/api/sealed/qta/<int:i>")
def sealed_qta(i):
    n = int((request.get_json() or {}).get("d", 1))
    q("update sealed set qta=qta+? where id=?", (n, i), True)
    q("delete from sealed where id=? and qta<=0", (i,), True)
    return jsonify(ok=True)


@app.delete("/api/sealed/<int:i>")
def sealed_elimina(i):
    q("delete from sealed where id=?", (i,), True)
    return jsonify(ok=True)


@app.get("/api/sealed/img/<int:bp>")
def sealed_img(bp):
    f = SEAL_IMG / f"{bp}.img"
    if f.exists():
        testa = f.read_bytes()[:12]
        mt = "image/png" if testa.startswith(b"\x89PNG") else "image/webp" if testa[:4] == b"RIFF" else "image/gif" if testa[:3] == b"GIF" else "image/jpeg"
        return send_file(f, mimetype=mt, max_age=86400)
    r = q("select img_url from sealed where blueprint_id=? limit 1", (bp,))
    url = r[0]["img_url"] if r else None
    if url and (urllib.parse.urlparse(url).hostname or "").endswith("cardtrader.com"):
        threading.Thread(target=_seal_scarica_img, args=(bp, url), daemon=True).start()      # la prossima volta e' gia' in locale
        return redirect(url)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 250 350"><rect x="2" y="2" width="246" height="346" rx="16" fill="#eef0f4" stroke="#c9ced8" stroke-width="3"/>'
           '<text x="125" y="180" fill="#8b93a2" font-family="sans-serif" font-size="18" text-anchor="middle">Senza immagine</text></svg>')
    return Response(svg, mimetype="image/svg+xml", headers={"Cache-Control": "max-age=300"})


@app.post("/api/sealed/pubblica")
def sealed_pubblica():
    d = request.get_json() or {}
    try:
        i, quantity, price = int(d.get("id") or 0), int(d.get("quantity") or 0), float(d.get("price") or 0)
    except (TypeError, ValueError):
        return jsonify(errore="Quantita' o prezzo non validi"), 400
    r = q("select * from sealed where id=?", (i,))
    if not r:
        return jsonify(errore="Prodotto non trovato nella raccolta"), 404
    r = r[0]
    if quantity < 1 or price <= 0:
        return jsonify(errore="Quantita' o prezzo non validi"), 400
    if quantity > r["qta"]:
        return jsonify(errore=f"Ne possiedi solo {r['qta']}"), 400
    try:
        b = next((x for x in _seal_bps(r["exp_id"]) if int(x.get("id") or 0) == r["blueprint_id"]), None)
        if not b:
            return jsonify(errore="Prodotto non piu' presente nel catalogo CardTrader"), 404
        props = _ct_props(b)
        lk = _seal_lang_key(props) or "pokemon_language"
        properties = {lk: r["lang"]}
        if "sealed" in props:
            properties["sealed"] = True
        if "first_edition" in props:
            properties["first_edition"] = False
        token = cardtrader_key()
        if not token:
            return jsonify(errore="Token CardTrader non configurato"), 400
        resp = ps.requests.post("https://api.cardtrader.com/api/v2/products", headers={"Authorization": "Bearer " + token}, timeout=30, json={
            "blueprint_id": r["blueprint_id"], "quantity": quantity, "price": price, "properties": properties,
            "user_data_field": f"pokescan-sealed:{r['blueprint_id']}:{r['lang']}"})
        if not resp.ok:
            sl(f"pubblicazione rifiutata {resp.status_code}: {resp.text[:300]}")
            return jsonify(errore=f"CardTrader {resp.status_code}: {resp.text[:200]}"), 502
        return jsonify(ok=True, prodotto=resp.json())
    except RuntimeError as e:
        return _seal_err(e)
    except Exception as e:
        sl("ERRORE pubblicazione " + traceback.format_exc()[-300:])
        return _seal_err(e)


VERIF = {"in_corso": False, "tot": 0, "fatte": 0, "righe": []}


def verifica_lavoro(nome, setq, lang):
    VERIF.update(in_corso=True, tot=0, fatte=0, righe=[])
    try:
        sn = norm(setq)
        carte = [m for m in M.meta if m["lang"] == lang and norm(nome) in norm(m["name"]) and (not sn or sn in norm(m["set"]))]
        carte.sort(key=lambda m: int(re.sub(r"\D", "", numn(m["number"])) or 0))
        VERIF["tot"] = len(carte)
        for m in carte:
            jid = jt_collega(m["id"], m["lang"], forza=True)
            VERIF["righe"].append(f"{m['number']:>7}  {m['name']}  ->  " + (f"OK  {jid}" if jid else "NON COLLEGATA  " + JTDBG.get(m["id"], "(errore o limite JustTCG: vedi /api/jt-log)")))
            VERIF["fatte"] += 1
    except Exception:
        jtl("ERRORE verifica " + traceback.format_exc()[-300:])
    finally:
        VERIF["in_corso"] = False


@app.get("/api/jt-verifica")
def jt_verifica():
    """Controlla come JustTCG chiama un gruppo di carte: /api/jt-verifica?nome=Pikachu&set=30th&lang=it&avvia=1"""
    nome, setq, lang = request.args.get("nome", ""), request.args.get("set", ""), request.args.get("lang", "it")
    if request.args.get("avvia") and nome and not VERIF["in_corso"]:
        threading.Thread(target=verifica_lavoro, args=(nome, setq, lang), daemon=True).start()
        time.sleep(0.3)
    return jsonify(VERIF)


@app.get("/api/jt-cerca")
def jt_cerca():
    """Mostra i nomi esatti con cui JustTCG chiama le carte: /api/jt-cerca?q=Pikachu&set=30th"""
    qq, setq = request.args.get("q", ""), norm(request.args.get("set", ""))
    sets = [s for s in jt_sets() if setq and (setq in norm(s.get("name")) or setq in norm(s.get("id")))][:2]
    out = []
    for extra in ([{"set": s["id"]} for s in sets] or [{}]):
        for off in (0, 20, 40):
            data = jt_get(dict({"game": "pokemon", "q": qq, "limit": 20, "offset": off}, **extra))
            if data is None:
                return jsonify(errore="JustTCG non risponde: guarda /api/jt-log"), 502
            out += [c for c in data if not setq or setq in norm(c.get("set_name")) or setq in norm(c.get("set"))]
            if len(data) < 20:
                break
    nm = lambda c: next((v.get("price") for v in c.get("variants", []) if v.get("condition") == "Near Mint" and v.get("price") is not None), None)
    return jsonify(set_trovati=[{"id": s.get("id"), "nome": s.get("name")} for s in sets], n=len(out),
                   carte=[{"id": c.get("id"), "nome": c.get("name"), "set": c.get("set_name"), "numero": c.get("number"),
                           "rarita": c.get("rarity"), "finiture": sorted({v.get("printing") for v in c.get("variants", []) if v.get("printing")}),
                           "prezzo_NM": nm(c)} for c in out])


@app.get("/api/jt-log")
def jt_log():
    return jsonify(chiave=bool(jt_key()), eventi=list(JTLOG))


@app.get("/api/tcg/<cid>")
def tcg(cid):
    l = q("select jid from jlink where card_id=?", (cid,))
    own = set(combos_di(cid))
    serie = {}
    for r in q("select cond, fin, giorno, valore from jp2 where card_id=? order by giorno", (cid,)):
        if (r["cond"], r["fin"]) in own:
            serie.setdefault(r["cond"] + "|" + r["fin"], []).append({"giorno": r["giorno"], "valore": r["valore"]})
    return jsonify(collegata=bool(l and l[0]["jid"]), serie=serie)


@app.get("/api/storico/<cid>")
def storico(cid):
    return jsonify(q("select giorno, valore, valuta from prezzi where card_id=? order by giorno", (cid,)))


@app.post("/api/qta/<int:i>")
def qta(i):
    n = int((request.get_json() or {}).get("d", 1))
    q("update carte set qta=coalesce(qta,1)+? where id=?", (n, i), True)
    q("delete from carte where id=? and qta<=0", (i,), True)
    return jsonify(ok=True)


@app.delete("/api/carta/<int:i>")
def elimina(i):
    q("delete from carte where id=?", (i,), True)
    return jsonify(ok=True)


@app.post("/api/elimina")
def elimina_molte():
    ids = [int(i) for i in ((request.get_json() or {}).get("ids") or [])][:500]
    q_molti("delete from carte where id=?", [(i,) for i in ids])
    return jsonify(ok=True, eliminate=len(ids))


@app.post("/api/aggiorna")
def aggiorna_ora():
    threading.Thread(target=aggiorna, daemon=True).start()
    return jsonify(ok=True)


@app.get("/export.csv")
def export():
    o = io.StringIO()
    w = csv.writer(o, delimiter=";")
    w.writerow(["data", "id", "nome", "set", "numero", "lingua", "rarita", "quantita", "valore", "valuta", "stato", "condizione", "finitura"])
    for r in q("select * from carte order by id"):
        w.writerow([r["ts"], r["card_id"], r["nome"], r["set_nome"], r["numero"], r["lang"], r.get("rarita") or "",
                    r.get("qta") or 1, str(r["valore"] if r["valore"] is not None else "").replace(".", ","),
                    r["valuta"], r["stato"], r.get("condiz") or "NM", {"S": "Standard", "H": "Holo", "R": "Reverse Holo"}.get(r.get("fin") or "", "")])
    return Response("\ufeff" + o.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=collezione.csv"})
