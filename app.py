"""
Pokescan - server web per riconoscere e catalogare carte Pokemon.

Avvio normale (Docker o gunicorn):   gunicorn -b 0.0.0.0:8085 -w 1 --threads 2 app:app
Comandi di configurazione (da lanciare dalla cartella del progetto):
    python app.py --setpw     imposta nome utente e password (attiva il login)
    python app.py --setkey    salva la chiave API di JustTCG (facoltativa) in pokedata/justtcg.key

Tutti i dati dell'utente (database, indici, password cifrata, chiavi) stanno nella cartella pokedata/,
che NON va mai pubblicata nel repository.
"""
import csv, getpass, hashlib, hmac, io, json, os, re, secrets, sqlite3, sys, threading, time, datetime as dt, pathlib
import collections, traceback
import cv2, numpy as np
from flask import Flask, Response, jsonify, redirect, request, send_file, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import pokescan as ps

pathlib.Path("pokedata").mkdir(exist_ok=True)
AUTH = pathlib.Path("pokedata/auth.json")
if __name__ == "__main__" and "--setpw" in sys.argv:      # python app.py --setpw
    u = input("Nome utente: ").strip()
    p1 = getpass.getpass("Password (almeno 8 caratteri): ")
    if not u or len(p1) < 8 or p1 != getpass.getpass("Ripeti la password: "):
        sys.exit("Dati non validi o password diverse: non e' cambiato nulla.")
    AUTH.write_text(json.dumps({"user": u, "hash": generate_password_hash(p1)}))
    os.chmod(AUTH, 0o600)
    sys.exit("Password salvata. Il login e' attivo.")

KEYF = pathlib.Path("pokedata/justtcg.key")
if __name__ == "__main__" and "--setkey" in sys.argv:      # python app.py --setkey
    k = getpass.getpass("Chiave API JustTCG (non viene mostrata): ").strip()
    if len(k) < 10:
        sys.exit("Chiave non valida: non e' cambiato nulla.")
    KEYF.write_text(k)
    os.chmod(KEYF, 0o600)
    sys.exit("Chiave salvata in pokedata/justtcg.key.")

app = Flask(__name__, static_folder="static")

# ---------- LOGIN ----------
def _key():
    f = pathlib.Path("pokedata/secret.key")
    if not f.exists():
        f.write_text(secrets.token_hex(32))
        os.chmod(f, 0o600)
    return f.read_text().strip()


app.secret_key = _key()
if not AUTH.exists():
    print("ATTENZIONE: nessuna password impostata, chiunque raggiunga questa porta puo' usare l'app. "
          "Imposta il login con:  python app.py --setpw", flush=True)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
app.permanent_session_lifetime = dt.timedelta(days=30)
FAIL = {}
LIBERE = {"/login", "/logout", "/static/icon-180.png", "/static/icon-512.png"}
LOGIN = '<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<meta name="theme-color" content="#000"><title>Pokescan - Accesso</title><link rel="apple-touch-icon" href="/static/icon-180.png">\n<style>*{box-sizing:border-box}body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;color:#f5f5f7;font:16px system-ui,-apple-system,sans-serif;\nbackground:radial-gradient(800px 480px at 12% -8%,#13243f,transparent 60%),radial-gradient(700px 480px at 100% 105%,#2b1340,transparent 55%),#000 fixed}\nform{width:100%;max-width:380px;padding:28px 22px;border-radius:26px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);-webkit-backdrop-filter:blur(26px) saturate(160%);backdrop-filter:blur(26px) saturate(160%);text-align:center}\nimg{width:84px;height:84px;border-radius:20px;margin-bottom:10px}h1{margin:0 0 18px;font-size:26px;letter-spacing:-.5px}\ninput{width:100%;margin-bottom:12px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);color:#f5f5f7;border-radius:14px;padding:14px;font-size:16px;outline:0}\ninput:focus{border-color:#0a84ff}button{width:100%;border:0;border-radius:14px;padding:14px;font-size:16px;font-weight:600;background:#0a84ff;color:#fff;cursor:pointer}\n.e{color:#ff453a;min-height:22px;margin-bottom:8px;font-size:14px}</style></head><body>\n<form method="post"><img src="/static/icon-180.png" alt=""><h1>Pokescan</h1><div class="e" role="alert">@@ERR@@</div>\n<input name="u" placeholder="Nome utente" autocomplete="username" autocapitalize="none" autocorrect="off" required>\n<input name="p" type="password" placeholder="Password" autocomplete="current-password" required><button>Accedi</button></form></body></html>'


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
DB = "pokedata/collezione.db"
MARK = pathlib.Path("pokedata/ultimo_agg.txt")
LANGS = {"en": "English", "it": "Italiano", "fr": "Français", "de": "Deutsch", "es": "Español", "pt": "Português", "ja": "日本語", "ko": "한국어", "zh-tw": "繁體中文", "zh-cn": "简体中文"}


