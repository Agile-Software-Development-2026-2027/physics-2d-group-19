"""Esegue l'analisi legacy sull'esperimento 49 (radial_map=False) e salva i
risultati attesi in backend/tests/fixtures/exp49/reference/ come .txt.gz.

Uso:
    python backend/scripts/make_reference.py [--plots DIR]

Va lanciato con le versioni pinnate di numpy/pandas/scipy/matplotlib
(vedi backend/tests/fixtures/exp49/README.md, sezione 6).
"""

import os

os.environ.setdefault("MPLBACKEND", "Agg")  # deve stare prima di ogni import che tocchi matplotlib

import argparse
import gzip
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
REPO_ROOT = BACKEND_DIR.parent
LEGACY_ROOT = REPO_ROOT / "legacy-code"
FIXTURES_DIR = BACKEND_DIR / "tests" / "fixtures" / "exp49"
REFERENCE_DIR = FIXTURES_DIR / "reference"

sys.path.insert(0, str(LEGACY_ROOT))

from analyses.load_results import load_settings, load_tumbling_file  # noqa: E402
from analyses.plot_angle_distribution import plot_angle_distribution  # noqa: E402
from analyses.plot_density_vs_distance import plot_density_vs_distance  # noqa: E402
from analyses.plot_flux import plot_flux  # noqa: E402
from analyses.plot_nt_stats import plot_nt_stats  # noqa: E402
from analyses.plot_omega_distribution import plot_omega_distribution  # noqa: E402
from analyses.plot_theta_distribution import plot_theta_distribution  # noqa: E402
from analyses.plot_tumbling import (  # noqa: E402
    plot_tumbling_duration_vs_distance,
    plot_tumbling_vs_gradient,
)
from clam_pipeline.analyze import AnalysisParams, FilterParams  # noqa: E402
from clam_pipeline.cli import main as run_legacy_analysis  # noqa: E402

EXP_ID = 49

# Parametri espliciti dell'esperimento 49. NON lasciare params/fparams a None:
# clam_pipeline.cli.main() usa, se non specificati, default diversi da quelli
# del dataclass (radial_map=True di default, e FilterParams con
# blinking_tolerance=0.1 / long_track_min_snaps=20 invece di 0.0 / 0).
DISC_RADIUS = 350  # ricordato dalla demo live (inner_circle = disc_radius = 350)
# da riconfermare con l'operatrice
# Intero (non float): clam_pipeline/cli.py salva i file flat con int(disc_radius)
# nel nome (es. Flux_exp49_disc350.txt); le funzioni di plot cercano il file
# costruendo il nome dal valore che gli passiamo, quindi deve combaciare esattamente.
DT = 0.1  # default legacy: da verificare contro gli fps reali del video tAlgae49.avi
TUMBLING_THRESHOLD = 5.0  # confermato dal nome del file dell'operatrice

PARAMS = AnalysisParams(
    diam=10,
    dt=DT,
    particle_show=5,
    disc_radius=DISC_RADIUS,
    flux_cg_in=1,
    flux_cg_out=150,
    tumbling_threshold=TUMBLING_THRESHOLD,
    radial_map=False,  # modalità corretta per il 49 (manca il file della mappa radiale)
    nskip=1,
)

FPARAMS = FilterParams(
    # Ricordati dalla demo live con l'operatrice: filtri sostanzialmente disattivati
    # (tutti a 0 tranne dist_step) - da riconfermare via mail.
    lifetime_min=0,
    threshold_dist=0,
    threshold_dist_tot=0,
    dist_step=1,
    strict=True,
    only_inside=True,
    blinking_ratio=0,
    blinking_tolerance=0,
    long_track_min_snaps=0,
)

# Output flat legacy che finiscono nel riferimento. Restano fuori:
# - i CSV della cartella results/<timestamp>/ (stessi dati in un altro formato)
# - tumb_exp49_tthres5.0.txt, identico al file dell'operatrice gia' tra gli input
REFERENCE_FILES = [
    f"angle_exp{EXP_ID}.txt",
    f"omega_exp{EXP_ID}.txt",
    f"Theta_exp{EXP_ID}_FluoRadialised.txt",
    f"ThetaY_exp{EXP_ID}.txt",
    f"ThetaY_axis0_exp{EXP_ID}.txt",
    f"ThetaY_axis1_exp{EXP_ID}.txt",
    f"Flux_exp{EXP_ID}_disc{DISC_RADIUS}.txt",
    f"N_dist_exp{EXP_ID}_disc{DISC_RADIUS}.txt",
    f"N_dist_compare_exp{EXP_ID}_disc{DISC_RADIUS}.txt",
    f"tumb_dur_exp{EXP_ID}_tthres{TUMBLING_THRESHOLD:.1f}.txt",
]


def run_analysis(work_dir: Path) -> dict:
    # non deve esistere: con radial_map=False non viene mai controllata
    radial_dir = FIXTURES_DIR / "_unused_radial_map"

    # cli.main() scrive i .txt flat nel genitore di results_dir e i CSV in
    # results_dir/<timestamp>/: tutto resta nella cartella temporanea.
    return run_legacy_analysis(
        code_dir=LEGACY_ROOT,
        traj_dir=FIXTURES_DIR,
        settings_txt=FIXTURES_DIR / "talgae_settings.txt",
        illum_dir=FIXTURES_DIR,
        radial_dir=radial_dir,
        results_dir=work_dir / "results",
        exp_ids=EXP_ID,
        params=PARAMS,
        fparams=FPARAMS,
    )


