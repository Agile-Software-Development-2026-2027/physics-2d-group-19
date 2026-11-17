import { useEffect, useState } from 'react'
import {
  getGifFrames,
  getGifFrameUrl,
  getGifUrl,
} from '../../api/client/client.js'

// Small line chart of the concentration ratio, with a marker on the chosen frame.
function ConcentrationChart({ values, index }) {
  const width = 300
  const height = 80
  const pad = 6
  const min = Math.min(...values)
  const span = Math.max(...values) - min || 1
  const x = (i) =>
    pad + (i * (width - 2 * pad)) / Math.max(values.length - 1, 1)
  const y = (v) => height - pad - ((v - min) * (height - 2 * pad)) / span
  const points = values.map((v, i) => `${x(i)},${y(v)}`).join(' ')

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full h-auto"
      role="img"
      aria-label="Concentrazione nell'anello nel tempo"
    >
      <polyline
        points={points}
        fill="none"
        stroke="var(--color-alga)"
        strokeWidth="1.5"
      />
      <line
        x1={x(index)}
        x2={x(index)}
        y1={pad}
        y2={height - pad}
        stroke="var(--color-text-muted)"
        strokeDasharray="3 3"
      />
      <circle
        cx={x(index)}
        cy={y(values[index])}
        r="3.5"
        fill="var(--color-alga)"
      />
    </svg>
  )
}

// GIF of the trajectories (US-24): the animated GIF with its download, and a
// slider over the frames with the cells inside the ring and the concentration.
// Shows nothing when the job has no GIF (not requested or failed: 404).
export function GifViewer({ jobId }) {
  const [gifSrc, setGifSrc] = useState(null)
  const [frames, setFrames] = useState(null)
  const [index, setIndex] = useState(0)
  const [frameSrc, setFrameSrc] = useState(null)

  // The GIF and frames.json, once per job
  useEffect(() => {
    let active = true

    getGifUrl(jobId)
      .then((url) => {
        if (!active) return URL.revokeObjectURL(url)
        setGifSrc(url)
      })
      .catch(() => {})

    getGifFrames(jobId)
      .then((data) => {
        if (active) setFrames(data)
      })
      .catch(() => {})

    return () => {
      active = false
    }
  }, [jobId])

  // The PNG of the frame chosen with the slider
  useEffect(() => {
    if (!frames || frames.count === 0) return
    let active = true

    getGifFrameUrl(jobId, index)
      .then((url) => {
        if (!active) return URL.revokeObjectURL(url)
        setFrameSrc(url)
      })
      .catch(() => {})

    return () => {
      active = false
    }
  }, [jobId, index, frames])

  // Each blob URL is freed when it is replaced or when the page closes
  useEffect(() => () => gifSrc && URL.revokeObjectURL(gifSrc), [gifSrc])
  useEffect(() => () => frameSrc && URL.revokeObjectURL(frameSrc), [frameSrc])

  if (!gifSrc) return null

  const hasFrames = frames && frames.count > 0
  const cells = frames?.cells_in_ring?.[index]
  const ratio = frames?.concentration?.[index]
  const videoFrame = frames?.frame_indices?.[index]

  return (
    <section className="mt-8 p-5 rounded-xl border border-border bg-surface">
      <h2 className="mb-4 text-lg font-semibold">Traiettorie (GIF)</h2>

      <div className="grid gap-6 md:grid-cols-2">
        <figure className="flex flex-col gap-2">
          <img
            src={gifSrc}
            alt="GIF delle traiettorie"
            className="w-full rounded-lg bg-white"
          />
          <a
            href={gifSrc}
            download="trajectories.gif"
            className="self-start px-3.5 py-1.5 rounded-lg text-xs font-semibold border border-border bg-bg text-text hover:bg-alga-light hover:text-alga hover:border-alga/40 transition-colors"
          >
            ⬇ Scarica GIF
          </a>
        </figure>

        {hasFrames && (
          <div className="flex flex-col gap-3">
            {frameSrc && (
              <img
                src={frameSrc}
                alt={`Frame ${index + 1} di ${frames.count}`}
                className="w-full rounded-lg bg-white"
              />
            )}

            <label className="flex flex-col gap-1 text-sm">
              <span className="text-text-muted">
                Frame {index + 1} di {frames.count}
                {videoFrame !== undefined && ` (frame ${videoFrame} del video)`}
              </span>
              <input
                type="range"
                min={0}
                max={frames.count - 1}
                value={index}
                onChange={(e) => setIndex(Number(e.target.value))}
                className="w-full accent-alga cursor-pointer"
              />
            </label>

            <p className="text-sm">
              {cells !== undefined && (
                <>
                  <strong>{cells}</strong> cellule nell&apos;anello
                </>
              )}
              {ratio !== undefined && (
                <span className="text-text-muted">
                  {' '}
                  · ρ in/out {ratio.toFixed(2)}
                </span>
              )}
            </p>

            {frames.concentration?.length > 1 && (
              <ConcentrationChart values={frames.concentration} index={index} />
            )}
          </div>
        )}
      </div>
    </section>
  )
}
