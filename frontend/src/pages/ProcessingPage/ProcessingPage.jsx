import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createJob, getJob } from '../../api/client/client.js'

const PHASES = {
  queued: 'In coda',
  tracking: 'Tracking delle cellule',
  analysis: 'Analisi',
  plots: 'Creazione dei grafici',
}

export function ProcessingPage({ pollMs = 2000 }) {
  const navigate = useNavigate()
  const [experiment, setExperiment] = useState('')
  const [kind, setKind] = useState('trajectories')
  const [mainFile, setMainFile] = useState(null)
  const [illumination, setIllumination] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)

  const running = status !== null && status !== 'done' && status !== 'error'

  const mainExtension = kind === 'video' ? '.avi' : '.txt'
  const mainOk = mainFile?.name.toLowerCase().endsWith(mainExtension)
  const illuminationName = illumination?.name.toLowerCase() ?? ''
  const illuminationOk = illuminationName.endsWith('.tif') || illuminationName.endsWith('.tiff')

  async function start() {
    setError(null)
    setStatus('queued')
    const formData = new FormData()
    formData.append('exp_id', experiment)
    formData.append(kind, mainFile)
    formData.append('illumination', illumination)
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
    <div className="max-w-2xl mx-auto my-6 p-6 md:p-8 bg-surface border border-border rounded-2xl shadow-sm space-y-6">
      <h1 className="text-3xl font-bold text-text font-sponge tracking-wide border-b border-border pb-3">
        Elaborazione
      </h1>

      <div className="space-y-5">
        {/* Numero Esperimento */}
        <label className="flex flex-col gap-1.5 text-sm font-semibold text-text">
          Numero esperimento
          <input
            type="number"
            min="0"
            value={experiment}
            onChange={(e) => setExperiment(e.target.value)}
            className="w-full px-4 py-2.5 rounded-xl border border-border bg-bg text-text font-normal focus:outline-none focus:ring-2 focus:ring-alga/50 focus:border-alga transition-all"
          />
        </label>

        {/* Selezione Dati */}
        <fieldset className="border border-border rounded-xl p-4 bg-bg/50 space-y-3">
          <legend className="px-2 text-xs font-semibold text-text-muted uppercase tracking-wider">
            Dati da caricare
          </legend>
          <div className="flex items-center gap-6">
            <label className="flex items-center gap-2 text-sm font-medium text-text cursor-pointer">
              <input
                type="radio"
                name="kind"
                checked={kind === 'trajectories'}
                onChange={() => setKind('trajectories')}
                className="w-4 h-4 text-alga border-border focus:ring-alga cursor-pointer"
              />
              Traiettorie
            </label>
            <label className="flex items-center gap-2 text-sm font-medium text-text cursor-pointer">
              <input
                type="radio"
                name="kind"
                checked={kind === 'video'}
                onChange={() => setKind('video')}
                className="w-4 h-4 text-alga border-border focus:ring-alga cursor-pointer"
              />
              Video
            </label>
          </div>
        </fieldset>

        {/* File principale */}
        <div className="flex flex-col gap-1.5">
          <label htmlFor="main-file-input" className="text-sm font-semibold text-text cursor-pointer">
            Video o traiettorie
          </label>
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
            Illuminazione
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
  )
}