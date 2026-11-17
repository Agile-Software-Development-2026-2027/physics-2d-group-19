import { useState } from 'react'
import { uploadVideo } from '../../api/client/client.js'

// Readable messages for the errors of POST /api/videos
const ERROR_MESSAGES = {
  413: 'Il video supera la dimensione massima consentita.',
  422: 'Il video non si può leggere: controlla che il file non sia danneggiato.',
}

function formatBytes(bytes) {
  return bytes >= 1e9 ? `${(bytes / 1e9).toFixed(2)} GB` : `${(bytes / 1e6).toFixed(1)} MB`
}

function formatDuration(seconds) {
  const total = Math.round(seconds)
  const minutes = Math.floor(total / 60)
  return minutes > 0 ? `${minutes} min ${total % 60} s` : `${total} s`
}

// video: response of POST /api/videos or null; onChange receives the new value
export function VideoUpload({ video, onChange }) {
  const [progress, setProgress] = useState(null) // 0–1 while uploading
  const [error, setError] = useState(null)
  const uploading = progress !== null

  async function handleFile(file) {
    setError(null)
    onChange(null)
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.avi')) {
      setError('Il file deve essere .avi')
      return
    }

    setProgress(0)
    try {
      onChange(await uploadVideo(file, setProgress))
    } catch (err) {
      setError(ERROR_MESSAGES[err.status] ?? 'Caricamento del video non riuscito.')
    } finally {
      setProgress(null)
    }
  }

  return (
    <div className="p-5 rounded-2xl border-2 border-dashed border-alga/40 bg-alga-light/15 hover:border-alga transition-colors space-y-3">
      <label htmlFor="video-file-input" className="text-base font-bold text-text cursor-pointer">
        Carica video (*.avi)
      </label>

      <input
        id="video-file-input"
        type="file"
        accept=".avi"
        disabled={uploading}
        onChange={(e) => handleFile(e.target.files[0] ?? null)}
        className="block w-full text-sm text-text-muted border border-border rounded-xl bg-surface cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed file:mr-4 file:py-3 file:px-5 file:rounded-l-xl file:border-0 file:text-sm file:font-semibold file:bg-alga file:text-white hover:file:bg-alga-hover transition-all"
      />

      {uploading && (
        <div className="space-y-1">
          <div
            role="progressbar"
            aria-label="Caricamento del video"
            aria-valuenow={Math.round(progress * 100)}
            aria-valuemin={0}
            aria-valuemax={100}
            className="h-2 rounded-full bg-border overflow-hidden"
          >
            <div className="h-full bg-alga transition-all" style={{ width: `${progress * 100}%` }} />
          </div>
          <p className="text-xs text-text-muted">Caricamento… {Math.round(progress * 100)}%</p>
        </div>
      )}

      {video && (
        <dl className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
          <div>
            <dt className="text-text-muted">Nome</dt>
            <dd className="font-medium text-text break-all">{video.filename}</dd>
          </div>
          <div>
            <dt className="text-text-muted">Dimensione</dt>
            <dd className="font-medium text-text">{formatBytes(video.size_bytes)}</dd>
          </div>
          <div>
            <dt className="text-text-muted">Frame</dt>
            <dd className="font-medium text-text">{video.frames}</dd>
          </div>
          <div>
            <dt className="text-text-muted">Durata</dt>
            <dd className="font-medium text-text">{formatDuration(video.frames / video.fps)}</dd>
          </div>
        </dl>
      )}

      {error && (
        <p role="alert" className="text-xs font-medium text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
    </div>
  )
}
