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

**Parametri plot Theta P(θ)**
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

Data di generazione: 2026-10-26. Versioni librerie: numpy/pandas/scipy/matplotlib correnti su Python 3.12 (non ancora allineate a `legacy-code/requirements.txt` — vedi nota sotto).

**Nota sulle versioni**: questo run usa le versioni "latest" di numpy/pandas/scipy/matplotlib, non quelle pinnate in `legacy-code/requirements.txt`. Il match numerico esatto ottenuto (sezione 4) suggerisce che per questi calcoli specifici (operazioni su float64 standard, niente randomness) la differenza di versione non ha avuto effetto in questo caso — ma resta una verifica da ripetere con le versioni pinnate prima di considerarlo definitivo per il test di CI (rtol=1e-9).

## 4. Verifica: confronto riga per riga col file dell'operatrice

**Match esatto, confermato automaticamente — non solo una stima.**

Confronto tra `reference/tumb_exp49_tthres5.0.txt` (generato da noi) e `tumb_exp49_tthres5.0.txt` (fornito dall'operatrice, output originale del laboratorio):

- Righe: 27.787 generate = 27.787 dell'operatrice (conteggio identico)
- Confronto numerico elemento per elemento su tutte e 4 le colonne (`theta`, `dists`, `duration`, `time`): **0 righe con qualunque differenza, anche minima** (`np.array_equal` = True)
- `np.allclose(..., rtol=1e-9)`: True (ben oltre la tolleranza richiesta dal test di regressione della US-1)
- L'unica differenza rilevata da un `diff` testuale grezzo è il fine riga (CRLF generato su Windows vs LF nel file originale prodotto su Linux) — un dettaglio di codifica del file, non una differenza nei dati.

**Conclusione**: i parametri della sezione 3 sono quelli realmente usati dal laboratorio per produrre questo output. Non è ancora una conferma *esplicita* dell'operatrice (serve comunque la mail, sotto-task 1.3, anche per gli altri output non ancora verificati: theta, omega, angle, flux, N(t)) — ma è una conferma solida, verificata a livello di dato, non di stima.

## 5. Conferma dell'operatrice (via mail, US-1 1.3/1.4)

- Data mail inviata: [placeholder]
- Data risposta: [placeholder]
- Esito: [placeholder]
- Eventuali correzioni e data di rigenerazione: [placeholder]

## 6. Come rigenerare il riferimento

```
python backend/scripts/make_reference.py
```
