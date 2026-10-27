# Fixtures esperimento 49

Dati di riferimento per il test di regressione "core == legacy" (US-1).

## 1. Provenienza dei file originali

- Fonte: Google Drive, cartella R&D Physics 2D/2d/2d
- Codice legacy di riferimento: commit 16f5f87 di ScyPyna/moving-chlamydomonas_pub
- Data di scaricamento: [placeholder]
- Scaricati da: [placeholder]

## 2. File presenti e a cosa servono

| File | Origine | Uso |
|---|---|---|
| `tAlgae49.txt` | Output del tracking legacy sul video 49 (Drive) | Input dell'analisi, riferimento del tracking |
| `illumination14.tiff` | Immagine di illuminazione 14 (Drive) | Input dell'analisi, grafico densità |
| `talgae_settings.txt` | File settings completo del laboratorio (Drive); riga 49: `49 1 14 180 1.041667 1 0 0 0 0` | Impostazioni esperimento: tipo 1, illuminazione 14, 180 µW, pixel 1.041667 |
| `tumb_exp49_tthres5.0.txt` | Output dell'operatrice (Drive) | Riferimento per verificare i parametri di tumbling |

## 3. Parametri usati per generare il riferimento (`backend/scripts/make_reference.py`)

Valori ricostruiti riaprendo l'interfaccia Streamlit legacy (`app.py`) e richiamando alla memoria la demo live col laboratorio. Verificati empiricamente: vedi sezione 4.

**AnalysisParams**
- `diam` = 10
- `dt` = 0.100
- `particle_show` = 5
- `disc_radius` = 350
- `flux_cg_in` = 1
- `flux_cg_out` = 150
- `tumbling_threshold` = 5.0
- `radial_map` = False (modalità distanza dal centro: per il 49 manca il file della mappa radiale)
- `nskip` = 1

**Parametri plot Theta P(θ)** (solo con `--plots`)
- `inner_circle` = 350 (= `disc_radius`)
- `thickness_circle` = 0.0
- `max_distance` = 800

**FilterParams** — filtri sostanzialmente disattivati, tutti a 0 tranne `dist_step`
- `lifetime_min` = 0
- `threshold_dist` = 0
- `threshold_dist_tot` = 0
- `dist_step` = 1
- `strict` = True
- `only_inside` = True
- `blinking_ratio` = 0
- `blinking_tolerance` = 0
- `long_track_min_snaps` = 0

**Nota sui filtri**: il documento di pianificazione riportava `threshold_dist` = 1, `threshold_dist_tot` = 3 e `blinking_ratio` = 0.5 (sono anche i default di `clam_pipeline.cli.main()` quando `fparams` non viene passato). Qui sono a 0 perché con questi valori il tumbling generato coincide esattamente con il file dell'operatrice (sezione 4): è un indizio forte che il laboratorio abbia lavorato con i filtri disattivati. Resta comunque da confermare via mail (sezione 5).

**Perché solo disc350**: `cli.py` mette `disc_radius` nel nome dei file di N(t) e del flusso (`N_dist_*`, `N_dist_compare_*`, `Flux_*`), quindi ogni valore produce file diversi. Il riferimento contiene solo `disc350`, cioè il valore usato. Nel primo commit della PR c'erano anche dei file `disc135`: erano avanzi di un run di prova precedente, nessun codice li produce con questi parametri, e sono stati rimossi.

**Versioni librerie** (pinnate come in `legacy-code/requirements.txt`, perché il test di CI confronta con rtol=1e-9):
- Python 3.12.0
- numpy 2.3.5, pandas 2.3.3, scipy 1.17.0, matplotlib 3.10.8

Rigenerato il 2026-10-27 con queste versioni: i dati sono identici byte per byte a quelli della prima generazione (2026-10-26, versioni "latest"), quindi per questi calcoli la versione non ha avuto effetto.

## 4. Contenuto di `reference/` e verifica

