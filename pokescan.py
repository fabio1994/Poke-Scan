"""
pokescan - motore di riconoscimento delle carte Pokemon (e modalita' a riga di comando).

Come funziona il riconoscimento:
  1) un modello CLIP confronta la carta con le immagini ufficiali e propone i 40 candidati piu' simili;
  2) un secondo controllo (punti caratteristici SIFT + RANSAC) verifica i candidati sull'illustrazione
     e sceglie quello che coincide davvero.

Uso da riga di comando (la web app, app.py, usa le stesse funzioni):
    python pokescan.py index --lang it      # scarica le carte di una lingua e costruisce l'indice
    python pokescan.py scan                 # scansione automatica da webcam (finestra OpenCV)
    python pokescan.py folder PERCORSO      # riconosce tutte le immagini di una cartella

I dati delle carte e i prezzi di riferimento vengono da TCGdex (gratuito, nessuna chiave).
Risultati della modalita' a riga di comando in collezione.csv (separatore ';', si apre con Excel).
Se lo scan trova piu' indici (per esempio inglese + italiano) li usa tutti insieme.
"""
import argparse, csv, json, os, pathlib, sys, time
from collections import OrderedDict
from contextlib import nullcontext
from concurrent.futures import ThreadPoolExecutor
import cv2, numpy as np, requests
from PIL import Image

BASE = "https://api.tcgdex.net/v2"
API = f"{BASE}/en"              # i prezzi si leggono sempre dallo stesso id
DATA = pathlib.Path("pokedata")
IMG = DATA / "img"
CSV_OUT = "collezione.csv"
W, H = 300, 420
SOGLIA_SCORE = 0.80     # similarita' CLIP minima per fidarsi quando SIFT non basta
SOGLIA_MARGINE = 0.02
CANDIDATI = 40          # quanti candidati ricontrolla SIFT


def file_indice(lang):
    return ("emb.npy", "meta.json") if lang == "en" else (f"emb_{lang}.npy", f"meta_{lang}.json")


def percorso(m):
    lang = m.get("lang", "en")
    return IMG / (f"{m['id']}.png" if lang == "en" else f"{lang}_{m['id']}.png")


# ---------- 1) INDICE ----------
def get_json(url, tries=8, timeout=60):
    for t in range(tries):
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            attesa = 3 * (t + 1)
            print(f"Errore ({e.__class__.__name__}) su {url}, riprovo tra {attesa}s...")
            time.sleep(attesa)
    return None


def build_index(lang="en"):
    from sentence_transformers import SentenceTransformer
    IMG.mkdir(parents=True, exist_ok=True)
    sets = get_json(f"{BASE}/{lang}/sets")
    if not sets:
        sys.exit("Il server delle carte non risponde (o lingua non valida). Riprova tra qualche minuto.")
    cards = []
    for n, s in enumerate(sets, 1):
        d = get_json(f"{BASE}/{lang}/sets/{s['id']}")
        if not d:
            continue
        for c in d.get("cards", []):
            if c.get("image"):
                cards.append({"id": c["id"], "name": c.get("name", ""), "number": c.get("localId", ""),
                              "set": s.get("name", s["id"]), "lang": lang, "image": c["image"] + "/low.png"})
        print(f"[{lang}] Set {n}/{len(sets)}: {s.get('name', s['id'])} - carte con immagine finora: {len(cards)}")

    def scarica(c):
        p = percorso(c)
        if not p.exists():
            try:
                p.write_bytes(requests.get(c["image"], timeout=60).content)
            except Exception:
                return None
        return c if p.exists() and p.stat().st_size > 1000 else None

    print("Scarico le immagini (riprende da dove era arrivato se interrotto)...")
    with ThreadPoolExecutor(8) as ex:
        cards = [c for c in ex.map(scarica, cards) if c]

    model = SentenceTransformer("clip-ViT-B-32")
    embs = []
    for i in range(0, len(cards), 256):
        chunk = cards[i:i + 256]
        imgs = []
        for c in chunk:
            try:
                imgs.append(Image.open(percorso(c)).convert("RGB"))
            except Exception:
                imgs.append(Image.new("RGB", (245, 342)))
        embs.append(model.encode(imgs, batch_size=64, normalize_embeddings=True, convert_to_numpy=True))
        print(f"Indicizzate {min(i + 256, len(cards))}/{len(cards)}")
    f_emb, f_meta = file_indice(lang)
    np.save(DATA / f_emb, np.vstack(embs))
    meta = [{"id": c["id"], "name": c["name"], "number": c["number"], "set": c["set"], "lang": lang} for c in cards]
    (DATA / f_meta).write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    print(f"Indice [{lang}] pronto: {len(cards)} carte.")