def sid(cid):
    return cid.rsplit("-", 1)[0]


SETS = {}


def costruisci_sets():
    global SETS
    d = {}
    for m in M.meta:
        s = d.setdefault(sid(m["id"]), {"id": sid(m["id"]), "names": {}, "langs": set()})
        s["langs"].add(m["lang"])
        s["names"][m["lang"]] = m["set"]
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
    for col, t in (("rarita", "text"), ("qta", "integer default 1"), ("condiz", "text default 'NM'")):
        if col not in cols:
            c.execute(f"alter table carte add column {col} {t}")
    c.execute("create table if not exists prezzi(card_id text, giorno text, valore real, valuta text,"
              " primary key(card_id, giorno))")
    c.execute("create table if not exists jlink(card_id text primary key, jid text, ts text)")
    c.execute("create table if not exists jprezzi(card_id text, cond text, giorno text, valore real, primary key(card_id, cond, giorno))")
    c.execute("create table if not exists setinfo(sid text, lang text, nome text, logo text, totale integer, primary key(sid, lang))")
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


def jt_get(params=None, body=None):
    k = jt_key()
    if not k:
        return None
    for tentativo in range(2):
        with JTL:                                   # piano gratuito: circa 10 richieste al minuto
            time.sleep(max(0, 6.5 - (time.time() - JTT[0])))
            try:
                r = ps.requests.request("POST" if body is not None else "GET", JT, params=params, json=body,
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


def jt_collega(cid, lang):
    """Cerca la carta su JustTCG (nome inglese + numero + set) e salva il collegamento; i fallimenti si ritentano dopo 3 giorni."""
    r = q("select jid, ts from jlink where card_id=?", (cid,))
    if r and (r[0]["jid"] or r[0]["ts"] >= (dt.date.today() - dt.timedelta(3)).isoformat()):
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
    n = str(num or "").split("/")[0].lstrip("0") or "0"
    tok = set(norm(sset).split())
    def cod(s):      # "ME04" e "me04" -> stesso codice; "SWSH08" e "swsh8" idem
        return {re.sub(r"^([a-z]+)0+(?=\d)", r"\1", w) for w in norm(s).split()}

    sc = cod(sid(cid))

    def punti(c):
        if sc & (cod(c.get("set_name")) | cod((c.get("set") or "").replace("-", " "))):
            return 1.0                       # il codice del set (es. me04) coincide: corrispondenza sicura
        t = set(norm(c.get("set_name")).split())
        return len(tok & t) / max(len(tok | t), 1) if tok else 0

    cands = []
    for off in (0, 20, 40):          # guardo altre pagine solo se la carta giusta non e' ancora comparsa
        data = jt_get({"game": "pokemon", "q": nome, "limit": 20, "offset": off})
        if data is None:
            return None              # errore di rete, di chiave o troppe richieste: non salvo nulla e riprovo piu' tardi
        cands += [c for c in data if norm(nome) in norm(c.get("name"))
                  and (str(c.get("number") or "").split("/")[0].lstrip("0") or "0") == n]
        if len(data) < 20 or any(punti(c) >= 0.4 for c in cands):
            break

    cands.sort(key=lambda c: (punti(c), norm(c.get("name")) == norm(nome)), reverse=True)
    best = cands[0] if cands and (punti(cands[0]) >= 0.4 or len(cands) == 1) else None
    if not best:
        print("justtcg: nessun collegamento per", cid, "|", nome, "|", sset, "|", n, "| trovate:",
              [(c.get("name"), c.get("set_name"), c.get("number")) for c in cands[:5]])
    q("insert or replace into jlink values(?,?,?)", (cid, best and best.get("id"), dt.date.today().isoformat()), True)
    return best and best.get("id")


q("delete from jlink where jid is null", (), True)      # ad ogni avvio ritenta i collegamenti falliti


def jt_salva(cid, c, conds):
    """Salva il prezzo di oggi e lo storico disponibile, per ogni condizione posseduta. Restituisce quanti prezzi ha salvato."""
    oggi, storico, oggi_s = [], [], dt.date.today().isoformat()
    for cd in conds:
        vs = [v for v in c.get("variants", []) if v.get("condition") == CMAP.get(cd) and v.get("price") is not None]
        vs.sort(key=lambda v: PRINT.index(v["printing"]) if v.get("printing") in PRINT else 9)
        if not vs:
            jtl(f"{cid} {cd}: JustTCG non ha un prezzo per questa condizione")
            continue
        v = vs[0]
        oggi.append((cid, cd, oggi_s, v["price"]))
        for h in v.get("priceHistory") or []:
            if h.get("p") is not None and h.get("t"):
                g = dt.datetime.fromtimestamp(h["t"], dt.timezone.utc).date().isoformat()
                storico.append((cid, cd, g, h["p"]))
    q_molti("insert or ignore into jprezzi values(?,?,?,?)", storico)
    q_molti("insert or replace into jprezzi values(?,?,?,?)", oggi)      # il prezzo di oggi vince sullo storico
    return len(oggi)


def conds_di(cid):
    return [r["c"] for r in q("select distinct coalesce(condiz,'NM') c from carte where card_id=?", (cid,))]


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
        jtl(f"{cid}: salvati {jt_salva(cid, data[0], conds_di(cid))} prezzi")
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
                salvati += jt_salva(cid, by[j], conds_di(cid))
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
                   backup=bk[-1].stem[-10:] if bk else "", ric_tot=c["n"], ric_ok=c["e"])


