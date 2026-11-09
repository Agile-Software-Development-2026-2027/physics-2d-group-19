import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createJob, getJob } from '../../api/client/client.js'
import { parseExperimentIds } from '../../utility/splitExperimentID.js'

const PHASES = {
  queued: 'In coda',
  tracking: 'Tracking delle cellule',
  analysis: 'Analisi',
  plots: 'Creazione dei grafici',
}

const AVAILABLE_EXPERIMENTS = [
  { id: '49', name: 'exp_049_algae_tracking', date: '01 Nov 2026' },
  { id: '50', name: 'exp_050_fluorescence_test', date: '03 Nov 2026' },
  { id: '51', name: 'exp_051_photonics_run', date: '05 Nov 2026' },
  { id: '52', name: 'exp_052_lightfield_scan', date: '08 Nov 2026' },
  { id: '53', name: 'exp_053_high_density', date: '09 Nov 2026' },
]


export function ProcessingPage({ pollMs = 2000 }) {
  const navigate = useNavigate()
  const [experiment, setExperiment] = useState('')
  const [isFolderOpen, setIsFolderOpen] = useState(false)

  const [kindDataInput, setKindDataInput] = useState('trajectories')
  const [kindMachine, setKindMachine] = useState('microscope2d')
  const [mainFile, setMainFile] = useState(null)
  const [illumination, setIllumination] = useState(null)
  const [settings, setSettings] = useState(null)
  const [analysParams, setAnalysisParams] = useState({
    diam: 10,
    fluxCgIn: 1,
    dt: 0.1,
    fluxCgOut: 150,
    discRadius: 350,
    nSkip: 1,
    tumblingThreshold: 5,
    useRadialMap: false
  })
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)

  const running = status !== null && status !== 'done' && status !== 'error'

  // Calcola in tempo reale la lista degli ID risolti (inclusi i range)
  const parsedExpIds = parseExperimentIds(experiment)

  const mainExtension = kindDataInput === 'video' ? '.avi' : '.txt'
  const mainOk = mainFile?.name.toLowerCase().endsWith(mainExtension)
  const illuminationName = illumination?.name.toLowerCase() ?? ''
  const settingsName = settings?.name ?? ''
  const illuminationOk = illuminationName.endsWith('.tif') || illuminationName.endsWith('.tiff')
  const settingsOk = settingsName.endsWith('.txt')

  // Aggiunge o rimuove un ID dalla selezione
  function toggleExperiment(id) {
    const updated = parsedExpIds.includes(id)
      ? parsedExpIds.filter((item) => item !== id)
      : [...parsedExpIds, id]

    setExperiment(updated.join(', '))
  }
  // Aumenta o Diminuisci i valori dei parametri
  function updateParam(key, value) {
    setAnalysisParams((prev) => ({
      ...prev,
      [key]: Math.max(0, (prev[key] || 0) + value),
    }))
  }

  async function start() {
    setError(null)
    setStatus('queued')
    const formData = new FormData()

    formData.append('exp_id', parsedExpIds.join(','))
    formData.append('machine', kindMachine)
    formData.append(kindDataInput, mainFile)
    formData.append('illumination', illumination)
    formData.append('settings', settings)

    try {
      const job = await createJob(formData)
      setJobId(job.job_id)
    } catch {
      setStatus(null)
      setError("Impossibile avviare l'elaborazione.")
    }
  }

  useEffect(() => {
    if (!jobId) return
    const timer = setInterval(async () => {
      try {
        const job = await getJob(jobId)
        setStatus(job.status)
        if (job.status === 'done') {
          clearInterval(timer)
          navigate(`/risultati/${jobId}`)
        } else if (job.status === 'error') {
          clearInterval(timer)
          setError(job.error)
        }
      } catch {
        clearInterval(timer)
        setStatus('error')
        setError("Stato dell'elaborazione non disponibile.")
      }
    }, pollMs)

    return () => clearInterval(timer)
  }, [jobId, pollMs, navigate])

  return (
    <div className="max-w-2xl mx-auto my-6 space-y-6">

      {/* 1. SELETTORE MACCHINA */}
      <fieldset className="space-y-1.5">
        <legend className="text-sm font-semibold text-text">Seleziona Macchina utilizzata</legend>
        <div className="inline-flex p-1 bg-bg border border-border rounded-xl w-full">
          {['microscope2d', 'photonicsLab', 'lightfield'].map((machine) => (
            <label
              key={machine}
              className={`flex-1 text-center py-2 px-4 rounded-lg text-sm font-medium transition-all duration-150 cursor-pointer ${
                kindMachine === machine
                  ? 'bg-surface text-alga shadow-xs font-semibold border border-border/50'
                  : 'text-text-muted hover:text-text'
              }`}
            >
              <input
                type="radio"
                name="kindMachine"
                checked={kindMachine === machine}
                onChange={() => setKindMachine(machine)}
                className="sr-only"
              />
              {machine === 'microscope2d' ? 'Microscope2D' : machine === 'photonicsLab' ? 'PhotonicsLab' : 'LightField'}
            </label>
          ))}
        </div>
      </fieldset>

      {/* CARD FORM ELABORAZIONE */}
      <div className="p-6 md:p-8 bg-surface border border-border rounded-2xl shadow-sm text-left space-y-6">

        {/* 2. SELETTORE TIPO INPUT Analisi */}
        <fieldset className="space-y-1.5">
          <legend className="text-sm font-semibold text-text">Cosa vuoi analizzare?</legend>
          <div className="inline-flex p-1 bg-bg border border-border rounded-xl w-full">
            <label
              className={`flex-1 text-center py-2 px-4 rounded-lg text-sm font-medium transition-all duration-150 cursor-pointer ${
                kindDataInput === 'trajectories'
                  ? 'bg-surface text-alga shadow-xs font-semibold border border-border/50'
                  : 'text-text-muted hover:text-text'
              }`}
            >
              <input
                type="radio"
                name="kindDataInput"
                checked={kindDataInput === 'trajectories'}
                onChange={() => setKindDataInput('trajectories')}
                className="sr-only"
              />
              Traiettorie
            </label>

            <label
              className={`flex-1 text-center py-2 px-4 rounded-lg text-sm font-medium transition-all duration-150 cursor-pointer ${
                kindDataInput === 'video'
                  ? 'bg-surface text-alga shadow-xs font-semibold border border-border/50'
                  : 'text-text-muted hover:text-text'
              }`}
            >
              <input
                type="radio"
                name="kindDataInput"
                checked={kindDataInput === 'video'}
                onChange={() => setKindDataInput('video')}
                className="sr-only"
              />
              Video
            </label>
          </div>
        </fieldset>

        {/* 3. CAMPO NUMERO ESPERIMENTO CON SUPPORTO RANGE + CARTELLA */}
        <div className="relative space-y-2">
          <div className="flex justify-between items-center">
            <label htmlFor="experiment-input" className="text-sm font-semibold text-text">
              ID esperimenti
            </label>

            <button
              type="button"
              onClick={() => setIsFolderOpen(!isFolderOpen)}
              className="text-xs font-semibold text-alga hover:underline flex items-center gap-1 cursor-pointer"
            >
              <i className="fa-regular fa-folder-open"></i>
              {isFolderOpen ? 'Chiudi cartella' : 'Sfoglia cartella esperimenti'}
            </button>
          </div>

          <input
            id="experiment-input"
            type="text"
            placeholder="Es. 49,50... o anché un range di esperimenti 49-60"
            value={experiment}
            onChange={(e) => setExperiment(e.target.value)}
            className="w-full px-4 py-2.5 rounded-xl border border-border bg-bg text-text font-normal focus:outline-none focus:ring-2 focus:ring-alga/50 focus:border-alga transition-all"
          />

          {/*<p className="text-xs text-text-muted">
            Puoi inserire un numero singolo (<code className="font-mono text-alga">49</code>), liste (<code className="font-mono text-alga">49, 50</code>) o intervalli (<code className="font-mono text-alga">49-53</code>).
          </p>*/}

          {/* Tag con gli ID espansi in tempo reale */}
          {parsedExpIds.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-1">
              <span className="text-xs text-text-muted self-center mr-1">Trovati ({parsedExpIds.length}):</span>
              {parsedExpIds.map((id) => (
                <span
                  key={id}
                  className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-xs font-medium bg-alga-light text-alga border border-alga/20"
                >
                  #{id}
                  <button
                    type="button"
                    onClick={() => toggleExperiment(id)}
                    className="hover:text-red-500 font-bold ml-1 cursor-pointer"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}

          {/* TENDINA CARTELLA DROPDOWN */}
          {isFolderOpen && (
            <div className="absolute z-10 w-full mt-1 p-3 bg-surface border border-border rounded-xl shadow-lg space-y-2 text-left">
              <div className="flex justify-between items-center pb-2 border-b border-border text-xs text-text-muted">
                <span>Percorso: <code className="font-mono bg-bg px-1 rounded">/data/esperimenti/</code></span>
                <span>{parsedExpIds.length} selezionati</span>
              </div>

              <div className="max-h-48 overflow-y-auto space-y-1 pr-1">
                {AVAILABLE_EXPERIMENTS.map((exp) => {
                  const isChecked = parsedExpIds.includes(exp.id)
                  return (
                    <label
                      key={exp.id}
                      className={`flex items-center justify-between p-2 rounded-lg text-sm cursor-pointer transition-colors ${
                        isChecked ? 'bg-alga-light/60 text-alga font-medium' : 'hover:bg-bg text-text'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => toggleExperiment(exp.id)}
                          className="w-4 h-4 text-alga border-border rounded focus:ring-alga cursor-pointer"
                        />
                        <span>#{exp.id} - {exp.name}</span>
                      </div>
                      <span className="text-xs text-text-muted">{exp.date}</span>
                    </label>
                  )
                })}
              </div>
            </div>
          )}
        </div>

        {/* 4. FILE CARICATI & SUBMIT */}
        <div className="space-y-5 pt-2">
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between">
              <label htmlFor="main-file-input" className="text-sm font-semibold text-text cursor-pointer">
                {kindDataInput === "video" ? "Carica video (*.avi)" : "Carica traiettoria (*.txt)"}
              </label>
            </div>
            <input
              id="main-file-input"
              type="file"
              accept={mainExtension}
              onChange={(e) => setMainFile(e.target.files[0] ?? null)}
              className="block w-full text-sm text-text-muted border border-border rounded-xl bg-bg cursor-pointer file:mr-4 file:py-2.5 file:px-4 file:rounded-l-xl file:border-0 file:text-sm file:font-semibold file:bg-alga-light file:text-alga hover:file:bg-alga/20 transition-all"
            />
            {mainFile && !mainOk && (
              <p className="text-xs font-medium text-amber-600 dark:text-amber-400">
                Il file deve essere {mainExtension}
              </p>
            )}
          </div>

          {/* File illuminazione */}
          <div className="flex flex-col gap-1.5">
            <label htmlFor="illumination-file-input" className="text-sm font-semibold text-text cursor-pointer">
              Carica file Illuminazione (*.tiff | *.tif)
            </label>
            <input
              id="illumination-file-input"
              type="file"
              accept=".tif,.tiff"
              onChange={(e) => setIllumination(e.target.files[0] ?? null)}
              className="block w-full text-sm text-text-muted border border-border rounded-xl bg-bg cursor-pointer file:mr-4 file:py-2.5 file:px-4 file:rounded-l-xl file:border-0 file:text-sm file:font-semibold file:bg-alga-light file:text-alga hover:file:bg-alga/20 transition-all"
            />
            {illumination && !illuminationOk && (
              <p className="text-xs font-medium text-amber-600 dark:text-amber-400">
                L'illuminazione deve essere .tif o .tiff
              </p>
            )}
          </div>

          {/*File settings*/}
          <div className="flex flex-col gap-1.5">
            <label htmlFor="settings-file-input" className="text-sm font-semibold text-text cursor-pointer">
              Carica file Settings (*.txt)
            </label>
            <input
              id="settings-file-input"
              type="file"
              accept=".txt"
              onChange={(e) => setSettings(e.target.files[0] ?? null)}
              className="block w-full text-sm text-text-muted border border-border rounded-xl bg-bg cursor-pointer file:mr-4 file:py-2.5 file:px-4 file:rounded-l-xl file:border-0 file:text-sm file:font-semibold file:bg-alga-light file:text-alga hover:file:bg-alga/20 transition-all"
            />
            {settings && !settingsOk && (
              <p className="text-xs font-medium text-amber-600 dark:text-amber-400">
                Il file settings deve essere .txt
              </p>
            )}
          </div>

          {/* Parametri di Analisi */}
          <details className="group border border-border rounded-xl bg-surface p-4">
            <summary className="flex items-center justify-between font-semibold text-text cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden">
              <span>Parametri Analisi</span>

              <svg
                className="w-4 h-4 text-text-muted transition-transform duration-200 group-open:rotate-180"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </summary>

            <div className="mt-4 pt-4 border-t border-border grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[
                { id: 'diam', label: 'Diametro' },
                { id: 'fluxCgIn', label: 'Flusso CG In' },
                { id: 'dt', label: 'dt (Intervallo)', step: 0.1 },
                { id: 'fluxCgOut', label: 'Flusso CG Out' },
                { id: 'discRadius', label: 'Raggio Disco' },
                { id: 'nSkip', label: 'N Skip' },
                { id: 'tumblingThreshold', label: 'Soglia Tumbling' },
              ].map((field) => (
                <div
                  key={field.id}
                  className="flex items-center justify-between p-2.5 rounded-xl border border-border bg-bg"
                >
                  <span className="text-xs font-semibold text-text">{field.label}</span>

                  {/* Controlli +/- e Input */}
                  <div className="flex items-center gap-1 bg-surface border border-border rounded-lg p-0.5">
                    <button
                      type="button"
                      onClick={() => updateParam(field.id, -(field.step || 1))}
                      className="w-7 h-7 flex items-center justify-center rounded-md bg-bg hover:bg-border text-text font-bold text-sm transition-colors cursor-pointer select-none active:scale-95"
                    >
                      -
                    </button>

                    <input
                      type="number"
                      step={field.step || 1}
                      value={analysParams[field.id]}
                      onChange={(e) =>
                        setAnalysisParams({
                          ...analysParams,
                          [field.id]: Number(e.target.value) || 0,
                        })
                      }
                      className="w-12 text-center text-xs font-semibold text-text bg-transparent focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    />

                    <button
                      type="button"
                      onClick={() => updateParam(field.id, field.step || 1)}
                      className="w-7 h-7 flex items-center justify-center rounded-md bg-bg hover:bg-border text-text font-bold text-sm transition-colors cursor-pointer select-none active:scale-95"
                    >
                      +
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </details>


          {/* Pulsante Avvia */}
          <div className="pt-2">
            <button
              type="button"
              onClick={start}
              disabled={!experiment || !mainOk || !illuminationOk || running}
              className="w-full py-3 px-6 rounded-xl font-semibold text-white bg-alga hover:bg-alga-hover shadow-xs transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer flex items-center justify-center gap-2"
            >
              {running && (
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              )}
              Avvia
            </button>
          </div>

          {/* Fasi e Errori */}
          {running && (
            <div className="flex items-center gap-3 p-4 rounded-xl bg-alga-light/50 border border-alga/20 text-alga font-medium text-sm animate-pulse">
              <span className="w-2.5 h-2.5 rounded-full bg-alga animate-ping" />
              {PHASES[status] ?? status}
            </div>
          )}

          {error && (
            <p role="alert" className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 text-sm font-medium">
              {error}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}