def aggiorna_indice(matcher, lang, lock=None):
    """Aggiunge all'indice solo le carte nuove (scarica e calcola solo quelle). Restituisce quante."""
    IMG.mkdir(parents=True, exist_ok=True)
    f_emb, f_meta = file_indice(lang)
    esistenti = {m["id"] for m in matcher.meta if m.get("lang") == lang}
    sets = get_json(f"{BASE}/{lang}/sets", tries=3)
    if not sets:
        return 0
    nuove = []
    for s in sets:
        d = get_json(f"{BASE}/{lang}/sets/{s['id']}", tries=3)
        for c in (d or {}).get("cards", []):
            if c.get("image") and c["id"] not in esistenti:
                nuove.append({"id": c["id"], "name": c.get("name", ""), "number": c.get("localId", ""),
                              "set": s.get("name", s["id"]), "lang": lang, "image": c["image"] + "/low.png"})

    def scarica(c):
        p = percorso(c)
        if not p.exists():
            try:
                p.write_bytes(requests.get(c["image"], timeout=60).content)
            except Exception:
                return None
        return c if p.exists() and p.stat().st_size > 1000 else None

    with ThreadPoolExecutor(4) as ex:
        nuove = [c for c in ex.map(scarica, nuove) if c]
    if not nuove:
        return 0
    imgs = [Image.open(percorso(c)).convert("RGB") for c in nuove]
    with (lock or nullcontext()):
        emb = matcher.model.encode(imgs, batch_size=16, normalize_embeddings=True, convert_to_numpy=True)
    meta_old = json.loads((DATA / f_meta).read_text(encoding="utf-8")) if (DATA / f_meta).exists() else []
    E_old = np.load(DATA / f_emb) if (DATA / f_emb).exists() else np.zeros((0, emb.shape[1]), emb.dtype)
    meta_new = meta_old + [{"id": c["id"], "name": c["name"], "number": c["number"], "set": c["set"], "lang": lang} for c in nuove]
    with open(DATA / (f_emb + ".tmp"), "wb") as fh:
        np.save(fh, np.vstack([E_old, emb]))
    (DATA / (f_meta + ".tmp")).write_text(json.dumps(meta_new, ensure_ascii=False), encoding="utf-8")
    os.replace(DATA / (f_emb + ".tmp"), DATA / f_emb)
    os.replace(DATA / (f_meta + ".tmp"), DATA / f_meta)
    print(f"[{lang}] aggiunte {len(nuove)} carte nuove")
    return len(nuove)