def meta_set(s, lang):
    """Nome, logo e numero totale di carte del set (da TCGdex), salvati una volta sola."""
    if q("select 1 from setinfo where sid=? and lang=? and totale is not null", (s, lang)):
        return
    d = ps.get_json(f"{ps.BASE}/{lang}/sets/{s}", tries=2, timeout=30) or {}
    if not d:
        return
    cc = d.get("cardCount") or {}
    logo = d.get("logo") or ""
    if logo and not logo.lower().endswith((".png", ".webp", ".jpg")):
        logo += ".png"
    q("insert or replace into setinfo values(?,?,?,?,?)", (s, lang, d.get("name"), logo, cc.get("total") or cc.get("official")), True)


@app.get("/api/set")
def set_list():
    g = {}
    for r in q("select card_id, lang, set_nome, qta from carte"):
        k = (sid(r["card_id"]), r["lang"])
        e = g.setdefault(k, {"nome": r["set_nome"], "ids": set(), "copie": 0})
        e["ids"].add(r["card_id"])
        e["copie"] += r["qta"] or 1
    info = {(x["sid"], x["lang"]): x for x in q("select * from setinfo")}
    out = []
    for k, e in g.items():
        i = info.get(k, {})
        out.append({"sid": k[0], "lang": k[1], "nome": i.get("nome") or e["nome"], "logo": i.get("logo") or "",
                    "possedute": len(e["ids"]), "totale": i.get("totale"), "copie": e["copie"]})
    manca = [k for k in g if info.get(k, {}).get("totale") is None]
    if manca:
        threading.Thread(target=lambda: [meta_set(*k) for k in manca], daemon=True).start()
    return jsonify(sorted(out, key=lambda x: (x["nome"] or "").lower()))


COND = ("NM", "LP", "MP", "HP", "DMG")


@app.post("/api/condizione/<int:i>")
def condizione(i):
    c = (request.get_json() or {}).get("c")
    r = q("select * from carte where id=?", (i,))
    if c not in COND or not r:
        return jsonify(errore="richiesta non valida"), 400
    r = r[0]
    if (r.get("condiz") or "NM") == c:
        return jsonify(ok=True)
    dest = q("select id from carte where card_id=? and lang=? and coalesce(condiz,'NM')=? and id!=?",
             (r["card_id"], r["lang"], c, i))
    if (r.get("qta") or 1) > 1:          # sposta una sola copia
        q("update carte set qta=qta-1 where id=?", (i,), True)
        if dest:
            q("update carte set qta=coalesce(qta,1)+1 where id=?", (dest[0]["id"],), True)
        else:
            q("insert into carte(ts,card_id,nome,set_nome,numero,lang,valore,valuta,stato,rarita,qta,condiz) "
              "select ts,card_id,nome,set_nome,numero,lang,valore,valuta,stato,rarita,1,? from carte where id=?", (c, i), True)
    elif dest:
        q("update carte set qta=coalesce(qta,1)+1 where id=?", (dest[0]["id"],), True)
        q("delete from carte where id=?", (i,), True)
    else:
        q("update carte set condiz=? where id=?", (c, i), True)
    threading.Thread(target=jt_card, args=(r["card_id"], r["lang"]), daemon=True).start()
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
    return send_file(ps.percorso({"id": secure_filename(cid), "lang": secure_filename(lang)}), max_age=86400)


@app.get("/api/filtri")
def filtri():
    langs = sorted({m["lang"] for m in M.meta})
    return jsonify(langs=[{"id": l, "nome": LANGS.get(l, l.upper())} for l in langs],
                   sets=[{"id": s["id"], "names": s["names"], "langs": sorted(s["langs"])} for s in SETS.values()])


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
    if not tutti:
        return jsonify(errore="nessuna carta con questi filtri"), 404
    top, st = fondi(tutti)
    jtl(f"riconoscimento: {int((time.time() - t0) * 1000)} ms su {len(ims)} fotogrammi")
    return jsonify(trovata=trovata, stato=st, frames=len(tutti), candidati=[cand(r["m"], r["inl"], r["sim"]) for r in top])


