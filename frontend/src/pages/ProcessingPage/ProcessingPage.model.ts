import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createJob, getJob } from '../../api/client/client.js'

export type MachineType = 'microscope2d' | 'photonicsLab' | 'lightfield'
export type InputDataType = 'trajectories' | 'video'
export type JobStatus = 'queued' | 'tracking' | 'analysis' | 'plots' | 'done' | 'error'

export const PHASES: Record<string, string> = {
  queued: 'In coda',
  tracking: 'Tracking delle cellule',
  analysis: 'Analisi',
  plots: 'Creazione dei grafici',
}

export const MACHINES: { id: MachineType; label: string }[] = [
  { id: 'microscope2d', label: 'Microscope2D' },
  { id: 'photonicsLab', label: 'PhotonicsLab' },
  { id: 'lightfield', label: 'LightField' },
]

export function useProcessingPageModel(pollMs = 2000) {
  const navigate = useNavigate()

  const [experiment, setExperiment] = useState('')
  const [kindDataInput, setKindDataInput] = useState<InputDataType>('trajectories')
  const [kindMachine, setKindMachine] = useState<MachineType>('microscope2d')

  const [mainFile, setMainFile] = useState<File | null>(null)
  const [illumination, setIllumination] = useState<File | null>(null)

  // Dynamic parameters from ParamsForm
  const [params, setParams] = useState<any>(null)
  const [paramsValid, setParamsValid] = useState(true)
  const [makeGif, setMakeGif] = useState(false)

  const [jobId, setJobId] = useState<string | null>(null)
  const [status, setStatus] = useState<JobStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Derived validations
  const running = status !== null && status !== 'done' && status !== 'error'
  const mainExtension = kindDataInput === 'video' ? '.avi' : '.txt'
  const mainOk = Boolean(mainFile?.name.toLowerCase().endsWith(mainExtension))
  const illuminationName = illumination?.name.toLowerCase() ?? ''
  const illuminationOk = illuminationName.endsWith('.tif') || illuminationName.endsWith('.tiff')
  const canSubmit = Boolean(experiment.trim()) && mainOk && illuminationOk && paramsValid && !running

  const handleParamsChange = (newParams: any, isValid: boolean) => {
    setParams(newParams)
    setParamsValid(isValid)
  }

  async function start() {
    if (!mainFile || !illumination || !paramsValid) return

    setError(null)
    setStatus('queued')
    const formData = new FormData()

    formData.append('exp_id', experiment.trim())
    formData.append(kindDataInput, mainFile)
    formData.append('illumination', illumination)
    formData.append('machine', kindMachine)
    if (params) {
      formData.append('params', JSON.stringify(params))
    }
    formData.append('make_gif', String(makeGif))

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

  return {
    PHASES,
    MACHINES,
    experiment,
    setExperiment,
    kindDataInput,
    setKindDataInput,
    kindMachine,
    setKindMachine,
    mainFile,
    setMainFile,
    illumination,
    setIllumination,
    params,
    paramsValid,
    handleParamsChange,
    makeGif,
    setMakeGif,
    status,
    error,
    running,
    mainExtension,
    mainOk,
    illuminationOk,
    canSubmit,
    start,
  }
}