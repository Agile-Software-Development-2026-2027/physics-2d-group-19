import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  getPlotImageUrl,
  getPlotsList,
  getElaborationResults,
  downloadElaborationResultCsv,
  getJobConfig,
} from '../../api/client/client.js'
import { GifViewer } from '../../components/GifViewer/GifViewer.jsx'
import styles from './ResultsPage.module.css'

const TITLES = {
  theta_distribution: 'θ distribution',
  flux: 'Flux',
  density_vs_distance: 'Density vs distance',
  angle_distribution: 'Angle distribution',
  omega_distribution: 'ω distribution',
  nt_stats: 'N(t)',
  tumbling_vs_gradient: 'Tumbling vs gradient',
  tumbling_duration_vs_distance:
    'Tumbling duration vs distance',
}

const PARAM_GROUPS = [
  ['tracking', 'Tracking'],
  ['analysis', 'Analysis'],
  ['filters', 'Filters'],
]

// true/false/null are not readable as they are
function formatValue(value) {
  if (value === true) return 'yes'
  if (value === false) return 'no'
  if (value === null || value === undefined) return '—'
  return String(value)
}

export function ResultsPage() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const [plots, setPlots] = useState([])
  const [images, setImages] = useState({})
  const [message, setMessage] = useState(null)
  const [results, setResults] = useState([])
  const [config, setConfig] = useState(null)
  const [configError, setConfigError] = useState(false)

  // The job is already finished when we get here: no polling, one load.
  useEffect(() => {
    let active = true
    const created = []

    getPlotsList(jobId)
      .then((items) => {
        if (!active) return
        setPlots(items)
        items
          .filter((item) => item.url)
          .forEach((item) => {
            getPlotImageUrl(jobId, item.name)
              .then((src) => {
                if (!active) {
                  URL.revokeObjectURL(src)
                  return
                }
                created.push(src)
                setImages((prev) => ({ ...prev, [item.name]: src }))
              })
              .catch(() => {})
          })
      })
      .catch((err) => {
        if (!active) return
        setMessage(
          err.status === 409
            ? 'The processing has not finished yet.'
            : 'Could not load the plots.',
        )
      })

    getElaborationResults(jobId)
      .then((items) => {
        if (!active) return
        setResults(items)
      })
      .catch((err) => {
        if (!active) return
        setMessage(
          err.status === 409
            ? 'The processing has not finished yet.'
            : 'Could not load the CSV files.',
        )
      })

    // Jobs created before 23.1 have no config (404): only this box says so,
    // plots and CSVs still work.
    getJobConfig(jobId)
      .then((data) => {
        if (!active) return
        setConfig(data)
      })
      .catch(() => {
        if (!active) return
        setConfigError(true)
      })

    return () => {
      active = false
      created.forEach((src) => URL.revokeObjectURL(src))
    }
  }, [jobId])

  return (
    <main className={styles.resultsPage}>
      <h1>Processing results</h1>
      <section className={styles.configBox}>
        <h2>Processing</h2>
        {config ? (
          <>
            <p className={styles.configSummary}>
              Experiment <strong>{config.experiment.exps}</strong>
              {' · '}
              {new Date(config.created_at).toLocaleString('en-GB')}
              {config.inputs.video && ` · video: ${config.inputs.video}`}
            </p>
            <div className={styles.configGroups}>
              {PARAM_GROUPS.map(([group, label]) => (
                <div key={group}>
                  <h3>{label}</h3>
                  <dl>
                    {Object.entries(config.params[group]).map(
                      ([name, value]) => (
                        <div key={name} className={styles.configRow}>
                          <dt>{name}</dt>
                          <dd>{formatValue(value)}</dd>
                        </div>
                      ),
                    )}
                  </dl>
                </div>
              ))}
            </div>
          </>
        ) : (
          <p className={styles.configMissing}>
            {configError ? 'Parameters not available.' : 'Loading…'}
          </p>
        )}
      </section>

      {message && (
        <p role="alert" className={styles.resultsMessage}>
          {message}
        </p>
      )}
      <div className={styles.plotGrid}>
        {plots.map((plot) => {
          const title = TITLES[plot.name] ?? plot.name
          const src = images[plot.name]
          return (
            <figure key={plot.name} className={styles.plotCard}>
              <figcaption>{title}</figcaption>
              {src ? (
                <>
                  <img src={src} alt={title} />
                  <a href={src} download={`${plot.name}.png`}>
                    Download
                  </a>
                </>
              ) : (
                <p className={styles.plotMissing}>
                  {plot.url ? 'Loading…' : 'Plot not available'}
                </p>
              )}
            </figure>
          )
        })}
      </div>
      {results.length > 0 && (
        <section className={styles.resultsSection}>
          <h2>Data (CSV)</h2>
          <div className={styles.resultGrid}>
            {results.map((result) => (
              <button
                key={result.name}
                type="button"
                onClick={() => downloadElaborationResultCsv(jobId, result.name)}
                className="px-3.5 py-1.5 rounded-lg text-xs font-semibold border border-border bg-bg text-text hover:bg-alga-light hover:text-alga hover:border-alga/40 transition-colors cursor-pointer"
              >
                ⬇ {result.name}.csv
              </button>
            ))}
          </div>
        </section>
      )}

      <GifViewer jobId={jobId} />

      <button
        type="button"
        onClick={() => navigate('/processing')}
        className={`${styles.newJob} px-4 py-2 rounded-lg text-sm font-semibold bg-alga text-white hover:bg-alga-hover transition-colors cursor-pointer`}
      >
        New processing
      </button>
    </main>
  )
}
