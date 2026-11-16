import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createJob, getJob } from '../../api/client/client.js'

export type MachineType = 'microscope2d' | 'photonicsLab' | 'lightfield'
export type InputDataType = 'trajectories' | 'video'
export type JobStatus = 'queued' | 'tracking' | 'analysis' | 'plots' | 'done' | 'error'

export interface FieldConfig {
  id: string
  label: string
  step?: number
  min?: number
  type?: 'number' | 'boolean'
}

export interface AnalysisParams {
  diam: number
  fluxCgIn: number
  dt: number
  fluxCgOut: number
  discRadius: number
  nSkip: number
  tumblingThreshold: number
  useRadialMap: boolean
}

export interface PlotParams {
  innerCircle: number
  thicknessCircle: number
  maxDistance: number
}

export interface FilterParams {
  lifetimeMin: number
  thresholdDist: number
  blinkingRatio: number
  blinkingTolerance: number
  thresholdDistTot: number
  longTrackMinSnaps: number
  distStep: number
  strict: boolean
  onlyInside: boolean
}

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

export const ANALYS_FIELDS: FieldConfig[] = [
  { id: 'diam', label: 'Diameter (µm)' },
  { id: 'fluxCgIn', label: 'Flux CG In' },
  { id: 'dt', label: 'dt (s)', step: 0.1 },
  { id: 'fluxCgOut', label: 'Flux CG Out' },
  { id: 'discRadius', label: 'Disc Radius (µm)' },
  { id: 'nSkip', label: 'N Skip' },
  { id: 'tumblingThreshold', label: 'Tumbling Threshold (°/s)' },
  { id: 'useRadialMap', label: 'Use Radial Map', type: 'boolean' },
]

export const PLOT_FIELDS: FieldConfig[] = [
  { id: 'innerCircle', label: 'Inner Circle (µm)' },
  { id: 'thicknessCircle', label: 'Thickness Circle (µm)' },
  { id: 'maxDistance', label: 'Max Distance (µm)' },
]

export const FILTER_FIELDS: FieldConfig[] = [
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

export const DEFAULT_ANALYSIS_PARAMS: AnalysisParams = {
  diam: 10,
  fluxCgIn: 1,
  dt: 0.1,
  fluxCgOut: 150,
  discRadius: 350,
  nSkip: 1,
  tumblingThreshold: 5,
  useRadialMap: false,
}

export const DEFAULT_PLOT_PARAMS: PlotParams = {
  innerCircle: 300,
  thicknessCircle: 0,
  maxDistance: 800,
}

export const DEFAULT_FILTER_PARAMS: FilterParams = {
  lifetimeMin: 0,
  thresholdDist: 0,
  blinkingRatio: 0,
  blinkingTolerance: 0,
  thresholdDistTot: 0,
  longTrackMinSnaps: 0,
  distStep: 1,
  strict: true,
  onlyInside: true,
}

export function useProcessingPageModel(pollMs = 2000) {
  const navigate = useNavigate()

  const [experiment, setExperiment] = useState('')
  const [kindDataInput, setKindDataInput] = useState<InputDataType>('trajectories')
  const [kindMachine, setKindMachine] = useState<MachineType>('microscope2d')

  const [mainFile, setMainFile] = useState<File | null>(null)
  const [illumination, setIllumination] = useState<File | null>(null)
  const [settings, setSettings] = useState<File | null>(null)
  const [radialMap, setRadialMap] = useState<File | null>(null)

  const [analysParams, setAnalysisParams] = useState<AnalysisParams>(DEFAULT_ANALYSIS_PARAMS)
  const [plotParams, setPlotParams] = useState<PlotParams>(DEFAULT_PLOT_PARAMS)
  const [filterParams, setFilterParams] = useState<FilterParams>(DEFAULT_FILTER_PARAMS)

  const [jobId, setJobId] = useState<string | null>(null)
  const [status, setStatus] = useState<JobStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Validazioni derivate
  const running = status !== null && status !== 'done' && status !== 'error'
  const mainExtension = kindDataInput === 'video' ? '.avi' : '.txt'
  const mainOk = Boolean(mainFile?.name.toLowerCase().endsWith(mainExtension))
  const illuminationName = illumination?.name.toLowerCase() ?? ''
  const illuminationOk = illuminationName.endsWith('.tif') || illuminationName.endsWith('.tiff')
  const settingsOk = (settings?.name.toLowerCase() ?? '').endsWith('.txt')
  const radialMapOk = !analysParams.useRadialMap || Boolean(radialMap)
  const canSubmit = Boolean(experiment.trim()) && mainOk && illuminationOk && radialMapOk && !running

  async function start() {
    if (!mainFile || !illumination) return

    setError(null)
    setStatus('queued')
    const formData = new FormData()

    formData.append('exp_id', experiment.trim())
    formData.append(kindDataInput, mainFile)
    formData.append('illumination', illumination)
    formData.append('machine', kindMachine)
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

  return {
    // Costanti
    PHASES,
    MACHINES,
    ANALYS_FIELDS,
    PLOT_FIELDS,
    FILTER_FIELDS,
    // Stato e setter
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
    analysParams,
    setAnalysisParams,
    plotParams,
    setPlotParams,
    filterParams,
    setFilterParams,
    status,
    error,
    // Flag calcolati e azioni
    running,
    mainExtension,
    mainOk,
    illuminationOk,
    canSubmit,
    start,
  }
}