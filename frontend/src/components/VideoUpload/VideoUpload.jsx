import { useState } from 'react'
import { uploadVideo } from '../../api/client/client.js'

// Readable messages for the errors of POST /api/videos
const ERROR_MESSAGES = {
  413: 'Il video supera il limite di dimensione',
  422: 'Il file non è un .avi valido o non si riesce a leggere',
}

// Uploads the .avi with POST /api/videos (17.1), showing the progress and then
// the video info. onUploaded receives the response, or null when a new upload
// starts or fails, so the page never keeps a stale video_id.
export function VideoUpload({ onUploaded, disabled = false }) {
  const [progress, setProgress] = useState(null) // 0–1 while uploading
  const [video, setVideo] = useState(null)
  const [error, setError] = useState(null)
  const uploading = progress !== null

  async function handleFile(file) {
    setVideo(null)
    setError(null)
    onUploaded(null)
    if (!file) return

    setProgress(0)
    try {
      const response = await uploadVideo(file, setProgress)
      setVideo(response)
      onUploaded(response)
    } catch (err) {
      setError(ERROR_MESSAGES[err.status] ?? 'Caricamento non riuscito, riprova')
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
        disabled={disabled || uploading}
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
            <dd className="font-medium text-text">{(video.size_bytes / 1e6).toFixed(1)} MB</dd>
          </div>
          <div>
            <dt className="text-text-muted">Frame</dt>
            <dd className="font-medium text-text">{video.frames}</dd>
          </div>
          <div>
            <dt className="text-text-muted">Durata</dt>
            <dd className="font-medium text-text">{(video.frames / video.fps).toFixed(1)} s</dd>
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