def save_reference(flat_results_dir: Path) -> None:
    """Copia gli output scelti in reference/ come .txt.gz, con fine riga LF
    (su Windows il legacy scrive CRLF) e mtime=0 nell'header gzip, cosi' due
    rigenerazioni identiche producono gli stessi byte."""
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)

    for name in REFERENCE_FILES:
        data = (flat_results_dir / name).read_bytes().replace(b"\r\n", b"\n")
        out_path = REFERENCE_DIR / f"{name}.gz"
        with (
            open(out_path, "wb") as raw,
            gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0) as gz,
        ):
            gz.write(data)

    print(f"[OK] Riferimento salvato in: {REFERENCE_DIR}")


def make_plots(flat_results_dir: Path, settings_path: Path, plots_dir: Path) -> None:
    plots_dir.mkdir(parents=True, exist_ok=True)

    settings = load_settings(settings_path)
    exp_mask = settings["exps"] == EXP_ID

    plot_theta_distribution(
        results_dir=flat_results_dir,
        settings_path=settings_path,
        exp_ids=[EXP_ID],
        mask=exp_mask,
        inner_circle=DISC_RADIUS,
        thickness_circle=0,
        buffer=0,
        max_distance=800,
        save_path=plots_dir / f"theta_distribution_exp{EXP_ID}.pdf",
    )
    plot_flux(
        results_dir=flat_results_dir,
        settings_path=settings_path,
        exp_ids=[EXP_ID],
        disc_radius=DISC_RADIUS,
        save_path=plots_dir / f"flux_plot_exp{EXP_ID}.pdf",
    )
    plot_density_vs_distance(
        results_dir=flat_results_dir,
        settings_path=settings_path,
        illum_dir=FIXTURES_DIR,
        exp_ids=[EXP_ID],
        save_path=plots_dir / f"density_vs_distance_exp{EXP_ID}.pdf",
    )
    plot_angle_distribution(
        results_dir=flat_results_dir,
        exp_ids=[EXP_ID],
        save_path=plots_dir / f"angle_distribution_exp{EXP_ID}.pdf",
    )
    plot_omega_distribution(
        results_dir=flat_results_dir,
        exp_ids=[EXP_ID],
        save_path=plots_dir / f"omega_distribution_exp{EXP_ID}.pdf",
    )
    plot_nt_stats(
        results_dir=flat_results_dir,
        exp_ids=[EXP_ID],
        disc_radius=DISC_RADIUS,
        save_path=plots_dir / f"nt_stats_exp{EXP_ID}.pdf",
    )
    plot_tumbling_vs_gradient(
        results_dir=flat_results_dir,
        exp_ids=[EXP_ID],
        save_path=plots_dir / f"tumbling_vs_gradient_exp{EXP_ID}.pdf",
    )
    plot_tumbling_duration_vs_distance(
        results_dir=flat_results_dir,
        exp_ids=[EXP_ID],
        save_path=plots_dir / f"tumbling_duration_vs_distance_exp{EXP_ID}.pdf",
    )

    print(f"[OK] Grafici salvati in: {plots_dir}")


def compare_with_operator_tumbling(flat_results_dir: Path) -> None:
    """Controllo veloce (non un test automatico) contro il file gia' fornito
    dall'operatrice, per capire se i parametri scelti sono plausibili."""
    generated_path = flat_results_dir / f"tumb_exp{EXP_ID}_tthres{TUMBLING_THRESHOLD:.1f}.txt"
    reference_path = FIXTURES_DIR / "tumb_exp49_tthres5.0.txt"

    if not generated_path.exists():
        print(f"[WARN] Non trovato output generato: {generated_path}")
        return
    if not reference_path.exists():
        print(f"[WARN] Non trovato file dell'operatrice: {reference_path}")
        return

    generated = load_tumbling_file(generated_path)
    reference = load_tumbling_file(reference_path)

    print("\n[CONFRONTO con tumb_exp49_tthres5.0.txt dell'operatrice]")
    print(f"  righe generate:   {len(generated)}")
    print(f"  righe operatrice: {len(reference)}")
    if len(generated) > 0 and len(reference) > 0:
        print(f"  theta medio generato:    {generated['theta'].mean():.4f}")
        print(f"  theta medio operatrice:  {reference['theta'].mean():.4f}")
        print(f"  duration medio generato:   {generated['duration'].mean():.4f}")
        print(f"  duration medio operatrice: {reference['duration'].mean():.4f}")
    print("  (controllo indicativo: la conferma ufficiale arriva dalla mail all'operatrice,")
    print("  US-1 1.3/1.4)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--plots",
        type=Path,
        metavar="DIR",
        help="salva anche i grafici PDF in DIR (fuori dal repo: non vanno committati)",
    )
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        result = run_analysis(Path(tmp))
        flat_results_dir = result["flat_results_dir"]

        save_reference(flat_results_dir)
        if args.plots is not None:
            make_plots(flat_results_dir, result["settings_txt"], args.plots)
        compare_with_operator_tumbling(flat_results_dir)


if __name__ == "__main__":
    main()
