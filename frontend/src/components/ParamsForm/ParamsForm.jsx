import { useEffect, useRef, useState } from 'react'
import { getDefaultParams } from '../../api/client/client.js'

// Section titles displayed in the UI for each parameter group
const GROUP_TITLES = {
  tracking: 'Tracking',
  analysis: 'Analisi',
  filters: 'Filtri',
}

// Physical units appended to field labels where applicable
const FIELD_UNITS = {
  diameter: 'px',
  search_range: 'px',
  adaptive_stop: 'px',
  diam: 'µm',
  dt: 's',
  disc_radius: 'µm',
  tumbling_threshold: '°/s',
  lifetime_min: 's',
  threshold_dist: 'µm',
  threshold_dist_tot: 'µm',
}

// Fields that require integer values rather than floating-point numbers
const INTEGER_FIELDS = new Set([
  'channel',
  'diameter',
  'minmass',
  'search_range',
  'adaptive_stop',
  'memory',
  'filter_stubs',
  'particle_show',
  'flux_cg_in',
  'flux_cg_out',
  'nskip',
  'dist_step',
  'long_track_min_snaps',
])

// Format field name with its measurement unit if defined
function formatFieldLabel(field) {
  const unit = FIELD_UNITS[field]
  return unit ? `${field} (${unit})` : field
}

// Compute HTML native min, max, and step attributes from backend schema limits
function getInputBounds(field, fieldLimit = {}) {
  const isInt = INTEGER_FIELDS.has(field)
  const step = isInt ? 1 : 'any'

  let min = fieldLimit.minimum
  if (min === undefined && fieldLimit.exclusiveMinimum !== undefined) {
    min = isInt ? fieldLimit.exclusiveMinimum + 1 : fieldLimit.exclusiveMinimum
  }

  let max = fieldLimit.maximum
  if (max === undefined && fieldLimit.exclusiveMaximum !== undefined) {
    max = isInt ? fieldLimit.exclusiveMaximum - 1 : fieldLimit.exclusiveMaximum
  }

  return { min, max, step }
}

// Validate a single field against backend constraints and domain rules
function validateField(group, name, value, fieldLimit = {}) {
    if (typeof value === 'boolean' || fieldLimit.enum) {
        return null
    }

    // Optional field memory: null or empty string means auto (nFrames - 1)
    if (name === 'memory' && (value === null || value === '')) {
        return null
    }

    if (value === '' || value === null || Number.isNaN(Number(value))) {
        return 'Inserisci un valore numerico valido'
    }

    const num = Number(value)

    if (INTEGER_FIELDS.has(name) && !Number.isInteger(num)) {
        return 'Deve essere un numero intero'
    }

    if (fieldLimit.minimum !== undefined && num < fieldLimit.minimum) {
        return `Il valore deve essere almeno ${fieldLimit.minimum}`
    }

    if (fieldLimit.exclusiveMinimum !== undefined && num <= fieldLimit.exclusiveMinimum) {
        return `Il valore deve essere maggiore di ${fieldLimit.exclusiveMinimum}`
    }

    if (fieldLimit.maximum !== undefined && num > fieldLimit.maximum) {
        return `Il valore deve essere al massimo ${fieldLimit.maximum}`
    }

    if (fieldLimit.exclusiveMaximum !== undefined && num >= fieldLimit.exclusiveMaximum) {
        return `Il valore deve essere minore di ${fieldLimit.exclusiveMaximum}`
    }

    if (group === 'tracking' && name === 'diameter' && num % 2 === 0) {
        return 'Il diametro deve essere un numero dispari (es. 3, 5, 7)'
    }

    return null
}

// Validate all parameter groups and return a map of error messages keyed by "group.field"
function validateAll(params, limits) {
    const errors = {}
    for (const group of ['tracking', 'analysis', 'filters']) {
        if (!params[group]) continue
        for (const [field, val] of Object.entries(params[group])) {
            const err = validateField(group, field, val, limits?.[group]?.[field])
            if (err) {
                errors[`${group}.${field}`] = err
            }
        }
    }
    return errors
}

// Create a shallow copy of the three parameter groups to avoid mutating defaults
function cloneParams(data) {
    return {
        tracking: { ...data.tracking },
        analysis: { ...data.analysis },
        filters: { ...data.filters },
    }
}

