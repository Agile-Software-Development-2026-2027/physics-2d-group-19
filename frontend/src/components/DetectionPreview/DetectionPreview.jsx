import { useEffect, useState } from 'react'
import { getVideoPreview } from '../../api/client/client.js'

// Wait this long after the last change before asking the backend.
const DEBOUNCE_MS = 400

export function DetectionPreview({ videoId, frames, tracking, paramsValid = true }) {
  const [frame, setFrame] = useState(0)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const diameter = tracking?.diameter
  const minmass = tracking?.minmass
  const backgroundMethod = tracking?.background_method

  useEffect(() => {
    if (!videoId || !paramsValid) return

    // Set to false when a newer change arrives: an old answer must not overwrite a newer one.
    let active = true
    const timer = setTimeout(async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await getVideoPreview(videoId, {
          frame,
          diameter,
          minmass,
          background_method: backgroundMethod,
        })
        if (active) setPreview(data)
      } catch {
        if (active) setError("Impossibile calcolare l'anteprima.")
      } finally {
        if (active) setLoading(false)
      }
    }, DEBOUNCE_MS)

    // Runs before the next change: cancels the request that has not started yet.
    return () => {
      active = false
      clearTimeout(timer)
    }
  }, [videoId, frame, diameter, minmass, backgroundMethod, paramsValid])

  if (!videoId) {
    return <p className="text-sm text-text-muted">Carica un video per vedere l&apos;anteprima.</p>
  }

    return (
    <div className="space-y-3">
      <div className="max-w-xl mx-auto space-y-3">
        {preview && (
          <figure className="space-y-2">
            <img
              src={preview.image}
              alt={`Cellule rilevate nel frame ${preview.frame}`}
              className="w-full rounded-xl border border-border"
            />
            <figcaption className="text-sm font-semibold text-text">
              {preview.cell_count} cellule rilevate
            </figcaption>
          </figure>
        )}

        <div className="space-y-1">
          <label htmlFor="preview-frame" className="text-sm font-semibold text-text">
            Frame {frame} di {frames - 1}
          </label>
          <input
            id="preview-frame"
            type="range"
            min={0}
            max={frames - 1}
            value={frame}
            onChange={(e) => setFrame(Number(e.target.value))}
            className="w-full accent-alga"
          />
        </div>
      </div>

      {!paramsValid && (
        <p className="text-xs font-medium text-amber-600 dark:text-amber-400">
          Correggi i parametri per aggiornare l&apos;anteprima.
        </p>
      )}

      {loading && (
        <p role="status" className="text-sm text-text-muted animate-pulse">
          Calcolo dell&apos;anteprima...
        </p>
      )}

      {error && (
        <p role="alert" className="text-sm font-medium text-red-600 dark:text-red-400">
          {error}
        </p>
      )}

      <p className="text-xs text-text-muted">
        L&apos;anteprima usa uno sfondo stimato, il risultato finale può differire leggermente.
      </p>
    </div>
  )
}