# ---------- 2) RICONOSCIMENTO ----------
class Matcher:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.carica()
        self.model = SentenceTransformer("clip-ViT-B-32")
        self._init_sift()

    def carica(self):
        """(Ri)carica gli indici dal disco."""
        Es, meta = [], []
        lingue = ["en"] + [p.stem[4:] for p in sorted(DATA.glob("emb_*.npy"))]
        for lang in lingue:
            f_emb, f_meta = file_indice(lang)
            if (DATA / f_emb).exists() and (DATA / f_meta).exists():
                Es.append(np.load(DATA / f_emb))
                for m in json.loads((DATA / f_meta).read_text(encoding="utf-8")):
                    m.setdefault("lang", lang)
                    meta.append(m)
                print(f"Indice caricato: {lang}")
        if not Es:
            sys.exit("Indice mancante: esegui prima  python pokescan.py index")
        self.E = np.vstack(Es)
        self.lang_arr = np.array([m["lang"] for m in meta])
        self.sid_arr = np.array([m["id"].rsplit("-", 1)[0] for m in meta])
        self.meta = meta

    def _init_sift(self):
        self.sift = cv2.SIFT_create(nfeatures=700)
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
        self.bf = cv2.BFMatcher(cv2.NORM_L2)
        self.cache = OrderedDict()          # ultime 3000 carte in memoria
        (DATA / "sift").mkdir(parents=True, exist_ok=True)

    def _feat(self, bgr):
        g = cv2.cvtColor(cv2.resize(bgr, (W, H)), cv2.COLOR_BGR2GRAY)
        kp, des = self.sift.detectAndCompute(self.clahe.apply(g), None)
        pts = np.float32([k.pt for k in kp]).reshape(-1, 2) if kp else np.zeros((0, 2), np.float32)
        return pts, des

    def _carta(self, m):
        """Punti SIFT della carta di riferimento: memoria -> disco (pokedata/sift) -> calcolo e salvataggio."""
        key = (m.get("lang", "en"), m["id"])
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        f = DATA / "sift" / f"{key[0]}_{key[1]}.npz"
        feat = None
        try:
            with np.load(f) as z:
                feat = (z["p"], z["d"])
        except Exception:
            img = cv2.imread(str(percorso(m)))
            if img is not None:
                pts, des = self._feat(img)
                if des is not None:
                    feat = (pts, des.astype(np.uint8))
                    try:
                        tmp = f.with_suffix(".tmp")
                        with open(tmp, "wb") as fh:
                            np.savez(fh, p=pts, d=feat[1])
                        os.replace(tmp, f)
                    except Exception:
                        pass
        feat = feat or (None, None)
        self.cache[key] = feat
        if len(self.cache) > 3000:
            self.cache.popitem(last=False)
        return feat

    def _punti(self, q, m):
        """Quanti punti caratteristici coincidono (dopo RANSAC) tra la carta scansionata e la candidata."""
        p2, d2 = self._carta(m)
        p1, des1 = q
        if des1 is None or d2 is None or len(p1) < 8 or len(p2) < 8:
            return 0
        mt = self.bf.knnMatch(des1, d2.astype(np.float32), k=2)
        buoni = [x[0] for x in mt if len(x) == 2 and x[0].distance < 0.75 * x[1].distance]
        if len(buoni) < 8:
            return len(buoni)
        src = p1[[g.queryIdx for g in buoni]].reshape(-1, 1, 2)
        dst = p2[[g.trainIdx for g in buoni]].reshape(-1, 1, 2)
        _, mask = cv2.findHomography(src, dst, cv2.RANSAC, 6.0)
        return int(mask.sum()) if mask is not None else 0

    def match(self, bgr, lang=None, sid=None, n=3):
        """Restituisce le n migliori carte distinte, opzionalmente solo di una lingua e/o di un set (sid)."""
        mask = np.ones(len(self.meta), bool)
        if lang:
            mask &= self.lang_arr == lang
        if sid:
            mask &= self.sid_arr == sid
        idx = np.where(mask)[0]
        if len(idx) == 0:
            return []
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        imgs = [Image.fromarray(rgb), Image.fromarray(cv2.rotate(rgb, cv2.ROTATE_180))]
        v = self.model.encode(imgs, normalize_embeddings=True, convert_to_numpy=True)
        sims = np.full(len(self.meta), -1.0)
        sims[idx] = (self.E[idx] @ v.T).max(axis=1)
        corto = np.argsort(-sims)[:min(CANDIDATI, len(idx))]
        q = self._feat(bgr)
        ris = [{"m": self.meta[i], "sim": float(sims[i]), "inl": self._punti(q, self.meta[i])} for i in corto]
        if max(r["inl"] for r in ris) >= 10:
            ris.sort(key=lambda r: (r["inl"], r["sim"]), reverse=True)    # SIFT affidabile
        else:
            ris.sort(key=lambda r: r["sim"], reverse=True)                # foto troppo scarsa: solo CLIP
        uniche, visti = [], set()
        for r in ris:
            if r["m"]["id"] not in visti:
                visti.add(r["m"]["id"])
                uniche.append(r)
            if len(uniche) == n:
                break
        return uniche