export function ParamsForm({ onChange, disabled = false }) {
    const [defaults, setDefaults] = useState(null)
    const [limits, setLimits] = useState({})
    const [values, setValues] = useState(null)
    const [errors, setErrors] = useState({})
    const [loading, setLoading] = useState(true)
    const [fetchError, setFetchError] = useState(null)

    // Keep latest onChange callback in a ref to avoid re-triggering the mount effect
    const onChangeRef = useRef(onChange)
    useEffect(() => {
        onChangeRef.current = onChange
    }, [onChange])

    // Fetch default laboratory parameters and schema limits on component mount
    useEffect(() => {
        let active = true
        async function loadDefaults() {
            try {
                setLoading(true)
                const data = await getDefaultParams()
                if (!active) return
                const initial = cloneParams(data)
                setDefaults(initial)
                setLimits(data.limits ?? {})
                setValues(initial)
                setErrors({})
                onChangeRef.current?.(initial, true)
            } catch {
                if (!active) return
                setFetchError('Impossibile caricare i parametri di default dal server.')
            } finally {
                if (active) setLoading(false)
            }
        }
        loadDefaults()
        return () => {
            active = false
        }
    }, [])

    // Parse user input, update local state, run live validation, and notify parent
    function handleFieldChange(group, field, rawValue, fieldType) {
        let parsedValue = rawValue

        if (fieldType === 'boolean') {
            parsedValue = Boolean(rawValue)
        } else if (fieldType === 'number') {
            if (rawValue === '') {
                parsedValue = field === 'memory' ? null : ''
            } else {
                parsedValue = Number(rawValue)
            }
        }

        const updated = {
            ...values,
            [group]: {
                ...values[group],
                [field]: parsedValue,
            },
        }

        setValues(updated)
        const nextErrors = validateAll(updated, limits)
        setErrors(nextErrors)
        const isValid = Object.keys(nextErrors).length === 0
        onChange?.(updated, isValid)
    }

    // Restore all parameters back to the laboratory default values
    function handleReset() {
        if (!defaults) return
        const resetValues = cloneParams(defaults)
        setValues(resetValues)
        setErrors({})
        onChange?.(resetValues, true)
    }

    if (loading) {
        return (
        <div className="p-4 rounded-xl border border-border bg-bg/50 text-sm text-text-muted animate-pulse">
            Caricamento parametri...
        </div>
        )
    }

    if (fetchError) {
        return (
        <p
            role="alert"
            className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 text-sm font-medium"
        >
            {fetchError}
        </p>
        )
    }

    if (!values) return null

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between gap-4">
                <p className="text-xs text-text-muted">
                    Parametri dell'esperimento.
                </p>
                <button
                type="button"
                onClick={handleReset}
                disabled={disabled}
                className="shrink-0 px-3.5 py-1.5 rounded-lg text-xs font-semibold border border-border bg-bg text-text hover:bg-alga-light hover:text-alga hover:border-alga/40 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Ripristina default
                </button>
            </div>

            {(['tracking', 'analysis', 'filters']).map((group) => (
                <details
                key={group}
                className="group border border-border rounded-xl bg-bg/40 p-4"
                >
                    <summary className="flex items-center justify-between font-semibold text-sm text-text cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden">
                        <span>{GROUP_TITLES[group]}</span>
                        <span className="text-xs text-text-muted group-open:rotate-180 transition-transform">
                        ▼
                        </span>
                    </summary>

                    <div className="mt-4 pt-4 border-t border-border grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {Object.entries(values[group]).map(([field, val]) => {
                            const limit = limits?.[group]?.[field] ?? {}
                            const errorMsg = errors[`${group}.${field}`]
                            const inputId = `param-${group}-${field}`
                            const label = formatFieldLabel(field)

                            if (typeof defaults[group][field] === 'boolean') {
                                return (
                                    <div
                                    key={field}
                                    className="flex flex-col justify-center gap-1.5 p-3 rounded-xl border border-border bg-surface"
                                    >
                                        <label
                                            htmlFor={inputId}
                                            className="flex items-center gap-2.5 text-sm font-semibold text-text cursor-pointer"
                                        >
                                            <input
                                            id={inputId}
                                            type="checkbox"
                                            checked={Boolean(val)}
                                            disabled={disabled}
                                            onChange={(e) => handleFieldChange(group, field, e.target.checked, 'boolean')}
                                            className="w-4 h-4 rounded text-alga border-border focus:ring-alga cursor-pointer shrink-0"
                                            />
                                            <span>{label}</span>
                                        </label>
                                        {limit.description && (
                                            <span className="text-xs text-text-muted">{limit.description}</span>
                                        )}
                                    </div>
                                )
                            }

                            if (limit.enum) {
                                return (
                                <div
                                    key={field}
                                    className="flex flex-col gap-1 p-3 rounded-xl border border-border bg-surface"
                                >
                                    <label htmlFor={inputId} className="text-xs font-semibold text-text">
                                        {label}
                                    </label>
                                    <select
                                    id={inputId}
                                    value={val}
                                    disabled={disabled}
                                    onChange={(e) => handleFieldChange(group, field, e.target.value, 'enum')}
                                    className="w-full px-3 py-2 rounded-lg border border-border bg-bg text-sm text-text focus:outline-none focus:ring-2 focus:ring-alga/50"
                                    >
                                        {limit.enum.map((opt) => (
                                            <option key={opt} value={opt}>
                                            {opt}
                                            </option>
                                        ))}
                                    </select>
                                    {limit.description && (
                                    <span className="text-xs text-text-muted">{limit.description}</span>
                                    )}
                                </div>
                                )
                            } 

                            const { min, max, step } = getInputBounds(field, limit)

                            return (
                            <div
                                key={field}
                                className={`flex flex-col gap-1 p-3 rounded-xl border bg-surface transition-colors ${
                                errorMsg ? 'border-red-500/70' : 'border-border'
                                }`}
                            >
                                <label htmlFor={inputId} className="text-xs font-semibold text-text">
                                    {label}
                                </label>
                                <input
                                id={inputId}
                                type="number"
                                min={min}
                                max={max}
                                step={group === 'tracking' && field === 'diameter' ? 2 : step}
                                value={val === null ? '' : val}
                                placeholder={field === 'memory' ? 'Auto' : undefined}
                                disabled={disabled}
                                aria-invalid={Boolean(errorMsg)}
                                onChange={(e) => handleFieldChange(group, field, e.target.value, 'number')}
                                className={`w-full px-3 py-2 rounded-lg border bg-bg text-sm text-text focus:outline-none focus:ring-2 ${
                                    errorMsg
                                    ? 'border-red-500 focus:ring-red-500/40'
                                    : 'border-border focus:ring-alga/50 focus:border-alga'
                                }`}
                                />
                                {errorMsg && (
                                <p role="alert" className="text-xs font-medium text-red-600 dark:text-red-400">
                                    {errorMsg}
                                </p>
                                )}
                                {limit.description && (
                                <span className="text-xs text-text-muted">{limit.description}</span>
                                )}
                            </div>
                            )
                        })}
                    </div>
                </details>
            ))}
        </div>
    )
}