Ogni file è l'output flat legacy compresso con gzip (`np.loadtxt` e `pd.read_csv` leggono direttamente i `.gz`). La prima riga è l'intestazione, i separatori sono spazi, il fine riga è LF.

| File | Colonne | Righe dati |
|---|---|---|
| `angle_exp49.txt.gz` | `angle dists v` | 257.909 |
| `omega_exp49.txt.gz` | `omega dists time` | 248.905 |
| `ThetaY_exp49.txt.gz` | `theta_y dist` | 222.702 |
| `ThetaY_axis0_exp49.txt.gz` | `theta_y dist` (asse 0) | 222.702 |
| `ThetaY_axis1_exp49.txt.gz` | `theta_y dist` (asse 1) | 0: il legacy scrive solo l'intestazione |
| `Theta_exp49_FluoRadialised.txt.gz` | `Theta dists` | 47.931 |
| `tumb_dur_exp49_tthres5.0.txt.gz` | `dists duration time` | 13.900 |
| `N_dist_exp49_disc350.txt.gz` | `N n_disc dists` | 1.500 |
| `N_dist_compare_exp49_disc350.txt.gz` | `N_raw n_disc_raw dists_raw N n_disc dists` | 1.500 |
| `Flux_exp49_disc350.txt.gz` | `time flux` | 10 |

Non sono nel riferimento, perché duplicati o non confrontabili:
- i CSV di `results/<timestamp>/`: stessi dati dei `.txt`, in un altro formato
- il `tumb_exp49_tthres5.0.txt` generato: identico al file dell'operatrice già presente tra gli input (`../tumb_exp49_tthres5.0.txt`), il test può confrontarsi direttamente con quello
- i grafici PDF: binari, non confrontabili in un test; si rigenerano con `--plots` (sezione 6)

**Verifica: confronto riga per riga col file dell'operatrice. Match esatto, confermato automaticamente — non solo una stima.**

Confronto tra il `tumb_exp49_tthres5.0.txt` generato dallo script e `tumb_exp49_tthres5.0.txt` (fornito dall'operatrice, output originale del laboratorio):

- Righe: 27.787 generate = 27.787 dell'operatrice (conteggio identico)
- Confronto numerico elemento per elemento su tutte e 4 le colonne (`theta`, `dists`, `duration`, `time`): **0 righe con qualunque differenza, anche minima** (`np.array_equal` = True)
- Con i fine riga entrambi LF i due file sono identici anche byte per byte.

**Conclusione**: i parametri della sezione 3 sono quelli realmente usati dal laboratorio per produrre questo output. Non è ancora una conferma *esplicita* dell'operatrice (serve comunque la mail, sotto-task 1.3, anche per gli altri output non ancora verificati: theta, omega, angle, flux, N(t)) — ma è una conferma solida, verificata a livello di dato, non di stima.

## 5. Conferma dell'operatrice (via mail, US-1 1.3/1.4)

- Data mail inviata: [placeholder]
- Data risposta: [placeholder]
- Esito: [placeholder]
- Eventuali correzioni e data di rigenerazione: [placeholder]

## 6. Come rigenerare il riferimento

Dalla root del repo, con le versioni pinnate (sezione 3):

```
py -3.12 -m venv backend/.venv
backend/.venv/Scripts/python -m pip install numpy==2.3.5 pandas==2.3.3 scipy==1.17.0 matplotlib==3.10.8
backend/.venv/Scripts/python backend/scripts/make_reference.py
```

Su Linux/macOS il percorso è `backend/.venv/bin/python`. Lo script lavora in una cartella temporanea e scrive in `reference/` solo i `.txt.gz` della tabella sopra, con fine riga LF e header gzip senza data: con gli stessi input e le stesse versioni due esecuzioni danno file identici byte per byte, quindi `git status` resta pulito se non cambia niente. Alla fine stampa il confronto con il file di tumbling dell'operatrice.

Per avere anche i grafici PDF (da tenere fuori dal repo):

```
backend/.venv/Scripts/python backend/scripts/make_reference.py --plots <cartella>
```
