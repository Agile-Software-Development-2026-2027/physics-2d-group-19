import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createJob, getJob } from '../../api/client/client.js'
import styles from './ProcessingPage.module.css'

// The phases written by the backend in status.json
const PHASES = {
  queued: 'In coda',
  tracking: 'Tracking delle cellule',
  analysis: 'Analisi',
  plots: 'Creazione dei grafici',
}

// pollMs: how often the status is read; the tests pass a shorter time
export function ProcessingPage({ pollMs = 2000 }) {
  const navigate = useNavigate()
  const [experiment, setExperiment] = useState('')
  const [kind, setKind] = useState('trajectories')
  const [mainFile, setMainFile] = useState(null)
  const [illumination, setIllumination] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)

  // A job is running from the click on 'Avvia' until it ends
  const running = status !== null && status !== 'done' && status !== 'error'

  // The main file must match the chosen kind; the illumination must be a TIFF image
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

  // Read the status every pollMs until the job is done or failed
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
    // Stop the timer when leaving the page
    return () => clearInterval(timer)
  }, [jobId, pollMs, navigate])

  return (
    <main className={styles.processingPage}>
      <h1>Elaborazione</h1>
      <label>
        Numero esperimento
        <input
          type="number"
          min="0"
          value={experiment}
          onChange={(e) => setExperiment(e.target.value)}
        />
      </label>
      <fieldset>
        <legend>Dati da caricare</legend>
        <label>
          <input
            type="radio"
            name="kind"
            checked={kind === 'trajectories'}
            onChange={() => setKind('trajectories')}
          />
          Traiettorie
        </label>
        <label>
          <input
            type="radio"
            name="kind"
            checked={kind === 'video'}
            onChange={() => setKind('video')}
          />
          Video
        </label>
      </fieldset>
      <label>
        Video o traiettorie
        <input
          type="file"
          accept={mainExtension}
          onChange={(e) => setMainFile(e.target.files[0] ?? null)}
        />
      </label>
      {mainFile && !mainOk && (
        <p className={styles.processingHint}>Il file deve essere {mainExtension}</p>
      )}
      <label>
        Illuminazione
        <input
          type="file"
          accept=".tif,.tiff"
          onChange={(e) => setIllumination(e.target.files[0] ?? null)}
        />
      </label>
      {illumination && !illuminationOk && (
        <p className={styles.processingHint}>
          L'illuminazione deve essere .tif o .tiff
        </p>
      )}
      <button
        type="button"
        onClick={start}
        disabled={!experiment || !mainOk || !illuminationOk || running}
      >
        Avvia
      </button>
      {running && (
        <p className={styles.processingPhase}>{PHASES[status] ?? status}</p>
      )}
      {error && (
        <p role="alert" className={styles.processingError}>
          {error}
        </p>
      )}
    </main>
  )
}