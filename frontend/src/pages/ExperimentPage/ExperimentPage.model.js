import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getExperiments, saveExperiment, exportExperiments, importExperiments } from '../../api/client/client.js'

// Default values populated when initiating a new experiment
export const DEFAULT_EXPERIMENT = {
  exps: '',
  exp_type: 1,
  ill: 14,
  intensity: 180,
  pix_arr: 1.041667,
  no_skip: true,
  ctr: 0,
  fluo: 0,
  lin: 0,
  axis: 0,
}

// Select dropdown options matching backend ExperimentSettings field descriptions
export const EXP_TYPES = [
  { value: 0, label: '0 = none' },
  { value: 1, label: '1 = normal' },
  { value: 2, label: '2 = gaussian' },
  { value: 3, label: '3 = outside' },
  { value: 4, label: '4 = single cell' },
  { value: 5, label: '5 = LED' },
]

export const CTR_OPTIONS = [
  { value: -1, label: '-1 = left' },
  { value: 0, label: '0 = centre' },
  { value: 1, label: '1 = right' },
]

export const FLUO_OPTIONS = [
  { value: 0, label: '0 = none' },
  { value: 1, label: '1 = ring' },
  { value: 2, label: '2 = gaussian' },
]

export const LIN_OPTIONS = [
  { value: 0, label: '0 = no' },
  { value: 1, label: '1 = yes' },
]

export const AXIS_OPTIONS = [
  { value: 0, label: '0 = x' },
  { value: 1, label: '1 = y' },
]

// Custom hook encapsulating state, validation, and API interactions for ExperimentPage
export function useExperimentPageModel() {
  const navigate = useNavigate()

  const [experiments, setExperiments] = useState([])
  const [selectedExpId, setSelectedExpId] = useState(null)
  const [formData, setFormData] = useState(DEFAULT_EXPERIMENT)
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState(null)
  const [isEditing, setIsEditing] = useState(false)
  const [transferring, setTransferring] = useState(false)

  // Fetch list of registered experiments on component mount
  const fetchExperiments = () => {
    getExperiments()
      .then((data) => setExperiments(data || []))
      .catch(() =>
        setMessage({ type: 'error', text: 'Could not load the experiments.' }),
      )
  }

  useEffect(() => {
    fetchExperiments()
  }, [])

  // Select an existing experiment to view and edit its parameters
  const selectExperiment = (exp) => {
    setSelectedExpId(exp.exps)
    setFormData({ ...exp })
    setIsEditing(true)
    setErrors({})
    setMessage(null)
  }

  // Reset form to default values for creating a new experiment
  const newExperiment = () => {
    setSelectedExpId(null)
    setFormData(DEFAULT_EXPERIMENT)
    setIsEditing(false)
    setErrors({})
    setMessage(null)
  }

  // Update a form field and clear its active inline validation error
  const updateField = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors((prev) => {
        const updated = { ...prev }
        delete updated[field]
        return updated
      })
    }
  }

  // Import experiments from a legacy Clamidomoni_settings.txt file
  const handleImport = async (file) => {
    if (!file) return
    setTransferring(true)
    setMessage(null)
    try {
      const res = await importExperiments(file)
      const baseSummary = `Import completed: ${res.created} created, ${res.updated} updated, ${res.skipped_empty} skipped.`
      const lineErrors =
        res.errors?.length > 0
          ? ` Errors on lines: ${res.errors.map((e) => `${e.line} (${e.detail})`).join('; ')}.`
          : ''
      setMessage({
        type: res.errors?.length > 0 ? 'error' : 'success',
        text: `${baseSummary}${lineErrors}`,
      })
      fetchExperiments()
    } catch (err) {
      const fallback =
        err.status === 413
          ? 'File exceeds the 5 MB size limit.'
          : 'Failed to import settings file.'
      setMessage({
        type: 'error',
        text: typeof err.detail === 'string' ? err.detail : fallback,
      })
    } finally {
      setTransferring(false)
    }
  }

  // Export all registered experiments as Clamidomoni_settings.txt
  const handleExport = async () => {
    setTransferring(true)
    setMessage(null)
    try {
      await exportExperiments()
    } catch {
      setMessage({ type: 'error', text: 'Failed to export settings file.' })
    } finally {
      setTransferring(false)
    }
  }

  // Perform client-side validation before request dispatch
  const validateForm = () => {
    const newErrors = {}
    if (
      formData.exps === '' ||
      Number(formData.exps) < 0 ||
      !Number.isInteger(Number(formData.exps))
    ) {
      newErrors.exps = 'Enter a valid experiment number (integer >= 0)'
    }
    if (
      formData.ill === '' ||
      Number(formData.ill) < 0 ||
      !Number.isInteger(Number(formData.ill))
    ) {
      newErrors.ill = 'The illumination number must be an integer >= 0'
    }
    if (formData.intensity === '' || Number(formData.intensity) < 0) {
      newErrors.intensity = 'The intensity must be >= 0'
    }
    if (formData.pix_arr === '' || Number(formData.pix_arr) <= 0) {
      newErrors.pix_arr = 'The pixel size must be greater than 0'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Save or update experiment settings via PUT /api/experiments/{id}
  const save = async (e) => {
    e.preventDefault()
    setMessage(null)

    if (!validateForm()) return

    setLoading(true)
    const payload = {
      exps: Number(formData.exps),
      exp_type: Number(formData.exp_type),
      ill: Number(formData.ill),
      intensity: Number(formData.intensity),
      pix_arr: Number(formData.pix_arr),
      no_skip: Boolean(formData.no_skip),
      ctr: Number(formData.ctr),
      fluo: Number(formData.fluo),
      lin: Number(formData.lin),
      axis: Number(formData.axis),
    }

    try {
      await saveExperiment(payload.exps, payload)
      setMessage({
        type: 'success',
        text: `Experiment ${payload.exps} saved.`,
      })
      setSelectedExpId(payload.exps)
      setIsEditing(true)
      fetchExperiments()
    } catch (err) {
      // Map 422 validation error array to individual form fields
      if (err.status === 422 && Array.isArray(err.detail)) {
        const backendErrors = {}
        err.detail.forEach((item) => {
          const field = item.loc?.[item.loc.length - 1]
          if (field) backendErrors[field] = item.msg
        })
        setErrors(backendErrors)
        setMessage({ type: 'error', text: 'The form has validation errors.' })
      } else {
        setMessage({
          type: 'error',
          text: err.detail || err.message || 'Error while saving.',
        })
      }
    } finally {
      setLoading(false)
    }
  }

  return {
    // Constants
    EXP_TYPES,
    CTR_OPTIONS,
    FLUO_OPTIONS,
    LIN_OPTIONS,
    AXIS_OPTIONS,
    // State & Setters
    experiments,
    selectedExpId,
    formData,
    loading,
    transferring,
    errors,
    message,
    isEditing,
    // Actions
    selectExperiment,
    newExperiment,
    updateField,
    save,
    handleImport,
    handleExport,
    goBack: () => navigate('/processing'),
  }
}