def prezzo(card_id):
    d = get_json(f"{API}/cards/{card_id}", tries=3, timeout=30)
    p = (d or {}).get("pricing") or {}
    cm = p.get("cardmarket") or {}
    for k in ("trend", "avg", "avg30"):
        if cm.get(k) is not None:
            return cm[k], "EUR"
    for tipo in (p.get("tcgplayer") or {}).values():
        if isinstance(tipo, dict) and tipo.get("marketPrice"):
            return tipo["marketPrice"], "USD"
    return None, ""


def registra(matcher, bgr):
    top = matcher.match(bgr)
    best, second = top[0], top[1]
    if best["inl"] >= 15 and best["inl"] >= 1.5 * max(second["inl"], 1):
        stato = "ok"
    elif best["inl"] < 10 and best["sim"] >= SOGLIA_SCORE and best["sim"] - second["sim"] >= SOGLIA_MARGINE:
        stato = "ok"
    else:
        stato = "verifica"
    c = best["m"]
    val, valuta = prezzo(c["id"])
    nuovo = not pathlib.Path(CSV_OUT).exists()
    with open(CSV_OUT, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        if nuovo:
            w.writerow(["data", "id", "nome", "set", "numero", "lingua_indice", "similarita", "punti",
                        "valore", "valuta", "stato", "alternative"])
        alt = " | ".join(f"{r['m']['name']} ({r['m']['set']} {r['m']['number']})" for r in top[1:])
        w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), c["id"], c["name"], c["set"], c["number"],
                    c.get("lang", "en"), f"{best['sim']:.3f}", best["inl"],
                    str(val).replace(".", ",") if val is not None else "", valuta, stato, alt])
    print(f"[{stato}] {c['name']} - {c['set']} #{c['number']} ({c.get('lang', 'en')})  "
          f"sim={best['sim']:.2f} punti={best['inl']}  valore={val} {valuta}")
    return c, best["sim"], val, valuta, stato


# ---------- 3) RILEVAMENTO CARTA ----------
def ordina(p):
    """Ordina i 4 angoli in senso orario partendo da quello in alto a sinistra."""
    c = p.mean(axis=0)
    p = p[np.argsort(np.arctan2(p[:, 1] - c[1], p[:, 0] - c[0]))]
    return np.roll(p, -int(p.sum(axis=1).argmin()), axis=0).astype("float32")


