import pandas as pd

from app.services.export_services import save_analysis_results

EXP49_DIR = "tests/fixtures/exp49"
REF_DIR = f"{EXP49_DIR}/reference"


def test_save_analysis_results_matches_fixtures(tmp_path):
    theta_df = pd.read_csv(f"{EXP49_DIR}/Theta_exp49_FluoRadialised.txt", sep="\t")
    angle_df = pd.read_csv(f"{EXP49_DIR}/angle_exp49.txt", sep="\t")
    omega_df = pd.read_csv(f"{EXP49_DIR}/omega_exp49.txt", sep="\t")
    tumb_df = pd.read_csv(f"{EXP49_DIR}/tumb_exp49_tthres5.0.txt", sep="\t")
    tumb_dur_df = pd.read_csv(f"{EXP49_DIR}/tumb_dur_exp49_tthres5.0.txt", sep="\t")

    theta_y_0_df = pd.read_csv(f"{REF_DIR}/ThetaY_axis0_exp49.txt.gz", sep="\t", compression="gzip")
    theta_y_1_df = pd.read_csv(f"{REF_DIR}/ThetaY_axis1_exp49.txt.gz", sep="\t", compression="gzip")

    class RealOutputsMock:
        theta = theta_df
        angle = angle_df
        omega = omega_df
        tumbling_orientation = tumb_df
        tumbling_duration = tumb_dur_df
        theta_y_axis0 = theta_y_0_df
        theta_y_axis1 = theta_y_1_df
        flux = None

    saved_files = save_analysis_results(
        exp_id=49,
        disc_radius=150.0,
        tumbling_threshold=5.0,
        results_data=RealOutputsMock(),
        output_dir=tmp_path
    )

    gen_theta = tmp_path / "Theta_exp49_FluoRadialised.txt"
    assert gen_theta.exists()
    pd.testing.assert_frame_equal(pd.read_csv(gen_theta, sep="\t"), theta_df)

    gen_theta_y_0 = tmp_path / "ThetaY_axis0_exp49.txt.gz"
    assert gen_theta_y_0.exists()
    pd.testing.assert_frame_equal(
        pd.read_csv(gen_theta_y_0, sep="\t", compression="gzip"),
        theta_y_0_df
    )

    assert (tmp_path / "theta.csv").exists()