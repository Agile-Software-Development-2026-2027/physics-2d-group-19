export function ParametersSection({
  title,
  fields,
  values,
  onChange,
  defaultOpen = false,
}) {
  function handleStep(key, delta, min = 0) {
    onChange((prev) => {
      const current = Number(prev[key]) || 0
      const next = Number((current + delta).toFixed(4))
      return {
        ...prev,
        [key]: Math.max(min, next),
      }
    })
  }

  function handleDirectChange(key, newValue) {
    onChange((prev) => ({
      ...prev,
      [key]: newValue,
    }))
  }

  return (
    <details open={defaultOpen} className="group border border-border rounded-xl bg-surface p-4">
      <summary className="flex items-center justify-between font-semibold text-text cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden">
        <span>{title}</span>
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
        {fields.map((field) => {
          const step = field.step ?? 1
          const min = field.min ?? 0

          if (field.type === 'boolean') {
            return (
              <label
                key={field.id}
                className="flex items-center justify-between p-2.5 rounded-xl border border-border bg-bg cursor-pointer select-none"
              >
                <span className="text-xs font-semibold text-text">{field.label}</span>

                {/* Contenitore dello switch */}
                <div className="relative inline-flex items-center">
                  <input
                    type="checkbox"
                    checked={Boolean(values[field.id])}
                    onChange={(e) => handleDirectChange(field.id, e.target.checked)}
                    className="sr-only peer"
                  />
                  {/* Sfondo (track) + pallino (after:) */}
                  <div className="w-11 h-6 bg-slate-200 dark:bg-slate-700 rounded-full peer peer-checked:bg-alga transition-colors duration-200 after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:border after:border-slate-300 after:rounded-full after:h-5 after:w-5 after:transition-transform after:duration-200 peer-checked:after:translate-x-5" />
                </div>
              </label>
            )
          }

                return (
                <div
                  key={field.id}
                  className="flex items-center justify-between p-2.5 rounded-xl border border-border bg-bg"
                >
                  <span className="text-xs font-semibold text-text">{field.label}</span>

                  <div className="flex items-center gap-1 bg-surface border border-border rounded-lg p-0.5">
                    <button
                      type="button"
                      onClick={() => handleStep(field.id, -step, min)}
                      className="w-7 h-7 flex items-center justify-center rounded-md bg-bg hover:bg-border text-text font-bold text-sm transition-colors cursor-pointer select-none active:scale-95"
                    >
                      -
                    </button>

                    <input
                      type="number"
                      step={step}
                      min={min}
                      value={values[field.id]}
                      onChange={(e) =>
                        handleDirectChange(field.id, e.target.value === '' ? 0 : Number(e.target.value))
                      }
                      className="w-12 text-center text-xs font-semibold text-text bg-transparent focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    />

                    <button
                      type="button"
                      onClick={() => handleStep(field.id, step, min)}
                      className="w-7 h-7 flex items-center justify-center rounded-md bg-bg hover:bg-border text-text font-bold text-sm transition-colors cursor-pointer select-none active:scale-95"
                    >
                      +
                    </button>
                  </div>
                </div>
                )
                })}
              </div>
          </details>
          )
          }