@app.get("/api/cerca")
def cerca():
    t = request.args.get("q", "").strip().lower()
    lang, s = request.args.get("lang"), request.args.get("set")
    out = []
    if len(t) < 2:
        return jsonify(out)
    for m in M.meta:
        if t in m["name"].lower() and (not lang or m["lang"] == lang) and (not s or sid(m["id"]) == s):
            out.append(cand(m))
            if len(out) >= 30:
                break
    return jsonify(out)


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
    ts = time.strftime("%Y-%m-%d %H:%M")
    r = q("select id from carte where card_id=? and lang=? and coalesce(condiz,'NM')=?", (cid, d["lang"], cd))
    if r:
        q("update carte set qta=coalesce(qta,1)+1, ts=? where id=?", (ts, r[0]["id"]), True)
    else:
        q("insert into carte(ts,card_id,nome,set_nome,numero,lang,valore,valuta,stato,rarita,qta,condiz) values(?,?,?,?,?,?,?,?,?,?,1,?)",
          (ts, cid, d["nome"], d["set"], d["numero"], d["lang"], None, "", d.get("stato", "ok"), "N/D", cd), True)
    qta = q("select qta from carte where card_id=? and lang=? and coalesce(condiz,'NM')=?", (cid, d["lang"], cd))[0]["qta"]
    if d.get("proposta"):      # registro delle correzioni: la proposta era giusta?
        q("insert into correzioni(ts,proposta,scelta,lang,esatta,pos,stato,punti) values(?,?,?,?,?,?,?,?)",
          (ts, d["proposta"], cid, d["lang"], int(d["proposta"] == cid),
           d.get("pos", 0), d.get("stato", ""), d.get("punti", 0)), True)
    for f, args in ((dopo_salvataggio, (cid, d["lang"])), (meta_set, (sid(cid), d["lang"])), (jt_card, (cid, d["lang"]))):
        threading.Thread(target=f, args=args, daemon=True).start()
    jtl(f"salvataggio {cid}: {int((time.time() - t0) * 1000)} ms")
    return jsonify(qta=qta)


@app.get("/api/collezione")
def collezione():
    righe = q("select * from carte order by id desc")
    for r in righe:
        r["qta"] = r.get("qta") or 1
        r["rarita"] = r.get("rarita") or "N/D"
        r["condiz"] = r.get("condiz") or "NM"
    ult = {(r["card_id"], r["cond"]): r["valore"] for r in q(
        "select card_id, cond, valore from jprezzi where giorno=(select max(giorno) from jprezzi j "
        "where j.card_id=jprezzi.card_id and j.cond=jprezzi.cond)")}
    for r in righe:
        r["usd"] = ult.get((r["card_id"], r["condiz"]))
    tot = sum((r["usd"] or 0) * r["qta"] for r in righe)
    return jsonify(righe=righe, totale_usd=round(tot, 2), chiave=bool(jt_key()),
                   senza_prezzo=sum(r["qta"] for r in righe if r["usd"] is None))


@app.get("/api/jt-log")
def jt_log():
    return jsonify(chiave=bool(jt_key()), eventi=list(JTLOG))


@app.get("/api/tcg/<cid>")
def tcg(cid):
    l = q("select jid from jlink where card_id=?", (cid,))
    own = set(conds_di(cid))
    serie = {}
    for r in q("select cond, giorno, valore from jprezzi where card_id=? order by giorno", (cid,)):
        if r["cond"] in own:
            serie.setdefault(r["cond"], []).append({"giorno": r["giorno"], "valore": r["valore"]})
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


@app.post("/api/aggiorna")
def aggiorna_ora():
    threading.Thread(target=aggiorna, daemon=True).start()
    return jsonify(ok=True)


@app.get("/export.csv")
def export():
    o = io.StringIO()
    w = csv.writer(o, delimiter=";")
    w.writerow(["data", "id", "nome", "set", "numero", "lingua", "rarita", "quantita", "valore", "valuta", "stato", "condizione"])
    for r in q("select * from carte order by id"):
        w.writerow([r["ts"], r["card_id"], r["nome"], r["set_nome"], r["numero"], r["lang"], r.get("rarita") or "",
                    r.get("qta") or 1, str(r["valore"] if r["valore"] is not None else "").replace(".", ","),
                    r["valuta"], r["stato"], r.get("condiz") or "NM"])
    return Response("\ufeff" + o.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=collezione.csv"})
