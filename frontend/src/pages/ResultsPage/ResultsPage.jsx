import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getPlotImageUrl, getPlotsList } from '../../api/client.js'
import './ResultsPage.module.css'

const TITLES = {
  theta_distribution: 'Distribuzione di θ',
  flux: 'Flusso',
  density_vs_distance: 'Densità in funzione della distanza',
  angle_distribution: "Distribuzione dell'angolo",
  omega_distribution: 'Distribuzione di ω',
  nt_stats: 'N(t)',
  tumbling_vs_gradient: 'Tumbling rispetto al gradiente',
  tumbling_duration_vs_distance:
    'Durata del tumbling in funzione della distanza',
}

export function ResultsPage() {
  const { jobId } = useParams()
  const [plots, setPlots] = useState([])
  const [images, setImages] = useState({})
  const [message, setMessage] = useState(null)

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
            ? "L'elaborazione non è ancora finita."
            : 'Impossibile caricare i grafici.',
        )
      })

    return () => {
      active = false
      created.forEach((src) => URL.revokeObjectURL(src))
    }
  }, [jobId])

  return (
    <main className="results-page">
      <h1>Risultati dell'elaborazione</h1>
      {message && (
        <p role="alert" className="results-message">
          {message}
        </p>
      )}
      <div className="plot-grid">
        {plots.map((plot) => {
          const title = TITLES[plot.name] ?? plot.name
          const src = images[plot.name]
          return (
            <figure key={plot.name} className="plot-card">
              <figcaption>{title}</figcaption>
              {src ? (
                <>
                  <img src={src} alt={title} />
                  <a href={src} download={`${plot.name}.png`}>
                    Scarica
                  </a>
                </>
              ) : (
                <p className="plot-missing">
                  {plot.url ? 'Caricamento…' : 'Grafico non disponibile'}
                </p>
              )}
            </figure>
          )
        })}
      </div>
    </main>
  )
}
