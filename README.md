# Pokescan

Web app **self-hosted** per riconoscere, catalogare, valutare e **vendere** le tue carte Pokémon: inquadri una carta con la fotocamera del telefono (o carichi una foto), l'app la riconosce confrontandola con le immagini ufficiali, la salva nella tua collezione con condizione e finitura, ne segue il prezzo nel tempo e, se vuoi, ti aiuta a pubblicare le doppie su CardTrader. Gestisce anche una raccolta di **prodotti sigillati** (booster, box, ETB…) con i prezzi di mercato.

- Funziona anche con carte **rovinate**, su sfondi chiari o scuri, con **bordi grigi** e **riflessi del flash**.
- Pensata anche per scansioni in serie, per esempio con un **lanciatore di carte**: la carta successiva viene rilevata senza dover svuotare l'inquadratura.
- **Prezzi** in dollari (JustTCG, per condizione e finitura) e in euro (Cardmarket e CardTrader), con grafici dello storico.
- Tutti i dati restano **sul tuo server**: nessun account, nessun cloud.
- Interfaccia in italiano; riconosce carte in più lingue (inglese, italiano, francese, tedesco, spagnolo, portoghese, giapponese, coreano, cinese).

> **Progetto non ufficiale.** Non è affiliato né approvato da Nintendo, Creatures, Game Freak, The Pokémon Company, TCGdex, JustTCG, TCGplayer, Cardmarket o CardTrader. Vedi [Crediti e note legali](#crediti-e-note-legali).

## Indice

1. [Funzionalità in dettaglio](#funzionalità-in-dettaglio)
2. [Come funziona il riconoscimento](#come-funziona-il-riconoscimento)
3. [Requisiti](#requisiti)
4. [Installazione](#installazione)
5. [Prima configurazione](#prima-configurazione)
6. [Aggiornare a una nuova versione](#aggiornare-a-una-nuova-versione)
7. [Uso pratico e consigli di scansione](#uso-pratico-e-consigli-di-scansione)
8. [Dove sono i dati: la cartella `pokedata`](#dove-sono-i-dati-la-cartella-pokedata)
9. [Riferimento delle API HTTP](#riferimento-delle-api-http)
10. [Riferimento del codice](#riferimento-del-codice)
11. [Modalità a riga di comando](#modalità-a-riga-di-comando)
12. [Risoluzione dei problemi](#risoluzione-dei-problemi)
13. [Sicurezza e privacy](#sicurezza-e-privacy)
14. [Crediti e note legali](#crediti-e-note-legali)

---

## Funzionalità in dettaglio

La navigazione è nel menu **☰** in alto a sinistra. Le voci sono sette:

| Voce | A cosa serve |
|---|---|
| **Scansiona** | Riconosce una carta con la fotocamera o da una foto e la salva nella collezione. |
| **Prezzo** | Riconosce una carta e mostra i prezzi **senza salvarla**. |
| **Set** | I pacchetti in cui hai carte, con il completamento. |
| **Mancanti** | Le carte che ti mancano nei set che hai già iniziato. |
| **Vendi** | Le copie doppie, con il prezzo consigliato e la pubblicazione su CardTrader. |
| **Sealed** | La raccolta dei prodotti sigillati, con prezzi di mercato per lingua e storico. |
| **Collezione** | Tutte le carte, il valore totale, i filtri e l'esportazione. |

### «Scansiona»

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

**Scheda di conferma.** Dopo il riconoscimento si apre un foglio con la carta proposta, un'etichetta di affidabilità («Riconoscimento sicuro», «Da verificare», «Alternativa», «Scelta manuale»), la **condizione** (NM, LP, MP, HP, DMG; NM è preselezionata), la **finitura** (Standard, Holo, Reverse Holo) e tre azioni:

- **Conferma**: salva la carta.
- **Correggi**: mostra le altre possibilità trovate (fino a 6 candidati) e un campo di ricerca per nome.
- **Scarta**: chiude senza salvare.

Ogni conferma o correzione viene registrata: la scheda Collezione mostra la **percentuale di riconoscimenti esatti** (la prima proposta era giusta) sul totale delle scansioni.

**Lingua della carta.** Se una carta esiste solo in alcune lingue su TCGdex, l'app te lo segnala e puoi scegliere la lingua reale della tua copia.

**Carte senza immagine.** TCGdex elenca alcune carte (tipicamente promo) senza immagine di riferimento: non si possono riconoscere, ma si possono cercare per nome. Quando salvi una di queste, o una carta in una lingua che non ha ancora l'immagine, puoi spuntare «usa la foto appena scattata per riconoscerla in futuro»: la foto raddrizzata diventa l'immagine di riferimento nell'indice di quella lingua.

**Scansioni in serie.** Dopo un salvataggio l'app continua a osservare la miniatura della carta: se arriva una carta *diversa* (anche senza che l'inquadratura si svuoti) riparte da sola. Due copie **identiche** una dopo l'altra non sono distinguibili: in quel caso usa «Scansiona ora».

### «Prezzo»

Stessa fotocamera e stessi controlli di «Scansiona», ma **senza salvare nulla**: riconosci una carta e vedi subito

- la tabella **JustTCG** in dollari, per finitura e condizione (solo le colonne per cui esiste una quotazione);
- i prezzi **Cardmarket** in euro (tendenza, minimo, media a 7 e a 30 giorni).

Con «Correggi» puoi scegliere un'altra candidata o cercare per nome. I risultati JustTCG vengono riusati per 30 minuti per risparmiare richieste. Senza chiave JustTCG compaiono solo i prezzi Cardmarket.

### «Set»

Elenco dei pacchetti (per lingua) in cui hai almeno una carta, con logo, **completamento** (carte possedute / totale del set) e barra di avanzamento. Toccando un set vedi le carte possedute ordinate per numero; con **Seleziona** puoi toccare più carte ed eliminarle insieme.

### «Mancanti»

Per ogni set (e lingua) in cui possiedi almeno una carta: quante ne hai su quante ne esistono e **quante ne mancano**. Toccando un set vedi le carte mancanti con immagine, numero e rarità; toccando una carta si apre la scheda dei **prezzi** (come in «Prezzo»), utile per decidere cosa cercare. I loghi dei set vengono scaricati e salvati in locale.

### «Collezione»

- **Riepilogo in alto**: numero di carte e **valore totale in dollari** (prezzi JustTCG per la condizione e la finitura di ogni copia). Le carte senza prezzo non entrano nel totale e vengono contate («N senza prezzo TCG»).
- **Raggruppamento**: una tessera per ogni carta (stessa carta e stessa lingua) con il badge **×N** se ne hai più copie, anche di condizioni o finiture diverse.
- **Filtri e ordine**: nome, rarità, condizione, fascia di prezzo (min/max) e ordinamento (più recenti, prezzo decrescente/crescente, nome).
- **Aggiorna prezzi**: forza subito l'aggiornamento giornaliero (basta un tocco).
- **Esporta Excel**: scarica `collezione.csv` (separatore `;`, codifica UTF-8 con BOM per Excel) con data, id, nome, set, numero, lingua, rarità, quantità, valore, valuta, stato, condizione e finitura.
- **Aggiorna elenco carte**: cerca nuove carte uscite e le aggiunge agli indici (vedi [Aggiornamenti automatici](#aggiornamenti-automatici-e-backup)).
- **Backup ora**: crea subito una copia del database.
- **Barra informazioni**: ultimo aggiornamento di elenco carte, prezzi e backup, percentuale di riconoscimento e versione.
- **Esci**: chiude la sessione (ha effetto quando il login è attivo).

**Dettaglio carta** (tocca una tessera):

- una riga per ogni combinazione di condizione e finitura posseduta, con **menu condizione** e **menu finitura** (spostano *una* copia; se esiste già una riga uguale le copie si uniscono), pulsanti **− / +** per la quantità e **✕** per eliminare;
- prezzo in dollari e valore totale delle copie;
- **grafico dei prezzi** con **una linea per ogni condizione/finitura** posseduta (colori distinti, legenda con l'ultimo prezzo);
- se la carta non è collegata a JustTCG, mostra al suo posto lo **storico Cardmarket in euro**.

### «Vendi» (CardTrader)

Serve il [token CardTrader](#4-token-cardtrader-facoltativo-per-vendi-e-sealed). La scheda elenca le tue copie raggruppate per **carta, lingua, condizione e finitura**.

- **Mapping automatico**: per ogni carta l'app cerca su CardTrader il prodotto corrispondente (per nome, numero e codice del set) e salva il collegamento. Se non lo trova compare «mapping mancante» e la carta non si può pubblicare.
- **Prezzo consigliato**: l'offerta più bassa attualmente su CardTrader (in euro), aggiornata ogni 10 minuti.
- **Doppie**: si possono vendere solo le copie oltre la prima. **Una copia resta sempre in collezione**; il server rifiuta richieste che la includerebbero.
- **Pubblica**: scegli quantità e prezzo e conferma. L'app crea l'annuncio su CardTrader con lingua, condizione e finitura mappate sulle proprietà del prodotto. La quantità in collezione **non viene scalata** da sola: aggiustala tu quando la vendita è conclusa.

> La pubblicazione crea **annunci reali** sul tuo account CardTrader. Se CardTrader rifiuta la richiesta, l'app mostra il messaggio d'errore ricevuto.

### «Sealed» (CardTrader)

Una raccolta separata dalle carte per i **prodotti sigillati**: booster, booster box, Elite Trainer Box e bundle, blister, tin, box set, mazzi precostruiti, case e display. Il catalogo e i prezzi arrivano da CardTrader (serve il token).

- **Aggiungere un prodotto**: *Aggiungi prodotto* → scrivi almeno 2 lettere del nome o il codice del set (es. `Chaos Rising`, `cri`) → scegli il prodotto, la **lingua** e la quantità → *Aggiungi*. Lo stesso prodotto nella stessa lingua si somma. *Mostra anche accessori* include anche sleeves, playmat, album, dadi e simili.
- **Prezzi per lingua**: per ogni prodotto e lingua si salvano l'**offerta più bassa** e la **mediana** (solo euro). Se in una lingua ci sono offerte marcate `sealed`, si usano solo quelle; se il flag è falso su tutte (succede su alcuni prodotti) si usano tutte. I venditori in vacanza contano solo se non ci sono altre offerte. Il valore totale usa l'offerta più bassa.
- **Aggiornamento**: una volta al giorno in automatico, oppure con *Aggiorna prezzi*. Se un prezzo non si scarica, sotto il prodotto compare il motivo (errore di CardTrader, nessuna offerta nella lingua scelta…).
- **Dettaglio e grafico**: toccando un prodotto si apre la scheda con il valore e il grafico dello storico (offerta più bassa e mediana). CardTrader non fornisce uno storico: la linea si costruisce con una rilevazione al giorno a partire da quando aggiungi il prodotto, quindi servono almeno due giorni.
- **Vendere**: *Vendi* sulla scheda → quantità e prezzo (precompilato con il minimo) → *Pubblica su CardTrader* (con conferma). A differenza delle carte si possono mettere in vendita anche tutte le copie, e la quantità non viene scalata in automatico.
- **Immagini**: scaricate da CardTrader e salvate in `pokedata/sealed_img/`.
- **Limite delle richieste**: l'elenco dei prodotti in vendita di CardTrader è limitato a una chiamata al secondo; l'app aspetta da sola, quindi la prima aggiunta di un set può richiedere qualche secondo.

### Prezzi

Tre fonti, usate per scopi diversi:

| Fonte | Valuta | Uso nell'app |
|---|---|---|
| **JustTCG** (prezzi in stile TCGplayer, per condizione e finitura) | USD | Prezzo mostrato sulle tessere, valore della collezione, grafico multi-linea, scheda «Prezzo». Richiede una **chiave API gratuita** (facoltativa). |
| **TCGdex / Cardmarket** | EUR | Rarità, scheda «Prezzo» e storico di riserva. Non richiede chiave. |
| **CardTrader** | EUR | Prezzo consigliato in «Vendi» e prezzi dei prodotti in «Sealed». Richiede un **token** (facoltativo). |

Senza chiavi l'app funziona lo stesso: riconosce e cataloga le carte, ma senza prezzi in dollari, grafici per condizione, vendita e sealed.

**Collegamento a JustTCG.** Al primo salvataggio di una carta l'app la cerca su JustTCG usando il **nome inglese**, tiene i risultati con lo **stesso numero** e sceglie il set per **codice** (es. `me04`) o per somiglianza del nome; se resta una sola candidata la accetta. Il collegamento si salva una volta sola. Le carte in altre lingue usano l'equivalente inglese. I tentativi falliti vengono ripetuti dopo 3 giorni e a ogni riavvio.

**Scelta del prezzo.** Per ogni copia si usa la variante JustTCG che corrisponde alla finitura scelta (Standard, Holo, Reverse Holo; le 1st Edition si ignorano). Le condizioni sono mappate su Near Mint, Lightly Played, Moderately Played, Heavily Played, Damaged. Per le condizioni senza quotazione su JustTCG (frequente per MP, HP e DMG sulle carte economiche) compare «—» e non si applicano percentuali di stima.

**Storico e limiti.** Al primo collegamento si richiede lo storico disponibile (fino a 90 giorni, se il piano lo consente); poi ogni giorno si aggiunge un punto, aggiornando le carte a **gruppi di 20 per richiesta**. Il piano gratuito ha limiti giornalieri, mensili e al minuto: l'app distanzia le richieste (una ogni ~6,5 secondi) e, dopo un errore *429*, attende 40 secondi e riprova una volta. Controlla i limiti aggiornati sul sito di JustTCG. Se hai molte carte nuove, i prezzi possono arrivare in più giorni.

### Aggiornamenti automatici e backup

Un processo in background controlla ogni ora:

- **Backup**: una copia coerente del database al giorno in `pokedata/backup/`, conservando le ultime 14.
- **Prezzi delle carte**: una volta al giorno (se la collezione non è vuota) aggiorna rarità e prezzi Cardmarket e poi i prezzi JustTCG.
- **Prezzi sealed**: una volta al giorno, se hai prodotti nella raccolta e il token CardTrader è impostato.
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

### 2. Riconoscimento a cascata (`Matcher.match`)

Per essere veloce, il confronto procede per gradi e si ferma appena il risultato è netto:

1. **CLIP** (modello `clip-ViT-B-32`) trasforma la carta in un vettore e lo confronta con quelli di tutte le carte indicizzate (filtrando per lingua/set se richiesto). La carta **ruotata di 180°** viene provata solo se la somiglianza migliore è bassa (sotto `POKESCAN_SOGLIA_ROT`, 0,78 di default) o se SIFT non conferma nulla.
2. Per i candidati più simili si confrontano i **punti caratteristici SIFT** con quelli dell'immagine ufficiale e si contano quelli coerenti dopo **RANSAC** (omografia). Questo distingue ristampe e carte quasi uguali. I candidati verificati sono **3**; se il risultato non è netto diventano **10** e infine **40**.
3. Se i punti coerenti sono sufficienti (almeno 10) si ordina per punti, altrimenti solo per similarità CLIP (foto troppo scarsa). Le candidate non verificate con SIFT restano come alternative.

### 3. Fusione dei fotogrammi e affidabilità (`fondi`, `stato_di`)

Per ogni scansione si catturano **fino a 3 fotogrammi** a 1280 px, a ~250 ms l'uno dall'altro; se già il primo dà un risultato nettissimo (almeno 25 punti SIFT e almeno il doppio del secondo) gli altri non vengono elaborati. I risultati vengono mediati. Il risultato è **«sicuro»** se:

- il primo candidato ha almeno 15 punti SIFT coerenti **e** almeno 1,5 volte quelli del secondo; oppure
- (foto povera, meno di 10 punti) la similarità CLIP è almeno 0,80 con un margine di almeno 0,02 sul secondo;

e, se i fotogrammi sono più di uno, la maggioranza concorda sul primo posto. Altrimenti è **«da verificare»**. Le soglie sono costanti in `pokescan.py` (`SOGLIA_SCORE`, `SOGLIA_MARGINE`, `SOGLIA_ROT`, `CANDIDATI`, `FASI_SIFT`) e in `stato_di`.

---

## Requisiti

- **Server**: qualsiasi macchina Linux/Windows/macOS con **Docker** (consigliato) oppure Python 3.10+ (consigliata la 3.11, quella dell'immagine Docker). Il riconoscimento usa PyTorch su CPU: conta indicativamente **1–2 GB di RAM** per il modello e gli indici; più processori rendono più veloce il riconoscimento. Funziona anche su un NAS con Docker.
- **Spazio**: l'indice di una lingua (immagini ufficiali, punti SIFT, vettori) occupa dell'ordine di **1 GB**; i tempi della prima indicizzazione vanno da decine di minuti a qualche ora, secondo connessione e CPU.
- **Client**: un browser moderno. Per la fotocamera **live** serve un contesto sicuro (**HTTPS** o `localhost`); senza HTTPS usa «Da galleria».
- **Internet** sul server per scaricare dati e immagini (TCGdex) e, se li vuoi, per i prezzi (JustTCG) e per vendita e sealed (CardTrader).
- **Facoltativo**: chiave API gratuita di JustTCG; token API di CardTrader.

---

## Installazione

### Cosa ti serve

- **Docker** con il comando `docker compose`: Docker Desktop su Windows e macOS, Docker Engine con il plugin Compose su Linux, oppure il Container Manager di un NAS. Controlla con `docker --version` e `docker compose version`. Guida ufficiale: <https://docs.docker.com/get-docker/>
- **Il progetto**: dal pulsante verde «Code» di questa pagina scegli «Download ZIP» ed estrailo, oppure usa `git clone <indirizzo di questo repository> pokescan`.
- Un **terminale aperto nella cartella del progetto** (quella che contiene `docker-compose.yml`).
- Un processore **x86-64 o ARM64**, una connessione a Internet e spazio su disco: alcuni GB (circa 3) per l'immagine Docker più circa 1 GB per ogni lingua che indicizzi.

### Guida rapida (da zero)

I passi vanno fatti **in quest'ordine**: l'app non parte finché non esiste almeno un indice delle carte.

**1. Costruisci l'immagine** (5–15 minuti, scarica PyTorch e le librerie):

```bash
docker compose build
```

**2. Costruisci l'indice della lingua delle tue carte** (una volta sola; da decine di minuti a qualche ora, secondo connessione e processore):

```bash
docker compose run --rm pokescan python pokescan.py index --lang it
```

Usa il codice della lingua delle *tue* carte (`it`, `en`, `fr`, `de`, `es`, `pt`, `ja`, `ko`, `zh-tw`, `zh-cn`, …). Se hai carte in più lingue ripeti il comando per ciascuna. Se si interrompe, rilancialo: le immagini già scaricate non vengono riscaricate.

**3. Avvia l'app:**

```bash
docker compose up -d
```

**4. Controlla che sia partita:**

```bash
docker compose logs -f
```

Devi vedere `Indice caricato: it` (o la tua lingua) e `Listening at: http://0.0.0.0:8085`. Al primo avvio l'app scarica anche il modello di riconoscimento (alcune centinaia di MB), quindi può servire qualche minuto. Esci dai log con `Ctrl+C`: l'app resta attiva.

**5. Apri l'app** nel browser: `http://localhost:8085` se sei sullo stesso computer, altrimenti `http://IP-DEL-SERVER:8085`. Dal telefono la fotocamera live richiede HTTPS (vedi [HTTPS](#5-https-per-la-fotocamera-live-da-telefono)); nel frattempo «Da galleria» funziona anche senza.

**6. Imposta la password** (fortemente consigliato):

```bash
docker compose exec pokescan python app.py --setpw
```

**7. Facoltativo**: la chiave JustTCG (prezzi in dollari) e il token CardTrader (vendita e sealed). Come si ottengono, come si salvano e come si controlla che funzionino: [Prima configurazione, punti 3 e 4](#3-chiave-justtcg-facoltativa-per-i-prezzi-in-dollari). Senza, l'app funziona lo stesso ma senza quei prezzi.

Per fermare l'app: `docker compose down` (i dati restano in `pokedata/`). Per riavviarla: `docker compose up -d`.

### Senza Docker

Crea l'ambiente e installa le dipendenze (da fare nella cartella del progetto):

```bash
python -m venv .venv
source .venv/bin/activate            # su Windows: .venv\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python pokescan.py index --lang it   # indice: obbligatorio prima di avviare l'app
```

Poi avvia il server, che deve usare **un solo processo** (il modello e gli indici stanno in memoria e il rilevamento dello sfondo è condiviso):

```bash
# Linux e macOS
gunicorn -b 0.0.0.0:8085 -w 1 --threads 2 --timeout 180 app:app

# Windows (gunicorn non funziona su Windows: usa waitress)
pip install waitress
waitress-serve --listen=0.0.0.0:8085 --threads=2 app:app
```

Su Windows puoi in alternativa usare Docker Desktop (percorso consigliato) o WSL2. La password e le chiavi si impostano con gli stessi comandi della guida, senza `docker compose exec pokescan`: per esempio `python app.py --setpw`.

### Su un NAS (esempio: Synology)

- Metti il progetto in una cartella condivisa (ad esempio dentro la cartella `docker`) e lancia gli stessi comandi `docker compose` da SSH.
- Se non riesci a sovrascrivere i file con `scp` perché la cartella ha permessi in sola lettura o ACL, carica lo zip con File Station ed estrailo con un container, che scavalca i permessi:

  ```bash
  docker run --rm -v "$PWD":/w python:3.11-slim python -c "import zipfile; zipfile.ZipFile('/w/NOME-DELLO-ZIP.zip').extractall('/w')"
  ```

---

## Prima configurazione

### 1. Costruire l'indice delle carte (obbligatorio, una tantum per lingua)

Se hai seguito la [guida rapida](#guida-rapida-da-zero) l'hai già fatto per la tua lingua. Qui i dettagli e come aggiungerne altre:

```bash
# con Docker
docker compose run --rm pokescan python pokescan.py index --lang en
docker compose run --rm pokescan python pokescan.py index --lang it
# senza Docker
python pokescan.py index --lang it
```

Scarica l'elenco dei set, le immagini ufficiali e calcola i vettori. Puoi indicizzare più lingue (`en`, `it`, `fr`, `de`, `es`, `pt`, `ja`, `ko`, `zh-tw`, `zh-cn`, …): lo scan le usa tutte insieme. Se viene interrotto, le immagini già scaricate non vengono riscaricate. Se l'app è già avviata, riavviala per caricare il nuovo indice (`docker compose restart`).

Indicizza **la lingua delle tue carte**: una carta italiana viene riconosciuta molto meglio confrontandola con la sua versione italiana (testo e cornice uguali). Basta anche una sola lingua.

### 2. Impostare la password (fortemente consigliato)

```bash
docker compose exec pokescan python app.py --setpw
```

Ti chiede nome utente e password (almeno 8 caratteri). Il login si attiva subito.

### 3. Chiave JustTCG (facoltativa, per i prezzi in dollari)

JustTCG è un servizio di prezzi con un **piano gratuito**, sufficiente per una collezione personale (i limiti cambiano nel tempo: controllali sul sito).

1. Registrati su <https://justtcg.com> e copia la chiave API dalla tua **Dashboard** (documentazione: <https://justtcg.com/docs>).
2. Salvala nell'app, **senza scriverla in file o nella cronologia del terminale**:

   ```bash
   docker compose exec pokescan python app.py --setkey
   ```

   La chiave viene chiesta in modo nascosto e salvata in `pokedata/justtcg.key`. Non serve riavviare. In alternativa si può usare la variabile d'ambiente `JUSTTCG_API_KEY` (vedi [la nota sulle variabili](#nota-variabili-dambiente-e-docker-composeyml)).
3. Salva almeno qualche carta: i prezzi si scaricano per le carte della collezione. Poi, in Collezione, tocca «Aggiorna prezzi» **una sola volta** e attendi qualche minuto (le richieste sono distanziate per rispettare i limiti del piano gratuito). La voce «Prezzo» mostra invece i prezzi di una carta senza salvarla.
4. **Verifica**: se dopo qualche minuto non compare nessun prezzo, guarda gli eventi dell'integrazione:

   ```bash
   docker compose logs --tail=100 | grep justtcg
   ```

   `risposta 401` o `403` = chiave errata o non attiva; `risposta 429` = limite del piano raggiunto (l'app aspetta e riprova, i prezzi arrivano in più giorni); «carta non trovata» = quella carta non è stata collegata a JustTCG. Le stesse informazioni sono nella pagina `/api/jt-log`.

### 4. Token CardTrader (facoltativo, per «Vendi» e «Sealed»)

Serve un account CardTrader. Il token API si ottiene nella **pagina delle impostazioni del tuo profilo** su CardTrader, come spiega la [documentazione ufficiale](https://www.cardtrader.com/docs/api/full/reference).

1. Salvalo nell'app allo stesso modo:

   ```bash
   docker compose exec pokescan python app.py --set-cardtrader-key
   ```

   Il token viene salvato in `pokedata/cardtrader.key` (oppure usa la variabile d'ambiente `CARDTRADER_API_TOKEN`). Non serve riavviare.
2. **Verifica**: nella voce «Sealed» scompare l'avviso «Token CardTrader non configurato»; in «Vendi» compaiono i prezzi consigliati. Per provare il token direttamente (stampa `200` se è valido, `401` se non lo è):

   ```bash
   docker compose exec pokescan python -c "import requests; t=open('pokedata/cardtrader.key').read().strip(); print(requests.get('https://api.cardtrader.com/api/v2/info', headers={'Authorization': 'Bearer ' + t}).status_code)"
   ```

> Il token consente di **pubblicare annunci a tuo nome**: trattalo come una password. Se lo esponi per errore, sostituiscilo dal sito di CardTrader e salva quello nuovo.

#### Nota: variabili d'ambiente e `docker-compose.yml`

Il modo consigliato è `--setkey` / `--set-cardtrader-key`: le chiavi finiscono in `pokedata/`, che non viene mai pubblicata. Se preferisci le variabili d'ambiente, **non scrivere le chiavi dentro `docker-compose.yml`** (fa parte del progetto e finirebbe su GitHub): crea un file `.env` accanto a `docker-compose.yml` (è già escluso da git e da Docker) con

```
JUSTTCG_API_KEY=la-tua-chiave
CARDTRADER_API_TOKEN=il-tuo-token
```

e togli il commento alle righe `environment` del compose, poi `docker compose up -d`. Se esiste anche il file in `pokedata/`, ha la precedenza.

### 5. HTTPS (per la fotocamera live da telefono)

I browser mobili consentono la fotocamera live solo in HTTPS. Metti l'app dietro un reverse proxy con certificato (Caddy, nginx, Traefik o uno già presente sul tuo server). Esempio con Caddy:

```
pokescan.example.com {
    reverse_proxy localhost:8085
}
```

Se esponi l'app fuori dalla rete di casa, **attiva il login** e non pubblicarla direttamente su Internet senza proxy e HTTPS.

---

## Aggiornare a una nuova versione

I tuoi dati stanno in `pokedata/`, fuori dal codice: aggiornare non li tocca (il database si aggiorna da solo alla prima partenza, creando le tabelle nuove).

```bash
git pull                                # oppure sostituisci i file del progetto con quelli nuovi
docker compose build --no-cache
docker compose up -d --force-recreate
```

Poi ricarica la pagina con **ricarica forzata** (Ctrl+F5) o chiudi e riapri la web app sul telefono: senza, il browser può mostrare la vecchia interfaccia dalla cache. La versione in uso compare nella barra informazioni di «Collezione».

---

## Uso pratico e consigli di scansione

- **Luce**: preferisci luce **morbida e laterale** (una lampada a 45°) al flash diretto, che crea riflessi che nessun software recupera del tutto. Se usi il flash, inclina leggermente la fotocamera.
- **Piano**: opaco e uniforme. Con carte dal bordo grigio su piani chiari, usa «Sfondo vuoto».
- **Stabilità**: telefono su un supporto fisso; dopo aver memorizzato lo sfondo non muoverlo né cambiare zoom.
- **Lanciatore di carte**: attiva «Scansione automatica» e «Salvataggio automatico», scegli la condizione predefinita e lascia la fotocamera ferma. Le carte dubbie si fermano sulla scheda di conferma.
- **Carte rovinate**: il confronto si basa sull'illustrazione, quindi pieghe e usura pesano poco; se il risultato è «da verificare» controlla le alternative.
- **Copie identiche consecutive**: usa «Scansiona ora» per la seconda.
- **Controllare un prezzo al volo**: usa la voce «Prezzo», così non sporchi la collezione.

---

## Dove sono i dati: la cartella `pokedata`

Tutto ciò che è tuo sta qui. **Non va mai pubblicata nel repository** (è già nel `.gitignore`).

| File / cartella | Contenuto |
|---|---|
| `collezione.db` (+ `-wal`, `-shm`) | Database SQLite: collezione, storico prezzi, collegamenti JustTCG, raccolta sealed e relativi prezzi, registro delle correzioni, info sui set. Usa la modalità WAL: se lo copi a mano, copia anche i file `-wal` e `-shm` (oppure usa i backup). |
| `backup/` | Una copia coerente al giorno, ultime 14. |
| `img/` | Immagini ufficiali scaricate (cache locale servita dall'app). |
| `sealed_img/` | Immagini dei prodotti sealed (si rigenerano da sole se le cancelli). |
| `emb*.npy`, `meta*.json` | Indici dei vettori CLIP e metadati delle carte, uno per lingua (`emb.npy` è l'inglese). |
| `noimg_*.json` | Elenco delle carte che TCGdex ha senza immagine. |
| `sift/` | Cache dei punti SIFT delle carte di riferimento. |
| `hf/` | Cache del modello CLIP (con Docker). |
| `auth.json` | Nome utente e **hash** della password. |
| `secret.key` | Chiave per firmare le sessioni (generata automaticamente). |
| `justtcg.key` | Chiave API JustTCG, se impostata. |
| `cardtrader.key` | Token API CardTrader, se impostato. |
| `cardtrader_blueprints.json`, `cardtrader_blueprint_info.json` | Collegamenti tra le tue carte e i prodotti CardTrader, e proprietà modificabili dei prodotti. |
| `ultimo_agg.txt`, `ultimo_indice.txt` | Date dell'ultimo aggiornamento di prezzi ed elenco carte. |

Per un backup completo copia l'intera cartella `pokedata/` a server fermo (o i soli file di `backup/` più gli indici, che si possono anche ricostruire).

---

## Riferimento delle API HTTP

Con il login attivo tutte le rotte (tranne `/login` e `/logout`) richiedono la sessione; le chiamate `/api/*` rispondono sempre in JSON, anche in caso di errore (`{"errore": "..."}`).

### Interfaccia e sistema

| Metodo e percorso | Descrizione |
|---|---|
| `GET /` | Pagina dell'app. |
| `GET/POST /login`, `GET /logout` | Accesso e uscita. |
| `GET /img/<lang>/<id>` | Immagine ufficiale della carta dalla cache locale. |
| `GET /setimg/<lang>/<set>` | Logo del set dalla cache locale. |
| `GET /api/filtri` | Lingue e set disponibili per i filtri. |
| `GET /api/stato` | Date di aggiornamento, numero di carte indicizzate, ultimo backup, versione, statistiche di riconoscimento. |
| `POST /api/aggiorna` | Avvia l'aggiornamento dei prezzi. |
| `POST /api/aggiorna-carte` | Avvia la ricerca di carte nuove. |
| `POST /api/backup` | Crea subito un backup. |
| `GET /api/correzioni` | Statistiche e errori di riconoscimento più frequenti. |
| `GET /api/jt-log` | Ultimi eventi dell'integrazione JustTCG e tempi di riconoscimento/salvataggio (diagnostica; non contiene la chiave). |
| `GET /api/jt-verifica`, `GET /api/jt-cerca` | Diagnostica: come JustTCG chiama un gruppo di carte o una singola carta. |

### Riconoscimento

| Metodo e percorso | Descrizione |
|---|---|
| `POST /api/rileva` | Riceve un fotogramma (`foto`) e restituisce se c'è una carta, i quattro angoli normalizzati e la miniatura. |
| `POST /api/scan` | Riceve fino a 3 fotogrammi (`foto`, più `lang`/`set` opzionali) e restituisce candidati, stato («ok»/«verifica») e punti. |
| `POST /api/sfondo`, `DELETE /api/sfondo` | Memorizza / rimuove l'immagine dello sfondo vuoto. |
| `GET /api/cerca?q=&lang=&set=` | Ricerca per nome tra le carte indicizzate (max 30 risultati). |
| `POST /api/impara` | Usa la foto come immagine di riferimento di una carta senza immagine. |
| `GET /api/prezzo?card_id=&lang=` | Prezzi di una carta senza salvarla (JustTCG per finitura e condizione, Cardmarket). |

### Collezione

| Metodo e percorso | Descrizione |
|---|---|
| `POST /api/salva` | Salva una carta (con `condiz` e `fin`); risponde subito, il resto avviene in background. |
| `GET /api/collezione` | Righe della collezione con prezzo USD, totale e conteggio senza prezzo. |
| `POST /api/qta/<riga>` | Aggiunge o toglie copie (`{"d": 1}` o `{"d": -1}`); a zero la riga sparisce. |
| `POST /api/condizione/<riga>`, `POST /api/finitura/<riga>` | Sposta una copia in un'altra condizione (`{"c": "LP"}`) o finitura (`{"f": "H"}`). |
| `DELETE /api/carta/<riga>`, `POST /api/elimina` | Elimina una riga, o più righe insieme. |
| `GET /api/tcg/<id>` | Serie di prezzi JustTCG per condizione/finitura possedute e stato del collegamento. |
| `GET /api/storico/<id>` | Storico Cardmarket di riserva. |
| `GET /api/set` | Set posseduti con completamento. |
| `GET /api/mancanti` | Carte mancanti nei set già iniziati. |
| `GET /export.csv` | Esporta la collezione. |

### Vendita su CardTrader

| Metodo e percorso | Descrizione |
|---|---|
| `GET /api/vendi` | Copie raggruppate per carta/lingua/condizione/finitura, con mapping CardTrader e prezzo consigliato. |
| `POST /api/vendi/pubblica` | Pubblica un annuncio (`blueprint_id`, `quantity`, `price`, …). Mantiene sempre una copia in collezione. |

### Sealed

| Metodo e percorso | Descrizione |
|---|---|
| `GET /api/sealed/set?q=` | Cerca espansioni Pokémon su CardTrader per nome o codice. |
| `GET /api/sealed/prodotti?exp=&tutti=` | Prodotti sealed di un'espansione (con `tutti=1` anche gli accessori). |
| `POST /api/sealed/aggiungi` | Aggiunge un prodotto alla raccolta (`blueprint_id`, `exp_id`, `lang`, `qta`). |
| `GET /api/sealed` | Raccolta con prezzi (minimo e mediana), valore totale e stato dell'aggiornamento. |
| `POST /api/sealed/qta/<id>`, `DELETE /api/sealed/<id>` | Cambia la quantità (`{"d": 1}`) o elimina un prodotto. |
| `POST /api/sealed/aggiorna-prezzi` | Avvia l'aggiornamento dei prezzi sealed. |
| `GET /api/sealed/storico/<blueprint>/<lang>` | Storico giornaliero di minimo e mediana. |
| `GET /api/sealed/img/<blueprint>` | Immagine del prodotto (dalla cache locale). |
| `POST /api/sealed/pubblica` | Pubblica un annuncio per un prodotto sealed (`id`, `quantity`, `price`). |

---

## Riferimento del codice

### `pokescan.py` — motore di riconoscimento

| Funzione / classe | Ruolo |
|---|---|
| `file_indice(lang)`, `percorso(m)` | Nomi dei file di indice per lingua e percorso dell'immagine di una carta. |
| `get_json(url, …)` | GET JSON con tentativi ripetuti e attesa crescente. |
| `build_index(lang)` | Scarica set e immagini di una lingua, calcola i vettori CLIP e salva l'indice. |
| `aggiorna_indice(matcher, lang, lock)` | Aggiunge all'indice solo le carte nuove. |
| `Matcher` | Carica gli indici (`carica`), calcola i vettori e confronta (`match`, a cascata). |
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
| `norm`, `jt_collega`, `fin_di` | Normalizza testi; collega una carta a JustTCG (nome, numero, codice o nome del set); finitura di una variante. |
| `jt_salva`, `jt_card`, `jt_tutte` | Salva prezzi e storico per ogni condizione/finitura posseduta; aggiorna una carta; aggiornamento giornaliero a gruppi di 20. |
| `aggiorna`, `backup`, `_bk`, `ciclo` | Aggiornamento prezzi, backup coerente, ciclo orario in background. |
| `aggiorna_carte`, `ciclo_carte` | Ricerca periodica di carte nuove e ricarica degli indici. |
| `meta_set` | Nome, logo e totale delle carte di un set, salvati una volta. |
| `aggiorna_noimg`, `impara` | Elenco delle carte senza immagine; uso della foto come immagine di riferimento. |
| `imgs_in`, `img_in`, `fondi`, `stato_di`, `cand` | Lettura delle immagini, fusione dei fotogrammi, giudizio di affidabilità, formato dei candidati. |
| `dopo_salvataggio` | Completa in background il salvataggio (rarità, prezzo, storico). |
| `mancanti_list`, `prezzo` | Carte mancanti dei set iniziati; prezzo di una carta senza salvarla. |
| `cardtrader_key`, `cardtrader_get`, `cardtrader_post` | Token e richieste a CardTrader. |
| `cardtrader_resolve`, `cardtrader_resolve_all` | Collegano le carte ai prodotti CardTrader (nome, numero, set) e salvano il mapping. |
| `cardtrader_recommended`, `cardtrader_properties` | Prezzo consigliato (offerta più bassa in euro); proprietà dell'annuncio (lingua, condizione, finitura). |
| `vendi`, `pubblica_vendita` | Elenco delle copie vendibili; pubblicazione dell'annuncio. |
| `ct_lento`, `_seal_espansioni`, `_seal_categorie`, `_seal_bps` | Richieste a CardTrader per i sealed (almeno 1,1 s tra l'una e l'altra) e relative cache. |
| `_seal_stats`, `sealed_prezzi_bp`, `sealed_aggiorna_prezzi`, `ciclo_sealed` | Minimo e mediana per lingua; aggiornamento dei prezzi sealed, anche una volta al giorno in background. |
| `sealed_*` (rotte) | Ricerca set e prodotti, raccolta, quantità, storico, immagini, pubblicazione. |
| `errore_json` | Risponde sempre in JSON alle chiamate `/api`. |

### `static/index.html` — interfaccia

| Funzione | Ruolo |
|---|---|
| `go`, `toast`, `stato` | Navigazione tra le voci del menu, messaggi, testo di stato. |
| `cam`, `fermaCam`, `iniZoom`, `applicaZoom`, `iniFlash` | Avvio e arresto della fotocamera, zoom ottico/digitale, torcia. |
| `frame`, `tre`, `disegna` | Cattura dei fotogrammi (uno o tre) e disegno del riquadro verde. |
| `loop`, `corr`, `riparti` | Ciclo di rilevamento, confronto delle miniature, ripartenza dopo il salvataggio. |
| `scansiona`, `renderConf`, `renderPrz`, `altri`, `cerca`, `conferma`, `salvaAuto`, `chiudi` | Riconoscimento, scheda di conferma, scheda prezzi, alternative, ricerca per nome, salvataggio manuale e automatico. |
| `caricaColl`, `grid`, `dettaglio`, `grafico`, `graficoTcg` | Collezione raggruppata, filtri, dettaglio per condizione/finitura, grafici (USD; euro di riserva). |
| `caricaSet`, `renderSet`, `selBar`, `initFiltri`, `fillSets`, `stInfo` | Voce Set (con selezione multipla), filtri lingua/pacchetto, barra informazioni. |
| `caricaMancanti`, `renderMancanti` | Voce Mancanti. |
| `caricaVendi`, `renderVendi` | Voce Vendi e pubblicazione su CardTrader. |
| `caricaSealed`, `renderSealed`, `dettaglioSealed`, `cercaSet`, `caricaProdotti`, `renderProdotti` | Voce Sealed: raccolta, dettaglio con grafico, ricerca del set e aggiunta di prodotti. |
| `grSet`, `disegnaGr` | Grafici a linee condivisi da carte e sealed. |

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
| Il container si riavvia di continuo, nei log «Indice mancante» | L'indice non esiste ancora: ferma l'app (`docker compose down`), esegui il passo 2 della [guida rapida](#guida-rapida-da-zero) e riavvia con `docker compose up -d`. |
| `docker compose exec …` dice che il container non è in esecuzione | L'app non è partita: guarda `docker compose logs` (di solito manca l'indice). |
| La pagina non si apre | Controlla che il container sia attivo (`docker compose ps`), la porta 8085 e il firewall del server. |
| Primo avvio molto lento | Normale: scarica e carica il modello CLIP. L'avviso su `HF_TOKEN` è innocuo. |
| Dopo un aggiornamento non vedo le novità | Ricarica forzata (Ctrl+F5) o riapri la web app; se serve, controlla che i file nuovi siano stati davvero copiati e che l'immagine sia stata ricostruita con `docker compose build --no-cache`. |
| Fotocamera non parte | Serve HTTPS (o `localhost`) e il permesso del browser; in alternativa usa «Da galleria». |
| «Il server ha risposto in modo non valido (codice N)» | Apri `/api/jt-log`: gli errori del server sono annotati lì. |
| La carta non viene rilevata | Più contrasto con lo sfondo, luce morbida, «Sfondo vuoto». Come ultima risorsa «Scansiona ora». |
| Riconoscimento sbagliato | Indicizza la lingua giusta; restringi per lingua/set; controlla riflessi e messa a fuoco; guarda le alternative in «Correggi». |
| Nessun prezzo in dollari | Chiave JustTCG impostata (punto 3)? Guarda `docker compose logs --tail=100 \| grep justtcg` o `/api/jt-log`: `401`/`403` chiave errata, `429` limite raggiunto, carta non trovata, oppure condizione senza quotazione (MP/HP/DMG). |
| «Token CardTrader non configurato» o errore 401 da CardTrader | Salva il token (punto 4) e provalo con il comando di verifica: deve stampare `200`. |
| «mapping mancante» in Vendi | L'app non ha trovato il prodotto CardTrader corrispondente: controlla il token e riapri la voce Vendi (il collegamento si ritenta). |
| «Prezzo non disponibile» in Sealed | Il motivo è scritto sotto il prodotto. Per i dettagli: `docker compose logs --tail=200 \| grep sealed`. |
| Annuncio rifiutato da CardTrader | L'app mostra il messaggio ricevuto: controlla prezzo, quantità e che il prodotto esista nella lingua scelta. |
| Salvataggio lento | Disco lento o molte scritture: il database usa WAL e il resto avviene in background; confronta i tempi in `/api/jt-log`. |
| Poca memoria | Un solo worker, evita altri servizi pesanti; riduci le lingue indicizzate. |

---

## Sicurezza e privacy

- **Nessun segreto nel codice.** Chiave JustTCG, token CardTrader, hash della password e chiave di sessione vivono solo in `pokedata/`. Non committare mai `pokedata/`, `.env`, `*.key`, `auth.json`, `secret.key`.
- **Non mettere chiavi in `docker-compose.yml`** né in altri file del progetto: usa `--setkey` / `--set-cardtrader-key` oppure un file `.env` (già ignorato da git).
- **Il token CardTrader permette di pubblicare annunci a tuo nome**: non condividerlo e revocalo dal sito se lo esponi per errore. Ogni pubblicazione chiede una conferma esplicita nell'interfaccia.
- **Attiva il login** e non esporre l'app direttamente su Internet: usa un reverse proxy con HTTPS.
- Le foto inviate per il riconoscimento sono elaborate in memoria e **non vengono salvate** (salvo la foto che scegli di usare come immagine di riferimento); lo sfondo vuoto resta solo in memoria fino al riavvio.
- L'app contatta solo TCGdex (dati, immagini) e, se configurati, JustTCG (prezzi) e CardTrader (vendita e sealed); il modello CLIP viene scaricato una volta da Hugging Face.
- Se pubblichi un fork, controlla con `git status` che `pokedata/` non sia tracciata.

## Crediti e note legali

- Dati e immagini delle carte: **TCGdex**, scaricati a runtime sul tuo server. Questo repository **non contiene** immagini né dati di carte.
- Prezzi in dollari: **JustTCG**, con la tua chiave personale e nel rispetto dei suoi termini di servizio e dei limiti del piano.
- Catalogo, prezzi e annunci per vendita e sealed: **CardTrader**, con il tuo token personale e nel rispetto dei suoi termini di servizio.
- Modello di riconoscimento: **CLIP ViT-B/32** (OpenAI) tramite *sentence-transformers*; visione artificiale con **OpenCV**; web con **Flask**.
- *Pokémon* e i nomi, le immagini e i marchi delle carte appartengono ai rispettivi titolari (Nintendo, Creatures, Game Freak, The Pokémon Company). Questo progetto è indipendente e **non affiliato**.
- I prezzi sono **indicativi**, non una stima ufficiale né una consulenza.
- Rispetta i termini d'uso di ciascun servizio e le norme locali sui dati.
