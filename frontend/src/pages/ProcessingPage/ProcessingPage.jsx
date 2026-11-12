import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createJob, getJob } from '../../api/client/client.js'
import { ParametersSection } from '../../components/ParametersSection/ParametersSection.jsx'

const PHASES = {
  queued: 'In coda',
  tracking: 'Tracking delle cellule',
  analysis: 'Analisi',
  plots: 'Creazione dei grafici',
}

const ANALYS_FIELDS = [
  { id: 'diam', label: 'Diameter (µm)' },
  { id: 'fluxCgIn', label: 'Flux CG In' },
  { id: 'dt', label: 'dt (s)', step: 0.1 },
  { id: 'fluxCgOut', label: 'Flux CG Out' },
  { id: 'discRadius', label: 'Disc Radius (µm)' },
  { id: 'nSkip', label: 'N Skip' },
  { id: 'tumblingThreshold', label: 'Tumbling Threshold (°/s)' },
  { id: 'useRadialMap', label: 'Use Radial Map', type: 'boolean' },
]

const PLOT_FIELDS = [
  { id: 'innerCircle', label: 'Inner Circle (µm)' },
  { id: 'thicknessCircle', label: 'Thickness Circle (µm)' },
  { id: 'maxDistance', label: 'Max Distance (µm)' },
]

const FILTER_FIELDS = [
  { id: 'lifetimeMin', label: 'Lifetime (min)', step: 0.1 },
  { id: 'blinkingRatio', label: 'Blinking Ratio', step: 0.1 },
  { id: 'thresholdDist', label: 'Threshold distance' },
  { id: 'blinkingTolerance', label: 'Blinking Tolerance', step: 0.1 },
  { id: 'thresholdDistTot', label: 'Threshold total distance' },
  { id: 'longTrackMinSnaps', label: 'Long Track Min Snaps' },
  { id: 'distStep', label: 'Step distance' },
  { id: 'strict', label: 'Strict', type: 'boolean' },
  { id: 'onlyInside', label: 'Only inside', type: 'boolean' },
]

