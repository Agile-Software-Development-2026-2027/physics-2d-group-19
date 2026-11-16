import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getExperiments, saveExperiment } from '../../api/client/client.js'
import styles from './ExperimentPage.module.css'

// Default values populated when creating a new experiment
const DEFAULT_EXPERIMENT = {
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

// Dropdown options matching backend ExperimentSettings field descriptions
const EXP_TYPES = [
  { value: 0, label: '0 = none' },
  { value: 1, label: '1 = normal' },
  { value: 2, label: '2 = gaussian' },
  { value: 3, label: '3 = outside' },
  { value: 4, label: '4 = single cell' },
  { value: 5, label: '5 = LED' },
]

const CTR_OPTIONS = [
  { value: -1, label: '-1 = left' },
  { value: 0, label: '0 = centre' },
  { value: 1, label: '1 = right' },
]

const FLUO_OPTIONS = [
  { value: 0, label: '0 = none' },
  { value: 1, label: '1 = ring' },
  { value: 2, label: '2 = gaussian' },
]

const LIN_OPTIONS = [
  { value: 0, label: '0 = no' },
  { value: 1, label: '1 = yes' },
]

const AXIS_OPTIONS = [
  { value: 0, label: '0 = x' },
  { value: 1, label: '1 = y' },
]

export function ExperimentPage() {
  const [experiments, setExperiments] = useState([])
  const [selectedExpId, setSelectedExpId] = useState(null)
  const [formData, setFormData] = useState(DEFAULT_EXPERIMENT)
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState(null)
  const [isEditing, setIsEditing] = useState(false)

  const navigate = useNavigate()

  // Fetch list of registered experiments on mount
  const fetchExperiments = () => {
    getExperiments()
      .then((data) => setExperiments(data || []))
      .catch(() => setMessage({ type: 'error', text: 'Impossibile caricare gli esperimenti.' }))
  }

  useEffect(() => {
    fetchExperiments()
  }, [])

  // Select an existing experiment to view or edit
  const handleSelectExperiment = (exp) => {
    setSelectedExpId(exp.exps)
    setFormData({ ...exp })
    setIsEditing(true)
    setErrors({})
    setMessage(null)
  }

  // Reset form to default values for creating a new experiment
  const handleNewExperiment = () => {
    setSelectedExpId(null)
    setFormData(DEFAULT_EXPERIMENT)
    setIsEditing(false)
    setErrors({})
    setMessage(null)
  }

  // Handle input change and clear inline error for that field
  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors((prev) => {
        const updated = { ...prev }
        delete updated[field]
        return updated
      })
    }
  }

  // Client-side validation before sending the request
  const validateForm = () => {
    const newErrors = {}
    if (formData.exps === '' || Number(formData.exps) < 0 || !Number.isInteger(Number(formData.exps))) {
      newErrors.exps = "Inserire un numero d'esperimento valido (intero >= 0)"
    }
    if (formData.ill === '' || Number(formData.ill) < 0 || !Number.isInteger(Number(formData.ill))) {
      newErrors.ill = "Il numero d'illuminazione deve essere un intero >= 0"
    }
    if (formData.intensity === '' || Number(formData.intensity) < 0) {
      newErrors.intensity = "L'intensità deve essere >= 0"
    }
    if (formData.pix_arr === '' || Number(formData.pix_arr) <= 0) {
      newErrors.pix_arr = 'La dimensione del pixel deve essere maggiore di 0'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Submit experiment data to the backend via PUT /api/experiments/{id}
  const handleSubmit = async (e) => {
    e.preventDefault()
    setMessage(null)

    if (!validateForm()) {
      return
    }

    setLoading(true)

    // Convert inputs into expected types
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
      setMessage({ type: 'success', text: `Esperimento ${payload.exps} salvato con successo!` })
      setSelectedExpId(payload.exps)
      setIsEditing(true)
      fetchExperiments()
    } catch (err) {
      // Map backend 422 validation errors to corresponding fields
      if (err.status === 422 && Array.isArray(err.detail)) {
        const backendErrors = {}
        err.detail.forEach((item) => {
          const field = item.loc?.[item.loc.length - 1]
          if (field) {
            backendErrors[field] = item.msg
          }
        })
        setErrors(backendErrors)
        setMessage({ type: 'error', text: 'Errori di validazione nel form.' })
      } else {
        setMessage({ type: 'error', text: err.detail || err.message || 'Errore durante il salvataggio.' })
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      {/* Header and navigation */}
        <div className={styles.headerRow}>
            <div>
            <button
                type="button"
                onClick={() => navigate('/processing')}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-text-muted hover:text-alga mb-2 transition-colors cursor-pointer"
            >
                ← Torna a Elaborazione
            </button>
            <h1 className="text-2xl font-bold text-text">Gestione esperimenti</h1>
            <p className="text-sm text-text-muted">
                Registra un nuovo esperimento o modifica le impostazioni di uno esistente.
            </p>
            </div>
            <button
            type="button"
            onClick={handleNewExperiment}
            className="px-4 py-2 rounded-lg text-sm font-semibold bg-alga text-white hover:bg-alga-hover transition-colors cursor-pointer"
            >
            + Nuovo esperimento
            </button>
        </div>

        {/* Feedback banner */}
        {message && (
            <div
            role="alert"
            className={`mb-6 p-4 rounded-lg text-sm font-medium border ${
                message.type === 'success'
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : 'bg-red-50 text-red-800 border-red-200'
            }`}
            >
            {message.text}
            </div>
        )}

        <div className={styles.grid}>
            {/* Left column: list of registered experiments */}
            <section className={styles.listCard}>
            <h2>Esperimenti registrati ({experiments.length})</h2>
            {experiments.length === 0 ? (
                <p className="text-sm text-text-muted">Nessun esperimento registrato.</p>
            ) : (
                <ul className={styles.expList}>
                {experiments.map((exp) => (
                    <li
                    key={exp.exps}
                    onClick={() => handleSelectExperiment(exp)}
                    className={`${styles.expItem} ${selectedExpId === exp.exps ? styles.expItemActive : ''}`}
                    >
                    <div>
                        <span className="font-semibold text-text">Exp {exp.exps}</span>
                        <span className="text-xs text-text-muted block">
                        Illum: {exp.ill} · {exp.intensity} µW
                        </span>
                    </div>
                    <span className="text-xs font-medium text-alga">
                        {selectedExpId === exp.exps ? 'In modifica' : 'Modifica →'}
                    </span>
                    </li>
                ))}
                </ul>
            )}
            </section>

            {/* Right column: experiment settings form */}
            <section className={styles.formCard}>
                <h2>{isEditing ? `Modifica Esperimento ${formData.exps}` : 'Nuovo Esperimento'}</h2>
                <form onSubmit={handleSubmit} noValidate>
                    <div className={styles.formGrid}>
                        {/* exps */}
                        <div className={styles.fieldGroup}>
                            <label htmlFor="exps">Numero esperimento (exps)</label>
                            <input
                            id="exps"
                            type="number"
                            min="0"
                            step="1"
                            disabled={isEditing}
                            value={formData.exps}
                            onChange={(e) => handleChange('exps', e.target.value)}
                            className="px-3 py-1.5 rounded-lg border border-border bg-bg text-text text-sm focus:border-alga focus:outline-hidden disabled:opacity-60"
                            />
                            <span className={styles.fieldDesc}>Identificativo univoco dell'esperimento</span>
                            {errors.exps && <span className={styles.fieldError}>{errors.exps}</span>}
                        </div>

                        {/* exp_type */}
                        <div className={styles.fieldGroup}>
                            <label htmlFor="exp_type">Tipo esperimento (exp_type)</label>
                            <select
                            id="exp_type"
                            value={formData.exp_type}
                            onChange={(e) => handleChange('exp_type', Number(e.target.value))}
                            className="px-3 py-1.5 rounded-lg border border-border bg-bg text-text text-sm focus:border-alga focus:outline-hidden"
                            >
                            {EXP_TYPES.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                {opt.label}
                                </option>
                            ))}
                            </select>
                            <span className={styles.fieldDesc}>Configurazione del pattern ottico</span>
                            {errors.exp_type && <span className={styles.fieldError}>{errors.exp_type}</span>}
                        </div>

                        {/* ill */}
                        <div className={styles.fieldGroup}>
                            <label htmlFor="ill">Numero illuminazione (ill)</label>
                            <input
                            id="ill"
                            type="number"
                            min="0"
                            step="1"
                            value={formData.ill}
                            onChange={(e) => handleChange('ill', e.target.value)}
                            className="px-3 py-1.5 rounded-lg border border-border bg-bg text-text text-sm focus:border-alga focus:outline-hidden"
                            />
                            <span className={styles.fieldDesc}>Numero dell'immagine di illuminazione (es. 14)</span>
                            {errors.ill && <span className={styles.fieldError}>{errors.ill}</span>}
                        </div>

                        {/* intensity */}
                        <div className={styles.fieldGroup}>
                            <label htmlFor="intensity">Intensità (µW)</label>
                            <input
                            id="intensity"
                            type="number"
                            min="0"
                            step="any"
                            value={formData.intensity}
                            onChange={(e) => handleChange('intensity', e.target.value)}
                            className="px-3 py-1.5 rounded-lg border border-border bg-bg text-text text-sm focus:border-alga focus:outline-hidden"
                            />
                            <span className={styles.fieldDesc}>Potenza della luce incidente</span>
                            {errors.intensity && <span className={styles.fieldError}>{errors.intensity}</span>}
                        </div>

                        {/* pix_arr */}
                        <div className={styles.fieldGroup}>
                            <label htmlFor="pix_arr">Dimensione pixel (pix_arr)</label>
                            <input
                            id="pix_arr"
                            type="number"
                            min="0.000001"
                            step="any"
                            value={formData.pix_arr}
                            onChange={(e) => handleChange('pix_arr', e.target.value)}
                            className="px-3 py-1.5 rounded-lg border border-border bg-bg text-text text-sm focus:border-alga focus:outline-hidden"
                            />
                            <span className={styles.fieldDesc}>Scala spaziale (µm/pixel)</span>
                            {errors.pix_arr && <span className={styles.fieldError}>{errors.pix_arr}</span>}
                        </div>

                        {/* ctr */}
                        <div className={styles.fieldGroup}>
                            <label htmlFor="ctr">Centro illuminazione (ctr)</label>
                            <select
                            id="ctr"
                            value={formData.ctr}
                            onChange={(e) => handleChange('ctr', Number(e.target.value))}
                            className="px-3 py-1.5 rounded-lg border border-border bg-bg text-text text-sm focus:border-alga focus:outline-hidden"
                            >
                            {CTR_OPTIONS.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                {opt.label}
                                </option>
                            ))}
                            </select>
                            <span className={styles.fieldDesc}>Posizione del fascio di luce</span>
                            {errors.ctr && <span className={styles.fieldError}>{errors.ctr}</span>}
                        </div>

                        {/* fluo */}
                        <div className={styles.fieldGroup}>
                            <label htmlFor="fluo">Fluorescenza (fluo)</label>
                            <select
                            id="fluo"
                            value={formData.fluo}
                            onChange={(e) => handleChange('fluo', Number(e.target.value))}
                            className="px-3 py-1.5 rounded-lg border border-border bg-bg text-text text-sm focus:border-alga focus:outline-hidden"
                            >
                            {FLUO_OPTIONS.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                {opt.label}
                                </option>
                            ))}
                            </select>
                            <span className={styles.fieldDesc}>Modalità immagine di fluorescenza</span>
                            {errors.fluo && <span className={styles.fieldError}>{errors.fluo}</span>}
                        </div>

                        {/* lin */}
                        <div className={styles.fieldGroup}>
                            <label htmlFor="lin">Illuminazione lineare (lin)</label>
                            <select
                            id="lin"
                            value={formData.lin}
                            onChange={(e) => handleChange('lin', Number(e.target.value))}
                            className="px-3 py-1.5 rounded-lg border border-border bg-bg text-text text-sm focus:border-alga focus:outline-hidden"
                            >
                            {LIN_OPTIONS.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                {opt.label}
                                </option>
                            ))}
                            </select>
                            <span className={styles.fieldDesc}>Presenza di gradiente lineare</span>
                            {errors.lin && <span className={styles.fieldError}>{errors.lin}</span>}
                        </div>

                        {/* axis */}
                        <div className={styles.fieldGroup}>
                            <label htmlFor="axis">Asse gradiente (axis)</label>
                            <select
                            id="axis"
                            value={formData.axis}
                            onChange={(e) => handleChange('axis', Number(e.target.value))}
                            className="px-3 py-1.5 rounded-lg border border-border bg-bg text-text text-sm focus:border-alga focus:outline-hidden"
                            >
                            {AXIS_OPTIONS.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                {opt.label}
                                </option>
                            ))}
                            </select>
                            <span className={styles.fieldDesc}>Direzione del gradiente lineare</span>
                            {errors.axis && <span className={styles.fieldError}>{errors.axis}</span>}
                        </div>

                        {/* no_skip */}
                        <div className={styles.checkboxGroup}>
                            <input
                            id="no_skip"
                            type="checkbox"
                            checked={formData.no_skip}
                            onChange={(e) => handleChange('no_skip', e.target.checked)}
                            className="h-4 w-4 rounded-sm border-border text-alga focus:ring-alga cursor-pointer"
                            />
                            <label htmlFor="no_skip">Includi nell'analisi (no_skip)</label>
                        </div>

                        {/* Action buttons */}
                        <div className={styles.actions}>
                            <button
                            type="button"
                            onClick={handleNewExperiment}
                            className="px-4 py-2 rounded-lg text-sm font-semibold border border-border bg-bg text-text hover:bg-surface transition-colors cursor-pointer"
                            >
                            Annulla
                            </button>
                            <button
                            type="submit"
                            disabled={loading}
                            className="px-5 py-2 rounded-lg text-sm font-semibold bg-alga text-white hover:bg-alga-hover disabled:opacity-50 transition-colors cursor-pointer"
                            >
                            {loading ? 'Salvataggio...' : 'Salva impostazioni'}
                            </button>
                        </div>
                    </div>
                </form>
            </section>
        </div>
    </div>
  )
}