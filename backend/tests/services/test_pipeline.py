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
        lambda *a: {"flux": str(a[-1] / "flux.png")},
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
        lambda *a: {"flux": str(a[-1] / "flux.png")},
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
        lambda *a: {"flux": str(plots_dir / "flux.png"), "nt_stats": None},
    )

    run_job(tmp_path, job_id)

    status = read_status(tmp_path, job_id)
    assert status["status"] == "done"
    assert status["plots"]["flux"] is None
    assert status["plots"]["nt_stats"] == "Plot generation failed; see server logs"
