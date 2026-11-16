import { useExperimentPageModel } from './ExperimentPage.model.js'
import styles from './ExperimentPage.module.css'

export function ExperimentPage() {
  const model = useExperimentPageModel()

  return (
    <div className={styles.container}>
        {/* Header and navigation */}
        <div className={styles.headerRow}>
            <div>
                <button
                    type="button"
                    onClick={model.goBack}
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
            onClick={model.newExperiment}
            className="px-4 py-2 rounded-lg text-sm font-semibold bg-alga text-white hover:bg-alga-hover transition-colors cursor-pointer"
            >
            + Nuovo esperimento
            </button>
        </div>

        {/* Feedback banner */}
        {model.message && (
            <div
            role="alert"
            className={`mb-6 p-4 rounded-lg text-sm font-medium border ${
                model.message.type === 'success'
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : 'bg-red-50 text-red-800 border-red-200'
            }`}
            >
            {model.message.text}
            </div>
        )}

        <div className={styles.grid}>
            {/* Left column: list of registered experiments */}
            <section className={styles.listCard}>
                <h2>Esperimenti registrati ({model.experiments.length})</h2>
                {model.experiments.length === 0 ? (
                    <p className="text-sm text-text-muted">Nessun esperimento registrato.</p>
                ) : (
                    <ul className={styles.expList}>
                    {model.experiments.map((exp) => (
                        <li
                        key={exp.exps}
                        onClick={() => model.selectExperiment(exp)}
                        className={`${styles.expItem} ${
                            model.selectedExpId === exp.exps ? styles.expItemActive : ''
                        }`}
                        >
                        <div>
                            <span className="font-semibold text-text">Exp {exp.exps}</span>
                            <span className="text-xs text-text-muted block">
                            Illum: {exp.ill} · {exp.intensity} µW
                            </span>
                        </div>
                        <span className="text-xs font-medium text-alga">
                            {model.selectedExpId === exp.exps ? 'In modifica' : 'Modifica →'}
                        </span>
                        </li>
                    ))}
                    </ul>
                )}
                </section>

                {/* Right column: experiment form */}
                <section className={styles.formCard}>
                <h2>
                    {model.isEditing
                    ? `Modifica Esperimento ${model.formData.exps}`
                    : 'Nuovo Esperimento'}
                </h2>
                <form onSubmit={model.save} noValidate>
                    <div className={styles.formGrid}>
                        {/* exps */}
                        <div className={styles.fieldGroup}>
                            <label htmlFor="exps">Numero esperimento (exps)</label>
                            <input
                            id="exps"
                            type="number"
                            min="0"
                            step="1"
                            disabled={model.isEditing}
                            value={model.formData.exps}
                            onChange={(e) => model.updateField('exps', e.target.value)}
                            className="px-3 py-1.5 rounded-lg border border-border bg-bg text-text text-sm focus:border-alga focus:outline-hidden disabled:opacity-60"
                            />
                            <span className={styles.fieldDesc}>
                            Identificativo univoco dell'esperimento
                            </span>
                            {model.errors.exps && (
                            <span className={styles.fieldError}>{model.errors.exps}</span>
                            )}
                        </div>

                        {/* exp_type */}
                        <div className={styles.fieldGroup}>
                            <label htmlFor="exp_type">Tipo esperimento (exp_type)</label>
                            <select
                            id="exp_type"
                            value={model.formData.exp_type}
                            onChange={(e) => model.updateField('exp_type', Number(e.target.value))}
                            className="px-3 py-1.5 rounded-lg border border-border bg-bg text-text text-sm focus:border-alga focus:outline-hidden"
                            >
                            {model.EXP_TYPES.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                {opt.label}
                                </option>
                            ))}
                            </select>
                            <span className={styles.fieldDesc}>
                            Configurazione del pattern ottico
                            </span>
                            {model.errors.exp_type && (
                            <span className={styles.fieldError}>{model.errors.exp_type}</span>
                            )}
                        </div>

                        {/* ill */}
                        <div className={styles.fieldGroup}>
                            <label htmlFor="ill">Numero illuminazione (ill)</label>
                            <input
                            id="ill"
                            type="number"
                            min="0"
                            step="1"
                            value={model.formData.ill}
                            onChange={(e) => model.updateField('ill', e.target.value)}
                            className="px-3 py-1.5 rounded-lg border border-border bg-bg text-text text-sm focus:border-alga focus:outline-hidden"
                            />
                            <span className={styles.fieldDesc}>
                            Numero dell'immagine di illuminazione (es. 14)
                            </span>
                            {model.errors.ill && (
                            <span className={styles.fieldError}>{model.errors.ill}</span>
                            )}
                        </div>

                        {/* intensity */}
                        <div className={styles.fieldGroup}>
                            <label htmlFor="intensity">Intensità (µW)</label>
                            <input
                            id="intensity"
                            type="number"
                            min="0"
                            step="any"
                            value={model.formData.intensity}
                            onChange={(e) => model.updateField('intensity', e.target.value)}
                            className="px-3 py-1.5 rounded-lg border border-border bg-bg text-text text-sm focus:border-alga focus:outline-hidden"
                            />
                            <span className={styles.fieldDesc}>Potenza della luce incidente</span>
                            {model.errors.intensity && (
                            <span className={styles.fieldError}>{model.errors.intensity}</span>
                            )}
                        </div>

                        {/* pix_arr */}
                        <div className={styles.fieldGroup}>
                            <label htmlFor="pix_arr">Dimensione pixel (pix_arr)</label>
                            <input
                            id="pix_arr"
                            type="number"
                            min="0.000001"
                            step="any"
                            value={model.formData.pix_arr}
                            onChange={(e) => model.updateField('pix_arr', e.target.value)}
                            className="px-3 py-1.5 rounded-lg border border-border bg-bg text-text text-sm focus:border-alga focus:outline-hidden"
                            />
                            <span className={styles.fieldDesc}>Scala spaziale (µm/pixel)</span>
                            {model.errors.pix_arr && (
                            <span className={styles.fieldError}>{model.errors.pix_arr}</span>
                            )}
                        </div>

                        {/* ctr */}
                        <div className={styles.fieldGroup}>
                            <label htmlFor="ctr">Centro illuminazione (ctr)</label>
                            <select
                            id="ctr"
                            value={model.formData.ctr}
                            onChange={(e) => model.updateField('ctr', Number(e.target.value))}
                            className="px-3 py-1.5 rounded-lg border border-border bg-bg text-text text-sm focus:border-alga focus:outline-hidden"
                            >
                            {model.CTR_OPTIONS.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                {opt.label}
                                </option>
                            ))}
                            </select>
                            <span className={styles.fieldDesc}>Posizione del fascio di luce</span>
                            {model.errors.ctr && (
                            <span className={styles.fieldError}>{model.errors.ctr}</span>
                            )}
                        </div>

                        {/* fluo */}
                        <div className={styles.fieldGroup}>
                            <label htmlFor="fluo">Fluorescenza (fluo)</label>
                            <select
                            id="fluo"
                            value={model.formData.fluo}
                            onChange={(e) => model.updateField('fluo', Number(e.target.value))}
                            className="px-3 py-1.5 rounded-lg border border-border bg-bg text-text text-sm focus:border-alga focus:outline-hidden"
                            >
                            {model.FLUO_OPTIONS.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                {opt.label}
                                </option>
                            ))}
                            </select>
                            <span className={styles.fieldDesc}>
                            Modalità immagine di fluorescenza
                            </span>
                            {model.errors.fluo && (
                            <span className={styles.fieldError}>{model.errors.fluo}</span>
                            )}
                        </div>

                        {/* lin */}
                        <div className={styles.fieldGroup}>
                            <label htmlFor="lin">Illuminazione lineare (lin)</label>
                            <select
                            id="lin"
                            value={model.formData.lin}
                            onChange={(e) => model.updateField('lin', Number(e.target.value))}
                            className="px-3 py-1.5 rounded-lg border border-border bg-bg text-text text-sm focus:border-alga focus:outline-hidden"
                            >
                            {model.LIN_OPTIONS.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                {opt.label}
                                </option>
                            ))}
                            </select>
                            <span className={styles.fieldDesc}>Presenza di gradiente lineare</span>
                            {model.errors.lin && (
                            <span className={styles.fieldError}>{model.errors.lin}</span>
                            )}
                        </div>

                        {/* axis */}
                        <div className={styles.fieldGroup}>
                            <label htmlFor="axis">Asse gradiente (axis)</label>
                            <select
                            id="axis"
                            value={model.formData.axis}
                            onChange={(e) => model.updateField('axis', Number(e.target.value))}
                            className="px-3 py-1.5 rounded-lg border border-border bg-bg text-text text-sm focus:border-alga focus:outline-hidden"
                            >
                            {model.AXIS_OPTIONS.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                {opt.label}
                                </option>
                            ))}
                            </select>
                            <span className={styles.fieldDesc}>
                            Direzione del gradiente lineare
                            </span>
                            {model.errors.axis && (
                            <span className={styles.fieldError}>{model.errors.axis}</span>
                            )}
                        </div>

                        {/* no_skip */}
                        <div className={styles.checkboxGroup}>
                            <input
                            id="no_skip"
                            type="checkbox"
                            checked={model.formData.no_skip}
                            onChange={(e) => model.updateField('no_skip', e.target.checked)}
                            className="h-4 w-4 rounded-sm border-border text-alga focus:ring-alga cursor-pointer"
                            />
                            <label htmlFor="no_skip">Includi nell'analisi (no_skip)</label>
                        </div>

                        {/* Action buttons */}
                        <div className={styles.actions}>
                            <button
                            type="button"
                            onClick={model.newExperiment}
                            className="px-4 py-2 rounded-lg text-sm font-semibold border border-border bg-bg text-text hover:bg-surface transition-colors cursor-pointer"
                            >
                            Annulla
                            </button>
                            <button
                            type="submit"
                            disabled={model.loading}
                            className="px-5 py-2 rounded-lg text-sm font-semibold bg-alga text-white hover:bg-alga-hover disabled:opacity-50 transition-colors cursor-pointer"
                            >
                            {model.loading ? 'Salvataggio...' : 'Salva impostazioni'}
                            </button>
                        </div>
                    </div>
                </form>
            </section>
        </div>
    </div>
  )
}