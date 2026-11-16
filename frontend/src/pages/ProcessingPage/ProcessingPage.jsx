import { Link } from 'react-router-dom'
import { ParametersSection } from '../../components/ParametersSection/ParametersSection.jsx'
import { useProcessingPageModel } from './ProcessingPage.model'

{/*const AVAILABLE_EXPERIMENTS = [
  { id: '49', name: 'exp_049_algae_tracking', date: '01 Nov 2026' },
  { id: '50', name: 'exp_050_fluorescence_test', date: '03 Nov 2026' },
  { id: '51', name: 'exp_051_photonics_run', date: '05 Nov 2026' },
  { id: '52', name: 'exp_052_lightfield_scan', date: '08 Nov 2026' },
  { id: '53', name: 'exp_053_high_density', date: '09 Nov 2026' },
]*/}

export function ProcessingPage({ pollMs = 2000 }) {
  const model = useProcessingPageModel(pollMs)

  return (
    <div className="p-6 max-w-5xl mx-auto my-6 space-y-6">

      {/* 1. SELETTORE MACCHINA */}
      <fieldset className="space-y-1.5">
        <legend className="text-sm font-semibold text-text">Seleziona Macchina utilizzata</legend>
        <div className="inline-flex p-1 bg-bg border border-border rounded-xl w-full">
          {model.MACHINES.map(({ id, label }) => (
            <label
              key={id}
              className={`flex-1 text-center py-2 px-4 rounded-lg text-sm font-medium transition-all duration-150 cursor-pointer ${
                model.kindMachine === id
                  ? 'bg-surface text-alga shadow-xs font-semibold border border-border/50'
                  : 'text-text-muted hover:text-text'
              }`}
            >
              <input
                type="radio"
                name="kindMachine"
                checked={model.kindMachine === id}
                onChange={() => model.setKindMachine(id)}
                className="sr-only"
              />
              {label}
            </label>
          ))}
        </div>
      </fieldset>

      {/* CARD FORM ELABORAZIONE */}
      <div className="p-6 md:p-8 bg-surface border border-border rounded-2xl shadow-sm text-left space-y-6">

        {/* 2. SELETTORE TIPO INPUT ANALISI */}
        <fieldset className="space-y-1.5">
          <legend className="text-sm font-semibold text-text">Cosa vuoi analizzare?</legend>
          <div className="inline-flex p-1 bg-bg border border-border rounded-xl w-full">
            <label
              className={`flex-1 text-center py-2 px-4 rounded-lg text-sm font-medium transition-all duration-150 cursor-pointer ${
                model.kindDataInput === 'trajectories'
                  ? 'bg-surface text-alga shadow-xs font-semibold border border-border/50'
                  : 'text-text-muted hover:text-text'
              }`}
            >
              <input
                type="radio"
                name="kindDataInput"
                checked={model.kindDataInput === 'trajectories'}
                onChange={() => model.setKindDataInput('trajectories')}
                className="sr-only"
              />
              Traiettorie
            </label>

            <label
              className={`flex-1 text-center py-2 px-4 rounded-lg text-sm font-medium transition-all duration-150 cursor-pointer ${
                model.kindDataInput === 'video'
                  ? 'bg-surface text-alga shadow-xs font-semibold border border-border/50'
                  : 'text-text-muted hover:text-text'
              }`}
            >
              <input
                type="radio"
                name="kindDataInput"
                checked={model.kindDataInput === 'video'}
                onChange={() => model.setKindDataInput('video')}
                className="sr-only"
              />
              Video
            </label>
          </div>
        </fieldset>

        {/* 3. CAMPO NUMERO ESPERIMENTO */}
        <div className="relative space-y-2">
          <div className="flex justify-between items-center">
            <label htmlFor="experiment-input" className="text-sm font-semibold text-text">
              Numero esperimento
            </label>
            <Link
              to="/esperimento"
              className="text-xs font-semibold text-alga hover:underline flex items-center gap-1"
            >
              Gestisci esperimenti →
            </Link>
          </div>

          <input
            id="experiment-input"
            type="text"
            placeholder="Es. 49"
            value={model.experiment}
            onChange={(e) => model.setExperiment(e.target.value)}
            className="w-full px-4 py-2.5 rounded-xl border border-border bg-bg text-text font-normal focus:outline-none focus:ring-2 focus:ring-alga/50 focus:border-alga transition-all"
          />
        </div>

        {/* 4. FILE CARICATI & SUBMIT */}
        <div className="pt-2">

          {/* FILE PRINCIPALE */}
          <div className="mb-8 pb-7 border-b border-border">
            <div className="p-5 rounded-2xl border-2 border-dashed border-alga/40 bg-alga-light/15 hover:border-alga transition-colors space-y-3">
              <div className="flex items-center justify-between">
                <label htmlFor="main-file-input" className="text-base font-bold text-text cursor-pointer flex items-center gap-2">
                  {model.kindDataInput === 'video' ? 'Carica video (*.avi)' : 'Carica traiettoria (*.txt)'}
                </label>
              </div>

              <input
                id="main-file-input"
                type="file"
                accept={model.mainExtension}
                onChange={(e) => model.setMainFile(e.target.files[0] ?? null)}
                className="block w-full text-sm text-text-muted border border-border rounded-xl bg-surface cursor-pointer file:mr-4 file:py-3 file:px-5 file:rounded-l-xl file:border-0 file:text-sm file:font-semibold file:bg-alga file:text-white hover:file:bg-alga-hover transition-all"
              />

              {model.mainFile && !model.mainOk && (
                <p className="text-xs font-medium text-amber-600 dark:text-amber-400">
                  Il file deve essere {model.mainExtension}
                </p>
              )}
            </div>
          </div>

          <div className="space-y-5">
            {/* File illuminazione */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="illumination-file-input" className="text-sm font-semibold text-text cursor-pointer">
                Carica file Illuminazione (*.tiff | *.tif)
              </label>
              <input
                id="illumination-file-input"
                type="file"
                accept=".tif,.tiff"
                onChange={(e) => model.setIllumination(e.target.files[0] ?? null)}
                className="block w-full text-sm text-text-muted border border-border rounded-xl bg-bg cursor-pointer file:mr-4 file:py-2.5 file:px-4 file:rounded-l-xl file:border-0 file:text-sm file:font-semibold file:bg-alga-light file:text-alga hover:file:bg-alga/20 transition-all"
              />
              {model.illumination && !model.illuminationOk && (
                <p className="text-xs font-medium text-amber-600 dark:text-amber-400">
                  L&apos;illuminazione deve essere .tif o .tiff
                </p>
              )}
            </div>

            {/* Parametri di Analisi */}
            <ParametersSection
              title="Parametri di Analisi"
              fields={model.ANALYS_FIELDS}
              values={model.analysParams}
              onChange={model.setAnalysisParams}
            />

            {/* Parametri plot Theta p0 */}
            <ParametersSection
              title="Parametri Plot Theta p0"
              fields={model.PLOT_FIELDS}
              values={model.plotParams}
              onChange={model.setPlotParams}
            />

            {/* Parametri filtri */}
            <ParametersSection
              title="Filtri traiettorie"
              fields={model.FILTER_FIELDS}
              values={model.filterParams}
              onChange={model.setFilterParams}
            />

            {/* Pulsante Avvia */}
            <div className="pt-2">
              <button
                type="button"
                onClick={model.start}
                disabled={!model.canSubmit}
                className="w-full py-3 px-6 rounded-xl font-semibold text-white bg-alga hover:bg-alga-hover shadow-xs transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer flex items-center justify-center gap-2"
              >
                {model.running && (
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                )}
                Avvia
              </button>
            </div>

            {/* Fasi e Errori */}
            {model.running && (
              <div className="flex items-center gap-3 p-4 rounded-xl bg-alga-light/50 border border-alga/20 text-alga font-medium text-sm animate-pulse">
                <span className="w-2.5 h-2.5 rounded-full bg-alga animate-ping" />
                {model.PHASES[model.status] ?? model.status}
              </div>
            )}

            {model.error && (
              <p role="alert" className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 text-sm font-medium">
                {model.error}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}