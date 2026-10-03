# Pokescan

Web app **self-hosted** per riconoscere, catalogare e valutare le tue carte Pokémon: inquadri una carta con la fotocamera del telefono (o carichi una foto), l'app la riconosce confrontandola con le immagini ufficiali, la salva nella tua collezione con la condizione scelta e ne segue il prezzo nel tempo.

- Funziona anche con carte **rovinate**, su sfondi chiari o scuri, con **bordi grigi** e **riflessi del flash**.
- Pensata anche per scansioni in serie, per esempio con un **lanciatore di carte**: la carta successiva viene rilevata senza dover svuotare l'inquadratura.
- Tutti i dati restano **sul tuo server**: nessun account, nessun cloud.
- Interfaccia in italiano; riconosce carte in più lingue (inglese, italiano, francese, tedesco, spagnolo, portoghese, giapponese, coreano, cinese).

> **Progetto non ufficiale.** Non è affiliato né approvato da Nintendo, Creatures, Game Freak, The Pokémon Company, TCGdex, JustTCG, TCGplayer o Cardmarket. Vedi [Crediti e note legali](#crediti-e-note-legali).

## Indice

1. [Funzionalità in dettaglio](#funzionalità-in-dettaglio)
2. [Come funziona il riconoscimento](#come-funziona-il-riconoscimento)
3. [Requisiti](#requisiti)
4. [Installazione](#installazione)
5. [Prima configurazione](#prima-configurazione)
6. [Uso pratico e consigli di scansione](#uso-pratico-e-consigli-di-scansione)
7. [Dove sono i dati: la cartella `pokedata`](#dove-sono-i-dati-la-cartella-pokedata)
8. [Riferimento delle API HTTP](#riferimento-delle-api-http)
9. [Riferimento del codice](#riferimento-del-codice)
10. [Modalità a riga di comando](#modalità-a-riga-di-comando)
11. [Risoluzione dei problemi](#risoluzione-dei-problemi)
12. [Sicurezza e privacy](#sicurezza-e-privacy)
13. [Crediti e note legali](#crediti-e-note-legali)
14. [Licenza](#licenza)

---

## Funzionalità in dettaglio

L'interfaccia ha tre schede nella barra in basso: **Scansiona**, **Set** e **Collezione**.

### Scheda «Scansiona»

| Controllo | Cosa fa |
|---|---|
| **Lingua / Pacchetto** | Restringe la ricerca a una lingua e/o a un set. «Auto» cerca in tutte le lingue e in tutti i pacchetti. Restringere rende il riconoscimento più veloce e più preciso. |
| **Anteprima fotocamera** | Mostra l'immagine live con un riquadro verde attorno alla carta rilevata e una scritta di stato («Carta rilevata», «Tieni ferma la carta…», «Riconoscimento in corso…»). |
| **Zoom** | Cursore da 1× in su. Usa lo **zoom ottico** della fotocamera se disponibile, altrimenti uno **zoom digitale** (indicato dalla scritta «digitale»). Il valore scelto viene ricordato. |
| **Flash** | Il pulsante compare **solo** se il browser e la fotocamera supportano la torcia (tipicamente Chrome su Android). Parte sempre spento. |
| **Sfondo vuoto** | Con la fotocamera ferma e **senza carte**, memorizza com'è il piano. Da quel momento la carta viene cercata anche per differenza dallo sfondo, utile con carte grigie su piani chiari. Va rifatto se sposti il telefono, cambi lo zoom o riavvii il server. Un secondo tocco lo rimuove. |
| **Salvataggio automatico + condizione predefinita** | Se attivo, quando il riconoscimento è «sicuro» la carta viene salvata subito con la condizione scelta nel menu accanto, senza premere Conferma. Le carte dubbie aprono comunque la scheda di conferma. |
| **Scansione automatica** | Se attiva, l'app rileva da sola una carta ferma nell'inquadratura e la scansiona. Se disattivata, si usa «Scansiona ora». |
| **Scansiona ora** | Cattura subito 3 fotogrammi e li riconosce, senza aspettare il rilevamento. Utile con carte difficili da rilevare o copie identiche consecutive. |
| **Da galleria** | Riconosce una foto già esistente (o ne scatta una con la fotocamera del telefono). Funziona anche senza HTTPS. |
| **Cerca per nome** | Salta il riconoscimento: cerchi la carta per nome (anche parziale) tra quelle indicizzate, con gli stessi filtri lingua/set. |

**Scheda di conferma.** Dopo il riconoscimento si apre un foglio con la carta proposta, un'etichetta di affidabilità («Riconoscimento sicuro», «Da verificare», «Alternativa», «Scelta manuale»), i tasti della **condizione** (NM, LP, MP, HP, DMG; NM è preselezionata) e due azioni:

- **Conferma**: salva la carta.
- **Correggi**: mostra le altre possibilità trovate (fino a 6 candidati) e un campo di ricerca per nome.

Ogni conferma o correzione viene registrata: la scheda Collezione mostra la **percentuale di riconoscimenti esatti** (la prima proposta era giusta) sul totale delle scansioni.

**Scansioni in serie.** Dopo un salvataggio l'app continua a osservare la miniatura della carta: se arriva una carta *diversa* (anche senza che l'inquadratura si svuoti) riparte da sola. Due copie **identiche** una dopo l'altra non sono distinguibili: in quel caso usa «Scansiona ora».

### Scheda «Collezione»

- **Riepilogo in alto**: numero di carte e **valore totale in dollari** (prezzi TCGplayer via JustTCG, per la condizione di ogni copia). Le carte senza prezzo non entrano nel totale e vengono contate («N senza prezzo TCG»).
- **Raggruppamento**: una tessera per ogni carta (stessa carta e stessa lingua) con il badge **×N** se ne hai più copie, anche di condizioni diverse.
- **Filtri e ordine**: nome, rarità, condizione, fascia di prezzo (min/max) e ordinamento (più recenti, prezzo decrescente/crescente, nome).
- **Aggiorna prezzi**: forza subito l'aggiornamento giornaliero (basta un tocco).
- **Esporta Excel**: scarica `collezione.csv` (separatore `;`, codifica UTF-8 con BOM per Excel) con data, id, nome, set, numero, lingua, rarità, quantità, valore, valuta, stato e condizione.
- **Aggiorna elenco carte**: cerca nuove carte uscite e le aggiunge agli indici (vedi [Aggiornamenti automatici](#aggiornamenti-automatici-e-backup)).
- **Barra informazioni**: ultimo aggiornamento di elenco carte, prezzi e backup, e percentuale di riconoscimento.
- **Esci**: chiude la sessione (ha effetto quando il login è attivo).

**Dettaglio carta** (tocca una tessera):

- una riga per ogni condizione posseduta, con **menu condizione** (sposta *una* copia in un'altra condizione), pulsanti **− / +** per la quantità e **✕** per eliminare;
- prezzo in dollari della condizione e valore totale delle copie;
- **grafico dei prezzi** con **una linea per ogni condizione** posseduta (colori distinti, legenda con l'ultimo prezzo);
- se la carta non è collegata a JustTCG, mostra al suo posto lo **storico Cardmarket in euro**.

### Scheda «Set»

Elenco dei pacchetti (per lingua) in cui hai almeno una carta, con logo, **completamento** (carte possedute / totale del set) e barra di avanzamento. Toccando un set vedi le carte possedute ordinate per numero.

### Prezzi

Due fonti, usate per scopi diversi:

| Fonte | Valuta | Uso nell'app |
|---|---|---|
| **JustTCG** (prezzi in stile TCGplayer, per condizione) | USD | Prezzo mostrato sulle tessere, valore della collezione, grafico multi-linea. Richiede una **chiave API gratuita** (facoltativa). |
| **TCGdex / Cardmarket** | EUR | Rarità e storico di riserva. Non richiede chiave. |

Senza chiave JustTCG l'app funziona lo stesso, ma senza prezzi in dollari né grafici per condizione.

**Collegamento a JustTCG.** Al primo salvataggio di una carta l'app la cerca su JustTCG usando il **nome inglese**, tiene i risultati con lo **stesso numero** e sceglie il set per **codice** (es. `me04`) o per somiglianza del nome; se resta una sola candidata la accetta. Il collegamento si salva una volta sola. Le carte in altre lingue usano l'equivalente inglese. I tentativi falliti vengono ripetuti dopo 3 giorni e a ogni riavvio.

**Scelta del prezzo.** Se una carta esiste in più stampe, si usa nell'ordine *Normal*, *Holofoil*, *Reverse Holofoil* (poi le altre). Le condizioni sono mappate su Near Mint, Lightly Played, Moderately Played, Heavily Played, Damaged. Per le condizioni senza quotazione su JustTCG (frequente per MP, HP e DMG sulle carte economiche) compare «—» e non si applicano percentuali di stima.

**Storico e limiti.** Al primo collegamento si richiede lo storico disponibile (fino a 90 giorni, se il piano lo consente); poi ogni giorno si aggiunge un punto, aggiornando le carte a **gruppi di 20 per richiesta**. Il piano gratuito ha limiti giornalieri, mensili e al minuto: l'app distanzia le richieste (una ogni ~6,5 secondi) e, dopo un errore *429*, attende 40 secondi e riprova una volta. Controlla i limiti aggiornati sul sito di JustTCG. Se hai molte carte nuove, i prezzi possono arrivare in più giorni.

### Aggiornamenti automatici e backup

Un processo in background controlla ogni ora:

- **Backup**: una copia coerente del database al giorno in `pokedata/backup/`, conservando le ultime 14.
- **Prezzi**: una volta al giorno (se la collezione non è vuota) aggiorna rarità e prezzi Cardmarket e poi i prezzi JustTCG.
- **Elenco carte**: ogni 7 giorni cerca le carte nuove in tutte le lingue indicizzate e le aggiunge agli indici scaricando solo quelle mancanti. Si può forzare dal pulsante «Aggiorna elenco carte».

### Accesso protetto

Con una password impostata (`python app.py --setpw`) l'app richiede il login: sessione di 30 giorni, cookie `HttpOnly`/`SameSite=Lax`, password salvata solo come hash, pausa di 1 secondo dopo un errore e blocco dopo 5 tentativi falliti per indirizzo in 10 minuti (30 complessivi). **Senza password l'app è aperta a chiunque raggiunga la porta**: all'avvio stampa un avviso.

---

## Come funziona il riconoscimento

La pipeline ha tre fasi.

### 1. Rilevamento e raddrizzamento della carta (`trova_carta`, `raddrizza`)

Il browser invia un fotogramma ridotto (480 px) circa ogni 0,35 secondi a `/api/rileva`. Il server cerca il rettangolo della carta provando **molti metodi insieme** e tenendo il candidato più grande e più vicino alle proporzioni di una carta (circa 0,716):

- bordi (Canny) a tre soglie, anche dopo equalizzazione del contrasto locale (CLAHE) per i bordi grigi poco contrastati;
- soglie di luminosità (Otsu, inversa, adattiva);
- **differenza di colore dallo sfondo** stimato dai bordi dell'immagine (funziona con sfondi chiari, scuri o colorati);
- saturazione (bordo giallo) e bordi sui singoli canali colore;
- **differenza dallo sfondo vuoto memorizzato**, se presente.

Prima di tutto questo i **riflessi del flash** (macchie bianche isolate, che non toccano i bordi dell'immagine) vengono cancellati con inpainting. Se nessun contorno è valido, un **ripiego a linee** ricostruisce il rettangolo dai segmenti dei bordi anche se interrotti, e lo accetta solo se dentro c'è qualcosa di diverso dal piano circostante (così le fughe delle piastrelle non diventano carte). La carta viene poi **raddrizzata** in un'immagine 300×420 con una trasformazione prospettica.

Quando la carta è ferma per 2 controlli consecutivi parte la scansione. Il server calcola anche una **miniatura 16×22** della carta: è ciò che permette di accorgersi che è arrivata una carta diversa.

### 2. Riconoscimento (`Matcher.match`)

1. **CLIP** (modello `clip-ViT-B-32`) trasforma la carta, dritta e ruotata di 180°, in un vettore e lo confronta con quelli di tutte le carte indicizzate (filtrando per lingua/set se richiesto). Restano i **40 candidati** più simili.
2. Per ogni candidato si confrontano i **punti caratteristici SIFT** con quelli dell'immagine ufficiale e si contano quelli coerenti dopo **RANSAC** (omografia). Questo distingue ristampe e carte quasi uguali.
3. Se i punti coerenti sono sufficienti (almeno 10) si ordina per punti, altrimenti solo per similarità CLIP (foto troppo scarsa).

### 3. Fusione dei fotogrammi e affidabilità (`fondi`, `stato_di`)

Per ogni scansione si catturano **fino a 3 fotogrammi** a 1280 px, a ~250 ms l'uno dall'altro; i risultati vengono mediati. Il risultato è **«sicuro»** se:

- il primo candidato ha almeno 15 punti SIFT coerenti **e** almeno 1,5 volte quelli del secondo; oppure
- (foto povera, meno di 10 punti) la similarità CLIP è almeno 0,80 con un margine di almeno 0,02 sul secondo;

e, se i fotogrammi sono più di uno, la maggioranza concorda sul primo posto. Altrimenti è **«da verificare»**. Le soglie sono costanti in `pokescan.py` (`SOGLIA_SCORE`, `SOGLIA_MARGINE`) e in `stato_di`.

---

## Requisiti

- **Server**: qualsiasi macchina Linux/Windows/macOS con **Docker** (consigliato) oppure Python 3.10+. Il riconoscimento usa PyTorch su CPU: conta indicativamente **1–2 GB di RAM** per il modello e gli indici; più processori rendono più veloce il riconoscimento.
- **Spazio**: l'indice di una lingua (immagini ufficiali, punti SIFT, vettori) occupa dell'ordine di **1 GB**; i tempi della prima indicizzazione vanno da decine di minuti a qualche ora, secondo connessione e CPU.
- **Client**: un browser moderno. Per la fotocamera **live** serve un contesto sicuro (**HTTPS** o `localhost`); senza HTTPS usa «Da galleria».
- **Internet** sul server per scaricare dati e immagini (TCGdex) e, se vuoi i prezzi in dollari, per JustTCG.
- **Facoltativo**: chiave API gratuita di JustTCG.

---

## Installazione

### Con Docker (consigliato)

```bash
git clone <URL-DEL-TUO-REPOSITORY> pokescan
cd pokescan
docker compose up -d --build
```

L'app è raggiungibile su `http://IP-DEL-SERVER:8085`. La cartella `pokedata/` viene creata accanto al progetto e contiene tutti i tuoi dati.

Al primo avvio l'app **non ha ancora le carte**: costruisci l'indice (vedi sotto).

### Senza Docker

```bash
python -m venv .venv && source .venv/bin/activate        # su Windows: .venv\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
gunicorn -b 0.0.0.0:8085 -w 1 --threads 2 --timeout 180 app:app
```

Usa **un solo worker** (`-w 1`): il modello e gli indici stanno in memoria e il rilevamento dello sfondo è condiviso.

---

## Prima configurazione

### 1. Costruire l'indice delle carte (obbligatorio, una tantum per lingua)

```bash
# con Docker
docker compose run --rm pokescan python pokescan.py index --lang en
docker compose run --rm pokescan python pokescan.py index --lang it
# senza Docker
python pokescan.py index --lang it
```

Scarica l'elenco dei set, le immagini ufficiali e calcola i vettori. Puoi indicizzare più lingue (`en`, `it`, `fr`, `de`, `es`, `pt`, `ja`, `ko`, `zh-tw`, `zh-cn`, …): lo scan le usa tutte insieme. Se viene interrotto, le immagini già scaricate non vengono riscaricate. Poi riavvia il server (`docker compose restart`).

Indicizza **la lingua delle tue carte**: una carta italiana viene riconosciuta molto meglio confrontandola con la sua versione italiana (testo e cornice uguali).

### 2. Impostare la password (fortemente consigliato)

```bash
docker compose exec pokescan python app.py --setpw
```

Ti chiede nome utente e password (almeno 8 caratteri). Il login si attiva subito.

### 3. Chiave JustTCG (facoltativa, per i prezzi in dollari)

Registrati gratuitamente su JustTCG, copia la chiave e salvala **senza scriverla in file o nella cronologia**:

```bash
docker compose exec pokescan python app.py --setkey
```

La chiave viene chiesta in modo nascosto e salvata in `pokedata/justtcg.key`. In alternativa si può usare la variabile d'ambiente `JUSTTCG_API_KEY`. Non serve riavviare. Poi, in Collezione, tocca «Aggiorna prezzi» **una sola volta** e attendi qualche minuto.

### 4. HTTPS (per la fotocamera live da telefono)

I browser mobili consentono la fotocamera live solo in HTTPS. Metti l'app dietro un reverse proxy con certificato (Caddy, nginx, Traefik o uno già presente sul tuo server). Esempio con Caddy:

```
pokescan.example.com {
    reverse_proxy localhost:8085
}
```

Se esponi l'app fuori dalla rete di casa, **attiva il login** e non pubblicarla direttamente su Internet senza proxy e HTTPS.

---

## Uso pratico e consigli di scansione

- **Luce**: preferisci luce **morbida e laterale** (una lampada a 45°) al flash diretto, che crea riflessi che nessun software recupera del tutto. Se usi il flash, inclina leggermente la fotocamera.
- **Piano**: opaco e uniforme. Con carte dal bordo grigio su piani chiari, usa «Sfondo vuoto».
- **Stabilità**: telefono su un supporto fisso; dopo aver memorizzato lo sfondo non muoverlo né cambiare zoom.
- **Lanciatore di carte**: attiva «Scansione automatica» e «Salvataggio automatico», scegli la condizione predefinita e lascia la fotocamera ferma. Le carte dubbie si fermano sulla scheda di conferma.
- **Carte rovinate**: il confronto si basa sull'illustrazione, quindi pieghe e usura pesano poco; se il risultato è «da verificare» controlla le alternative.
- **Copie identiche consecutive**: usa «Scansiona ora» per la seconda.

---

## Dove sono i dati: la cartella `pokedata`

Tutto ciò che è tuo sta qui. **Non va mai pubblicata nel repository** (è già nel `.gitignore`).

| File / cartella | Contenuto |
|---|---|
| `collezione.db` (+ `-wal`, `-shm`) | Database SQLite: collezione, storico prezzi, collegamenti JustTCG, registro delle correzioni, info sui set. Usa la modalità WAL: se lo copi a mano, copia anche i file `-wal` e `-shm` (oppure usa i backup). |
| `backup/` | Una copia coerente al giorno, ultime 14. |
| `img/` | Immagini ufficiali scaricate (cache locale servita dall'app). |
| `emb*.npy`, `meta*.json` | Indici dei vettori CLIP e metadati delle carte, uno per lingua (`emb.npy` è l'inglese). |
| `sift/` | Cache dei punti SIFT delle carte di riferimento. |
| `hf/` | Cache del modello CLIP (con Docker). |
| `auth.json` | Nome utente e **hash** della password. |
| `secret.key` | Chiave per firmare le sessioni (generata automaticamente). |
| `justtcg.key` | Chiave API JustTCG, se impostata. |
| `ultimo_agg.txt`, `ultimo_indice.txt` | Date dell'ultimo aggiornamento di prezzi ed elenco carte. |

Per un backup completo copia l'intera cartella `pokedata/` a server fermo (o i soli file di `backup/` più gli indici, che si possono anche ricostruire).

---

## Riferimento delle API HTTP

Con il login attivo tutte le rotte (tranne `/login` e `/logout`) richiedono la sessione; le chiamate `/api/*` rispondono sempre in JSON, anche in caso di errore (`{"errore": "..."}`).

| Metodo e percorso | Descrizione |
|---|---|
| `GET /` | Pagina dell'app. |
| `GET/POST /login`, `GET /logout` | Accesso e uscita. |
| `GET /img/<lang>/<id>` | Immagine ufficiale della carta dalla cache locale. |
| `GET /api/filtri` | Lingue e set disponibili per i filtri. |
| `GET /api/stato` | Date di aggiornamento, numero di carte indicizzate, ultimo backup, statistiche di riconoscimento. |
| `POST /api/rileva` | Riceve un fotogramma (`foto`) e restituisce se c'è una carta, i quattro angoli normalizzati e la miniatura. |
| `POST /api/scan` | Riceve fino a 3 fotogrammi (`foto`, più `lang`/`set` opzionali) e restituisce candidati, stato («ok»/«verifica») e punti. |
| `POST /api/sfondo`, `DELETE /api/sfondo` | Memorizza / rimuove l'immagine dello sfondo vuoto. |
| `GET /api/cerca?q=&lang=&set=` | Ricerca per nome tra le carte indicizzate (max 30 risultati). |
| `POST /api/salva` | Salva una carta (con `condiz`); risponde subito, il resto avviene in background. |
| `GET /api/collezione` | Righe della collezione con prezzo USD, totale e conteggio senza prezzo. |
| `POST /api/qta/<riga>` | Aggiunge o toglie copie (`{"d": 1}` o `{"d": -1}`); a zero la riga sparisce. |
| `POST /api/condizione/<riga>` | Sposta una copia in un'altra condizione (`{"c": "LP"}`). |
| `DELETE /api/carta/<riga>` | Elimina la riga. |
| `GET /api/tcg/<id>` | Serie di prezzi JustTCG per condizione posseduta e stato del collegamento. |
| `GET /api/storico/<id>` | Storico Cardmarket di riserva. |
| `GET /api/set` | Set posseduti con completamento. |
| `POST /api/aggiorna` | Avvia l'aggiornamento dei prezzi. |
| `POST /api/aggiorna-carte` | Avvia la ricerca di carte nuove. |
| `POST /api/backup` | Crea subito un backup. |
| `GET /api/correzioni` | Statistiche e errori di riconoscimento più frequenti. |
| `GET /api/jt-log` | Ultimi eventi dell'integrazione JustTCG e tempi di riconoscimento/salvataggio (diagnostica; non contiene la chiave). |
| `GET /export.csv` | Esporta la collezione. |

---

## Riferimento del codice

### `pokescan.py` — motore di riconoscimento

| Funzione / classe | Ruolo |
|---|---|
| `file_indice(lang)`, `percorso(m)` | Nomi dei file di indice per lingua e percorso dell'immagine di una carta. |
| `get_json(url, …)` | GET JSON con tentativi ripetuti e attesa crescente. |
| `build_index(lang)` | Scarica set e immagini di una lingua, calcola i vettori CLIP e salva l'indice. |
| `aggiorna_indice(matcher, lang, lock)` | Aggiunge all'indice solo le carte nuove. |
| `Matcher` | Carica gli indici (`carica`), calcola i vettori e confronta (`match`). |
| `Matcher._feat`, `_carta`, `_punti` | Punti SIFT della scansione; punti della carta di riferimento (memoria → disco → calcolo, cache LRU da 3000); numero di punti coerenti dopo RANSAC. |
| `prezzo(id)`, `registra`, `esito` | Prezzo e salvataggio su CSV per la modalità a riga di comando. |
| `ordina(p)` | Ordina i 4 angoli in senso orario dall'alto a sinistra. |
| `_maschere(frame, sfondo)` | Genera le maschere candidate per trovare la carta. |
| `riduci_riflessi(img)` | Cancella i riflessi del flash con inpainting. |
| `_cluster`, `_quad_da_linee`, `_contenuto` | Ripiego a linee: raggruppa i segmenti, ricostruisce il rettangolo, verifica che dentro ci sia una carta. |
| `trova_carta(frame, sfondo)` | Rilevamento completo; restituisce i 4 angoli o `None`. |
| `raddrizza(frame, q)` | Prospettiva → immagine 300×420 dritta. |
| `riquadro`, `scan_webcam`, `scan_cartella` | Modalità a riga di comando. |

### `app.py` — server

| Funzione | Ruolo |
|---|---|
| `_key`, `auth`, `_tok`, `_ip`, `_bloccato`, `protezione`, `login`, `logout` | Login, sessioni e limite ai tentativi. |
| `sid(id)`, `costruisci_sets` | Codice del set ricavato dall'id carta; elenco dei set per lingua. |
| `db`, `q`, `q_molti` | Connessione SQLite (WAL, creazione e migrazione delle tabelle), query singola, scrittura di molte righe in una transazione. |
| `dettagli`, `punto` | Rarità e prezzo Cardmarket da TCGdex; punti dello storico di riserva. |
| `jt_key`, `jtl`, `jt_get` | Chiave JustTCG, registro eventi, richieste con passo minimo e ripetizione su 429. |
| `norm`, `jt_collega` | Normalizza testi; collega una carta a JustTCG (nome, numero, codice o nome del set). |
| `jt_salva`, `conds_di`, `jt_card`, `jt_tutte` | Salva prezzi e storico; condizioni possedute; aggiorna una carta; aggiornamento giornaliero a gruppi di 20. |
| `aggiorna`, `backup`, `_bk`, `ciclo` | Aggiornamento prezzi, backup coerente, ciclo orario in background. |
| `aggiorna_carte`, `ciclo_carte` | Ricerca periodica di carte nuove e ricarica degli indici. |
| `meta_set` | Nome, logo e totale delle carte di un set, salvati una volta. |
| `imgs_in`, `img_in`, `fondi`, `stato_di`, `cand` | Lettura delle immagini, fusione dei fotogrammi, giudizio di affidabilità, formato dei candidati. |
| `dopo_salvataggio` | Completa in background il salvataggio (rarità, prezzo, storico). |
| `errore_json` | Risponde sempre in JSON alle chiamate `/api`. |

### `static/index.html` — interfaccia

| Funzione | Ruolo |
|---|---|
| `go`, `toast`, `stato` | Navigazione tra le schede, messaggi, testo di stato. |
| `cam`, `fermaCam`, `iniZoom`, `applicaZoom`, `iniFlash` | Avvio e arresto della fotocamera, zoom ottico/digitale, torcia. |
| `frame`, `tre`, `disegna` | Cattura dei fotogrammi (uno o tre) e disegno del riquadro verde. |
| `loop`, `corr`, `riparti` | Ciclo di rilevamento, confronto delle miniature, ripartenza dopo il salvataggio. |
| `scansiona`, `renderConf`, `altri`, `cerca`, `conferma`, `salvaAuto`, `chiudi` | Riconoscimento, scheda di conferma, alternative, ricerca per nome, salvataggio manuale e automatico. |
| `caricaColl`, `grid`, `dettaglio`, `grafico`, `graficoTcg` | Collezione raggruppata, filtri, dettaglio per condizione, grafici (USD per condizione; euro di riserva). |
| `caricaSet`, `renderSet`, `initFiltri`, `fillSets`, `stInfo` | Scheda Set, filtri lingua/pacchetto, barra informazioni. |

---

## Modalità a riga di comando

`pokescan.py` può essere usato anche senza server web, ed è meno curato della web app:

```bash
python pokescan.py index --lang it       # costruisce l'indice di una lingua
python pokescan.py scan [--camera 1]     # webcam: Q esce, SPAZIO scansiona il riquadro bianco
python pokescan.py folder PERCORSO       # tutte le immagini di una cartella
```

Scrive i risultati in `collezione.csv`. Su Windows lo script apre una finestra OpenCV e può emettere un segnale acustico a ogni carta.

---

## Risoluzione dei problemi

| Sintomo | Cosa controllare |
|---|---|
| «Indice mancante» all'avvio | Costruisci l'indice (`pokescan.py index --lang …`). |
| Primo avvio molto lento | Normale: scarica e carica il modello CLIP. L'avviso su `HF_TOKEN` è innocuo. |
| Fotocamera non parte | Serve HTTPS (o `localhost`) e il permesso del browser; in alternativa usa «Da galleria». |
| «Il server ha risposto in modo non valido (codice N)» | Apri `/api/jt-log`: gli errori del server sono annotati lì. |
| La carta non viene rilevata | Più contrasto con lo sfondo, luce morbida, «Sfondo vuoto». Come ultima risorsa «Scansiona ora». |
| Riconoscimento sbagliato | Indicizza la lingua giusta; restringi per lingua/set; controlla riflessi e messa a fuoco; guarda le alternative in «Correggi». |
| Nessun prezzo in dollari | Chiave JustTCG impostata? Guarda `/api/jt-log`: limite *429* raggiunto, carta non trovata, oppure condizione senza quotazione (MP/HP/DMG). |
| Salvataggio lento | Disco lento o molte scritture: il database usa WAL e il resto avviene in background; confronta i tempi in `/api/jt-log`. |
| Poca memoria | Un solo worker, evita altri servizi pesanti; riduci le lingue indicizzate. |

---

## Sicurezza e privacy

- **Nessun segreto nel codice.** Chiave JustTCG, hash della password e chiave di sessione vivono solo in `pokedata/` (file con permessi `600`). Non committare mai `pokedata/`, `.env`, `*.key`, `auth.json`, `secret.key`.
- **Attiva il login** e non esporre l'app direttamente su Internet: usa un reverse proxy con HTTPS.
- Le foto inviate per il riconoscimento sono elaborate in memoria e **non vengono salvate**; lo sfondo vuoto resta solo in memoria fino al riavvio.
- L'app contatta solo TCGdex (dati, immagini) e, se configurato, JustTCG (prezzi); il modello CLIP viene scaricato una volta da Hugging Face.
- Se pubblichi un fork, controlla con `git status` che `pokedata/` non sia tracciata.

## Crediti e note legali

- Dati e immagini delle carte: **TCGdex**, scaricati a runtime sul tuo server. Questo repository **non contiene** immagini né dati di carte.
- Prezzi in dollari: **JustTCG**, con la tua chiave personale e nel rispetto dei suoi termini di servizio e dei limiti del piano.
- Modello di riconoscimento: **CLIP ViT-B/32** (OpenAI) tramite *sentence-transformers*; visione artificiale con **OpenCV**; web con **Flask**.
- *Pokémon* e i nomi, le immagini e i marchi delle carte appartengono ai rispettivi titolari (Nintendo, Creatures, Game Freak, The Pokémon Company). Questo progetto è indipendente e **non affiliato**.
- I prezzi sono **indicativi**, non una stima ufficiale né una consulenza.
- Rispetta i termini d'uso di ciascun servizio e le norme locali sui dati.