def _maschere(frame, sfondo=None):
    h, w = frame.shape[:2]
    gray = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    ms = [cv2.Canny(gray, lo, hi) for lo, hi in ((30, 90), (50, 150), (80, 200))]
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    ms += [otsu, 255 - otsu,
           cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 5)]
    # differenza di colore dal fondo, stimato dal bordo dell'immagine: vale per sfondi chiari, scuri o colorati
    lab = cv2.cvtColor(cv2.GaussianBlur(frame, (5, 5), 0), cv2.COLOR_BGR2LAB).astype(np.float32)
    b = max(4, int(min(h, w) * 0.04))
    bordo = np.concatenate([lab[:b].reshape(-1, 3), lab[-b:].reshape(-1, 3),
                            lab[:, :b].reshape(-1, 3), lab[:, -b:].reshape(-1, 3)])
    dist = np.linalg.norm(lab - np.median(bordo, axis=0), axis=2)
    ms += [((dist > t) * 255).astype(np.uint8) for t in (12, 20, 32)]
    # bordo giallo della carta: saturazione
    sat = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)[:, :, 1], (5, 5), 0)
    ms.append(cv2.threshold(sat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1])
    # contrasto locale amplificato (CLAHE): serve con bordi grigi su sfondi chiari
    eq = cv2.createCLAHE(3.0, (8, 8)).apply(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
    ms += [cv2.Canny(cv2.GaussianBlur(eq, (5, 5), 0), lo, hi) for lo, hi in ((10, 30), (20, 60))]
    # differenza dallo sfondo vuoto memorizzato (se c'e'): trova la carta anche grigio su grigio
    if sfondo is not None:
        lb = cv2.cvtColor(cv2.GaussianBlur(cv2.resize(sfondo, (w, h)), (5, 5), 0), cv2.COLOR_BGR2LAB).astype(np.float32)
        d = lab - lb
        d -= np.median(d.reshape(-1, 3), axis=0)         # compensa variazioni globali di luce/esposizione
        dd = np.linalg.norm(d, axis=2)
        ms += [((dd > t) * 255).astype(np.uint8) for t in (8, 14, 24)]
    # bordi su ciascun canale colore (non solo sul grigio)
    ms.append(np.maximum.reduce([cv2.Canny(cv2.GaussianBlur(c, (5, 5), 0), 40, 120) for c in cv2.split(frame)]))
    return ms


def riduci_riflessi(img):
    """Cancella i riflessi del flash (macchie bianche isolate) con inpainting; ignora fondi bianchi che toccano i bordi."""
    h, w = img.shape[:2]
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    s = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[:, :, 1]
    n, lab, st, _ = cv2.connectedComponentsWithStats(((g >= 243) & (s < 45)).astype(np.uint8), connectivity=8)
    ok = [i for i in range(1, n) if 15 <= st[i][4] <= 0.05 * h * w and st[i][0] > 0 and st[i][1] > 0
          and st[i][0] + st[i][2] < w and st[i][1] + st[i][3] < h]
    if not ok:
        return img
    m = cv2.dilate(np.isin(lab, ok).astype(np.uint8) * 255, np.ones((7, 7), np.uint8))
    return cv2.inpaint(img, m, 3, cv2.INPAINT_TELEA)


def _cluster(off, ln, tol):
    cl = []
    for i in np.argsort(off):
        if cl and off[i] - cl[-1]["o"] < tol:
            c = cl[-1]
            c["o"] = (c["o"] * c["s"] + off[i] * ln[i]) / (c["s"] + ln[i])
            c["s"] += ln[i]
        else:
            cl.append({"o": float(off[i]), "s": float(ln[i])})
    return cl


def _contenuto(frame, q):
    """Vero se dentro il rettangolo c'e' qualcosa di diverso dal piano intorno (colore o texture): scarta le linee del tavolo."""
    h, w = frame.shape[:2]
    m = np.zeros((h, w), np.uint8)
    cv2.fillPoly(m, [q.astype(np.int32)], 255)
    inn = cv2.erode(m, np.ones((15, 15), np.uint8))
    ring = cv2.dilate(m, np.ones((41, 41), np.uint8)) & ~cv2.dilate(m, np.ones((9, 9), np.uint8))
    if not inn.any() or not ring.any():
        return False
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB).astype(np.float32)
    a, b = lab[inn > 0], lab[ring > 0]
    return bool(np.linalg.norm(a.mean(0) - b.mean(0)) > 6 or a.std(0).sum() > 1.8 * b.std(0).sum() + 6)


