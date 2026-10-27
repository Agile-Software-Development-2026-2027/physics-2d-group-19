import numpy as np
import pandas as pd
import pytest

from tests.helpers.compare import assert_tables_close

# Tests for the table comparison helper


def test_identical_tables_pass():
    df1 = pd.DataFrame({"theta": [0.1, 0.2, 0.3], "dist": [10.0, 15.5, 20]})
    df2 = pd.DataFrame({"theta": [0.1, 0.2, 0.3], "dist": [10.0, 15.5, 20]})
    assert_tables_close(df1, df2)


def test_values_within_tolerance_pass():
    df1 = pd.DataFrame({"omega": [1.0000000000001]})
    df2 = pd.DataFrame({"omega": [1.0000000000000]})
    assert_tables_close(df1, df2, rtol=1e-9)


def test_exceeding_tolerance_fails_with_explicit_message():
    df1 = pd.DataFrame({"flux": [10.05]})
    df2 = pd.DataFrame({"flux": [10.00]})

    with pytest.raises(AssertionError) as exc_info:
        assert_tables_close(df1, df2, rtol=1e-9)

    msg = str(exc_info.value)
    assert "Regression detected in metric 'flux'" in msg
    assert "First mismatch at row 0" in msg
    assert "Actual value:   10.05" in msg
    assert "Expected value: 10.0" in msg


def test_nan_values_match_consistently():
    df1 = pd.DataFrame({"theta": [np.nan, 1.5]})
    df2 = pd.DataFrame({"theta": [np.nan, 1.5]})
    assert_tables_close(df1, df2)


def test_nan_mismatch_fails():
    df1 = pd.DataFrame({"theta": [np.nan]})
    df2 = pd.DataFrame({"theta": [1.5]})

    with pytest.raises(AssertionError) as exc_info:
        assert_tables_close(df1, df2)

    assert "Regression detected in metric 'theta'" in str(exc_info.value)


def test_schema_mismatch_fails():
    df1 = pd.DataFrame({"theta": [1.0]})
    df2 = pd.DataFrame({"omega": [1.0]})

    with pytest.raises(AssertionError) as exc_info:
        assert_tables_close(df1, df2)

    assert "Schema mismatch" in str(exc_info.value)


def test_row_count_mismatch_fails():
    df1 = pd.DataFrame({"theta": [1.0, 2.0]})
    df2 = pd.DataFrame({"theta": [1.0]})

    with pytest.raises(AssertionError) as exc_info:
        assert_tables_close(df1, df2)

    assert "Row count mismatch" in str(exc_info.value)


def test_sorting_handles_unaligned_rows():
    df1 = pd.DataFrame({"time": [2.0, 1.0], "flux": [20.0, 10.0]})
    df2 = pd.DataFrame({"time": [1.0, 2.0], "flux": [10.0, 20.0]})
    assert_tables_close(df1, df2, sort_by="time")


def test_sorting_with_ties_breaks_deterministically():
    df1 = pd.DataFrame({"dist": [1.0, 1.0], "theta": [0.1, 0.2]})
    df2 = pd.DataFrame({"dist": [1.0, 1.0], "theta": [0.2, 0.1]})
    assert_tables_close(df1, df2, sort_by="dist")
