import json
from types import SimpleNamespace

import pandas as pd

from app.schemas.params import ProcessingParams
from app.services import pipeline
from app.services.jobs_store import create_job, job_dir, read_status
from app.services.pipeline import run_job


def test_states_in_order_with_trajectories(tmp_path, monkeypatch):
    job_id = create_job(tmp_path, 49)
    (job_dir(tmp_path, job_id) / "input" / "tAlgae49.txt").write_text("frame,y,x,particle\n")
    seen = []
    real_write = pipeline.write_status

    def spy(d, j, status, **kw):
        seen.append(status)
        real_write(d, j, status, **kw)

    monkeypatch.setattr("app.services.pipeline.write_status", spy)
    monkeypatch.setattr("app.services.pipeline.run_analysis", lambda *a: "outputs")
    monkeypatch.setattr("app.services.pipeline.save_legacy_txt", lambda *a: [])
    monkeypatch.setattr("app.services.pipeline.save_csv", lambda *a: [])
    monkeypatch.setattr(
        "app.services.pipeline.generate_plots",
        lambda *a, **kw: {"flux": str(a[4] / "flux.png")},
    )

    run_job(tmp_path, job_id)

    assert seen == ["analysis", "plots", "done"]
    assert read_status(tmp_path, job_id)["plots"] == {"flux": None}


def test_states_in_order_with_video(tmp_path, monkeypatch):
    job_id = create_job(tmp_path, 49)
    base = job_dir(tmp_path, job_id)
    (base / "input" / "tAlgae49.avi").write_bytes(b"fake-avi")
    tracked_txt = base / "tracking" / "tAlgae49.txt"
    seen = []
    real_write = pipeline.write_status

    def spy(d, j, status, **kw):
        seen.append(status)
        real_write(d, j, status, **kw)

    monkeypatch.setattr("app.services.pipeline.write_status", spy)
    monkeypatch.setattr("app.services.pipeline.run_tracking", lambda *a: tracked_txt)
    monkeypatch.setattr("app.services.pipeline.run_analysis", lambda *a: "outputs")
    monkeypatch.setattr("app.services.pipeline.save_legacy_txt", lambda *a: [])
    monkeypatch.setattr("app.services.pipeline.save_csv", lambda *a: [])
    monkeypatch.setattr(
        "app.services.pipeline.generate_plots",
        lambda *a, **kw: {"flux": str(a[4] / "flux.png")},
    )

    run_job(tmp_path, job_id)

    assert seen == ["tracking", "analysis", "plots", "done"]
    assert read_status(tmp_path, job_id)["status"] == "done"


def test_error_is_recorded(tmp_path, monkeypatch):
    job_id = create_job(tmp_path, 49)
    (job_dir(tmp_path, job_id) / "input" / "tAlgae49.txt").write_text("")

    def fail(*args):
        raise ValueError("No trajectories to analyse")

    monkeypatch.setattr("app.services.pipeline.run_analysis", fail)

    run_job(tmp_path, job_id)  # must not raise

    status = read_status(tmp_path, job_id)
    assert status["status"] == "error"
    assert "No trajectories" in status["error"]


def test_plot_failure_is_recorded(tmp_path, monkeypatch):
    job_id = create_job(tmp_path, 49)
    plots_dir = job_dir(tmp_path, job_id) / "plots"
    monkeypatch.setattr("app.services.pipeline.run_analysis", lambda *a: "outputs")
    monkeypatch.setattr("app.services.pipeline.save_legacy_txt", lambda *a: [])
    monkeypatch.setattr("app.services.pipeline.save_csv", lambda *a: [])
    monkeypatch.setattr(
        "app.services.pipeline.generate_plots",
        lambda *a, **kw: {"flux": str(plots_dir / "flux.png"), "nt_stats": None},
    )

    run_job(tmp_path, job_id)

    status = read_status(tmp_path, job_id)
    assert status["status"] == "done"
    assert status["plots"]["flux"] is None
    assert status["plots"]["nt_stats"] == "Plot generation failed; see server logs"


def test_run_job_uses_config_json_and_custom_disc_radius(tmp_path, monkeypatch):
    job_id = create_job(tmp_path, 49)
    base = job_dir(tmp_path, job_id)
    (base / "input" / "tAlgae49.txt").write_text("frame,y,x,particle\n")

    params = ProcessingParams()
    params.analysis.disc_radius = 150
    config_file = base / "parameters" / "config.json"
    config_file.write_text(
        json.dumps({"version": 1, "params": params.model_dump()}),
        encoding="utf-8",
    )

    empty_nt = pd.DataFrame(columns=["N_raw", "n_disc_raw", "dists_raw", "N", "n_disc", "dists"])
    fake_outputs = SimpleNamespace(
        nt_stats=empty_nt,
        flux=pd.DataFrame(),
        theta=pd.DataFrame(),
        theta_y=pd.DataFrame(),
        theta_y_axis0=pd.DataFrame(),
        theta_y_axis1=pd.DataFrame(),
        angle=pd.DataFrame(),
        omega=pd.DataFrame(),
        tumbling_orientation=pd.DataFrame(),
        tumbling_duration=pd.DataFrame(),
    )

    captured_analysis = {}
    captured_plots = {}

    def fake_analysis(exp_id, settings_txt, traj_path, input_dir, a_params, f_params):
        captured_analysis["disc_radius"] = a_params.disc_radius
        return fake_outputs

    def fake_plots(results_dir, settings_txt, input_dir, exp_id, plots_dir, **kw):
        captured_plots["disc_radius"] = kw.get("disc_radius")
        return {"flux": str(plots_dir / "flux.png")}

    monkeypatch.setattr("app.services.pipeline.run_analysis", fake_analysis)
    monkeypatch.setattr("app.services.pipeline.generate_plots", fake_plots)

    run_job(tmp_path, job_id)

    assert read_status(tmp_path, job_id)["status"] == "done"
    assert captured_analysis["disc_radius"] == 150
    assert captured_plots["disc_radius"] == 150
    assert (base / "results" / "Flux_exp49_disc150.txt").exists()


def test_run_job_with_video_passes_custom_tracking_cfg(tmp_path, monkeypatch):
    job_id = create_job(tmp_path, 49)
    base = job_dir(tmp_path, job_id)
    (base / "input" / "tAlgae49.avi").write_bytes(b"fake-avi")

    params = ProcessingParams()
    params.tracking.diameter = 7
    params.tracking.minmass = 250
    config_file = base / "parameters" / "config.json"
    config_file.write_text(
        json.dumps({"version": 1, "params": params.model_dump()}),
        encoding="utf-8",
    )

    captured_tracking = {}

    def fake_tracking(video_path, tracking_dir, cfg):
        captured_tracking["diameter"] = cfg.diameter
        captured_tracking["minmass"] = cfg.minmass
        return tracking_dir / "tAlgae49.txt"

    monkeypatch.setattr("app.services.pipeline.run_tracking", fake_tracking)
    monkeypatch.setattr("app.services.pipeline.run_analysis", lambda *a: "outputs")
    monkeypatch.setattr("app.services.pipeline.save_legacy_txt", lambda *a: [])
    monkeypatch.setattr("app.services.pipeline.save_csv", lambda *a: [])
    monkeypatch.setattr("app.services.pipeline.generate_plots", lambda *a, **kw: {})

    run_job(tmp_path, job_id)

    assert read_status(tmp_path, job_id)["status"] == "done"
    assert captured_tracking["diameter"] == 7
    assert captured_tracking["minmass"] == 250