def _quad_da_linee(frame):
    """Ricostruisce il rettangolo dai segmenti dei bordi anche se interrotti (riflessi, bordo grigio su fondo chiaro)."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    eq = cv2.createCLAHE(3.0, (8, 8)).apply(gray)
    ed = cv2.dilate(cv2.Canny(cv2.GaussianBlur(eq, (5, 5), 0), 15, 45), np.ones((3, 3), np.uint8))
    ls = cv2.HoughLinesP(ed, 1, np.pi / 180, 50, minLineLength=int(0.2 * min(h, w)), maxLineGap=int(0.05 * max(h, w)))
    if ls is None or len(ls) < 4:
        return None
    L = np.asarray(ls, dtype=np.float32).reshape(-1, 4)     # OpenCV 4 restituisce (N,1,4), OpenCV 5 (N,4)
    ang = np.degrees(np.arctan2(L[:, 3] - L[:, 1], L[:, 2] - L[:, 0])) % 180
    ln = np.hypot(L[:, 2] - L[:, 0], L[:, 3] - L[:, 1])
    hist = np.bincount((ang % 90).astype(int) % 90, weights=ln, minlength=90)
    phi = float(np.argmax(np.convolve(np.r_[hist[-4:], hist, hist[:4]], np.ones(7), "same")[4:-4]))
    r = np.radians(phi)
    u, v = np.array([np.cos(r), np.sin(r)]), np.array([-np.sin(r), np.cos(r)])
    mid = np.c_[(L[:, 0] + L[:, 2]) / 2, (L[:, 1] + L[:, 3]) / 2]
    dA = ((ang - phi + 90) % 180) - 90
    dB = ((ang - phi) % 180) - 90
    A, B = np.abs(dA) < 9, np.abs(dB) < 9
    if A.sum() < 2 or B.sum() < 2:
        return None
    cA, cB = _cluster(mid[A] @ v, ln[A], 8), _cluster(mid[B] @ u, ln[B], 8)
    best, best_s = None, 0
    for i in range(len(cA)):
        for j in range(i + 1, len(cA)):
            for k in range(len(cB)):
                for l in range(k + 1, len(cB)):
                    a1, a2, b1, b2 = cA[i]["o"], cA[j]["o"], cB[k]["o"], cB[l]["o"]
                    wd, ht = abs(a2 - a1), abs(b2 - b1)
                    if min(wd, ht) < 0.18 * min(h, w):
                        continue
                    rt = min(wd, ht) / max(wd, ht)
                    if not 0.62 < rt < 0.80:
                        continue
                    if min(cA[i]["s"], cA[j]["s"]) < 0.3 * ht or min(cB[k]["s"], cB[l]["s"]) < 0.3 * wd:
                        continue                      # ogni lato deve avere almeno un po' di bordo visibile
                    s = (cA[i]["s"] + cA[j]["s"] + cB[k]["s"] + cB[l]["s"]) * max(0.1, 1 - 4 * abs(rt - 0.716))
                    if s > best_s:
                        best_s = s
                        best = np.array([b * u + a * v for a, b in ((a1, b1), (a1, b2), (a2, b2), (a2, b1))], dtype=np.float32)
    return ordina(best) if best is not None and _contenuto(frame, best) else None


def trova_carta(frame, sfondo=None):
    """Prova piu' metodi e tiene il rettangolo piu' grande e piu' simile alle proporzioni di una carta (0.716).
    Se i contorni falliscono, ricostruisce il rettangolo dalle linee dei bordi."""
    frame = riduci_riflessi(frame)
    area_tot = frame.shape[0] * frame.shape[1]
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    best, best_s = None, 0
    for m in _maschere(frame, sfondo):
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k, iterations=2)
        cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            a = cv2.contourArea(c)
            if a < 0.03 * area_tot or a > 0.95 * area_tot:
                continue
            rect = cv2.minAreaRect(c)
            w, h = rect[1]
            if min(w, h) < 1:
                continue
            r = min(w, h) / max(w, h)
            if 0.6 < r < 0.82 and a / (w * h) > 0.85:
                s = a * max(0.1, 1 - 4 * abs(r - 0.716))
                if s > best_s:
                    best, best_s = cv2.boxPoints(rect), s
    if best is not None:
        return ordina(best.astype("float32"))
    try:
        return _quad_da_linee(frame)
    except Exception:
        return None                       # il rilevamento non deve mai far fallire la richiesta


def raddrizza(frame, q):
    if np.linalg.norm(q[0] - q[1]) > np.linalg.norm(q[0] - q[3]):
        q = np.roll(q, -1, axis=0)                      # carta orizzontale -> verticale
    M = cv2.getPerspectiveTransform(q, np.float32([[0, 0], [W, 0], [W, H], [0, H]]))
    return cv2.warpPerspective(frame, M, (W, H))


# ---------- 4) MODALITA' ----------
def riquadro(frame):
    fh, fw = frame.shape[:2]
    h = int(fh * 0.9)
    w = int(h * 0.716)
    return (fw - w) // 2, (fh - h) // 2, w, h


def esito(matcher, card):
    c, s, val, valuta, stato = registra(matcher, card)
    try:
        import winsound
        winsound.Beep(1000 if stato == "ok" else 500, 200)
    except Exception:
        pass
    return f"{c['name']} {val if val is not None else '?'} {valuta} [{stato}]"


def scan_webcam(camera=0):
    matcher = Matcher()
    cap = cv2.VideoCapture(camera, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    stabile, assente, pronta, ultimo, prev = 0, 0, True, "", None
    print("Appoggia una carta su sfondo scuro. Q = esci, SPAZIO = scansiona subito la carta dentro il riquadro bianco.")
    while True:
        ok, frame = cap.read()
        if not ok:
            print("Non riesco a leggere la webcam. Prova:  python pokescan.py scan --camera 1")
            break
        vista = frame.copy()
        x0, y0, w, h = riquadro(frame)
        cv2.rectangle(vista, (x0, y0), (x0 + w, y0 + h), (255, 255, 255), 1)
        q = trova_carta(frame)
        if q is None:
            assente += 1
            stabile, prev = 0, None
            if assente > 15:
                pronta = True
            cv2.putText(vista, "Nessuna carta rilevata", (10, frame.shape[0] - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            assente = 0
            cv2.polylines(vista, [q.astype(int)], True, (0, 255, 0), 2)
            stabile = stabile + 1 if prev is not None and np.abs(q - prev).max() < 8 else 0
            prev = q
            if pronta and stabile >= 10:
                ultimo = esito(matcher, raddrizza(frame, q))
                pronta = False
        cv2.putText(vista, ultimo, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow("pokescan", vista)
        tasto = cv2.waitKey(1) & 0xFF
        if tasto in (ord("q"), 27):
            break
        if tasto == ord(" "):                            # scansione manuale del riquadro bianco
            ultimo = esito(matcher, cv2.resize(frame[y0:y0 + h, x0:x0 + w], (W, H)))
    cap.release()
    cv2.destroyAllWindows()


def scan_cartella(cartella):
    matcher = Matcher()
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
    for p in sorted(pathlib.Path(cartella).iterdir()):
        if p.suffix.lower() not in exts:
            continue
        img = cv2.imdecode(np.fromfile(str(p), dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            continue
        q = trova_carta(img)
        card = raddrizza(img, q) if q is not None else cv2.resize(img, (W, H))
        print(p.name, end=" -> ")
        registra(matcher, card)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("index"); i.add_argument("--lang", default="en")
    s = sub.add_parser("scan"); s.add_argument("--camera", type=int, default=0)
    f = sub.add_parser("folder"); f.add_argument("path")
    a = ap.parse_args()
    if a.cmd == "index":
        build_index(a.lang)
    elif a.cmd == "scan":
        scan_webcam(a.camera)
    else:
        scan_cartella(a.path)
