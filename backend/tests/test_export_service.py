from pathlib import Path

import pandas as pd

from app.services.export_services import save_analysis_results

BASE_FIXTURES = Path(__file__).parent / "fixtures" / "exp49"

EXP49_DIR = str(BASE_FIXTURES)
REF_DIR = str(BASE_FIXTURES / "reference")


def test_save_analysis_results_matches_fixtures(tmp_path):
    # 1. ARRANGE
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

    # 2. ACT
    saved_files = save_analysis_results(
        exp_id=49,
        disc_radius=150.0,
        tumbling_threshold=5.0,
        results_data=RealOutputsMock(),
        output_dir=tmp_path,
    )

    # 3. ASSERT
    assert "theta" in saved_files
    assert "theta_y_axis0" in saved_files
    assert "csv_theta" in saved_files

    # Verify saved files using the paths in saved_files
    theta_path = saved_files["theta"]
    assert theta_path.exists()
    pd.testing.assert_frame_equal(pd.read_csv(theta_path, sep="\t"), theta_df)

    theta_y_0_path = saved_files["theta_y_axis0"]
    assert theta_y_0_path.exists()
    pd.testing.assert_frame_equal(
        pd.read_csv(theta_y_0_path, sep="\t", compression="gzip"), theta_y_0_df
    )

    # Check for the presence of generated CSV files
    assert saved_files["csv_theta"].exists()