export function ProcessingPage({ pollMs = 2000 }) {
  const navigate = useNavigate()
  const [experiment, setExperiment] = useState('')

  const [kindDataInput, setKindDataInput] = useState('trajectories')
  const [kindMachine, setKindMachine] = useState('microscope2d')
  const [mainFile, setMainFile] = useState(null)
  const [illumination, setIllumination] = useState(null)
  const [settings, setSettings] = useState(null)
  const [radialMap, setRadialMap] = useState(null)

  const [analysParams, setAnalysisParams] = useState({
    diam: 10,
    fluxCgIn: 1,
    dt: 0.1,
    fluxCgOut: 150,
    discRadius: 350,
    nSkip: 1,
    tumblingThreshold: 5,
    useRadialMap: false,
  })
  const [plotParams, setPlotParams] = useState({
    innerCircle: 300,
    thicknessCircle: 0,
    maxDistance: 800,
  })
  const [filterParams, setFilterParams] = useState({
    lifetimeMin: 0,
    thresholdDist: 0,
    blinkingRatio: 0,
    blinkingTolerance: 0,
    thresholdDistTot: 0,
    longTrackMinSnaps: 0,
    distStep: 1,
    strict: true,
    onlyInside: true,
  })

  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)

  const running = status !== null && status !== 'done' && status !== 'error'

  const mainExtension = kindDataInput === 'video' ? '.avi' : '.txt'
  const mainOk = mainFile?.name.toLowerCase().endsWith(mainExtension)
  const illuminationName = illumination?.name.toLowerCase() ?? ''
  const settingsName = settings?.name ?? ''
  const illuminationOk = illuminationName.endsWith('.tif') || illuminationName.endsWith('.tiff')
  const settingsOk = settingsName.endsWith('.txt')
  const radialMapOk = !analysParams.useRadialMap || Boolean(radialMap)

  async function start() {
    setError(null)
    setStatus('queued')
    const formData = new FormData()

    // Campi letti dall'attuale jobs.py
    formData.append('exp_id', experiment.trim())
    formData.append(kindDataInput, mainFile)
    formData.append('illumination', illumination)

    // Campi già pronti per il futuro aggiornamento del backend
    formData.append('machine', kindMachine)
    if (settings) {
      formData.append('settings', settings)
    }
    if (analysParams.useRadialMap && radialMap) {
      formData.append('radial_map', radialMap)
    }
    formData.append('analysis_params', JSON.stringify(analysParams))
    formData.append('plot_params', JSON.stringify(plotParams))
    formData.append('filter_params', JSON.stringify(filterParams))

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
    <div className="p-6 max-w-5xl mx-auto my-6 space-y-6">

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

        {/* 2. SELETTORE TIPO INPUT ANALISI */}
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

        {/* 3. CAMPO NUMERO ESPERIMENTO */}
        <div className="relative space-y-2">
          <div className="flex justify-between items-center">
            <label htmlFor="experiment-input" className="text-sm font-semibold text-text">
              ID esperimenti
            </label>
          </div>

          <input
            id="experiment-input"
            type="text"
            placeholder="Es. 49"
            value={experiment}
            onChange={(e) => setExperiment(e.target.value)}
            className="w-full px-4 py-2.5 rounded-xl border border-border bg-bg text-text font-normal focus:outline-none focus:ring-2 focus:ring-alga/50 focus:border-alga transition-all"
          />
        </div>

        {/* 4. FILE CARICATI & SUBMIT */}
        <div className="pt-2">

          {/* FILE PRINCIPALE */}
          <div className="mb-8 pb-7 border-b border-border">
            <div className="p-5 rounded-2xl border-2 border-dashed border-alga/40 bg-alga-light/15 hover:border-alga transition-colors space-y-3">
              <div className="flex items-center justify-between">
                <label htmlFor="main-file-input" className="text-base font-bold text-text cursor-pointer flex items-center gap-2">
                  {kindDataInput === 'video' ? 'Carica video (*.avi)' : 'Carica traiettoria (*.txt)'}
                </label>
              </div>

              <input
                id="main-file-input"
                type="file"
                accept={mainExtension}
                onChange={(e) => setMainFile(e.target.files[0] ?? null)}
                className="block w-full text-sm text-text-muted border border-border rounded-xl bg-surface cursor-pointer file:mr-4 file:py-3 file:px-5 file:rounded-l-xl file:border-0 file:text-sm file:font-semibold file:bg-alga file:text-white hover:file:bg-alga-hover transition-all"
              />

              {mainFile && !mainOk && (
                <p className="text-xs font-medium text-amber-600 dark:text-amber-400">
                  Il file deve essere {mainExtension}
                </p>
              )}
            </div>
          </div>

          <div className="space-y-5">
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
                  L&apos;illuminazione deve essere .tif o .tiff
                </p>
              )}
            </div>

            {/* File settings */}
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

            {/* File Mappa radiale */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="radial-map-file-input" className="text-sm font-semibold text-text cursor-pointer">
                Carica file Mappa radiale
              </label>
              <input
                id="radial-map-file-input"
                type="file"
                onChange={(e) => {
                  const file = e.target.files[0] ?? null
                  setRadialMap(file)
                  // Opzionale: attiva automaticamente lo switch se l'utente carica un file
                  if (file) {
                    setAnalysisParams((prev) => ({ ...prev, useRadialMap: true }))
                  }
                }}
                className="block w-full text-sm text-text-muted border border-border rounded-xl bg-bg cursor-pointer file:mr-4 file:py-2.5 file:px-4 file:rounded-l-xl file:border-0 file:text-sm file:font-semibold file:bg-alga-light file:text-alga hover:file:bg-alga/20 transition-all"
              />
              {analysParams.useRadialMap && !radialMap && (
                <p className="text-xs font-medium text-amber-600 dark:text-amber-400">
                  Hai attivato &quot;Use Radial Map&quot;: carica il file corrispondente
                </p>
              )}
            </div>

            {/* Parametri di Analisi */}
            <ParametersSection
              title="Parametri di Analisi"
              fields={ANALYS_FIELDS}
              values={analysParams}
              onChange={setAnalysisParams}
            />

            {/* Parametri plot Theta p0 */}
            <ParametersSection
              title="Parametri Plot Theta p0"
              fields={PLOT_FIELDS}
              values={plotParams}
              onChange={setPlotParams}
            />

            {/* Parametri filtri */}
            <ParametersSection
              title="Filtri traiettorie"
              fields={FILTER_FIELDS}
              values={filterParams}
              onChange={setFilterParams}
            />

            {/* Pulsante Avvia */}
            <div className="pt-2">
              <button
                type="button"
                onClick={start}
                disabled={!experiment || !mainOk || !illuminationOk || !radialMapOk || running}
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
    </div>
  )
}