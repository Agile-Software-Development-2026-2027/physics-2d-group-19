from __future__ import annotations

import numpy as np
import pandas as pd


# Asserts that two DataFrames are equal within floating-point tolerances
def assert_tables_close(
    actual: pd.DataFrame,  # The computed DataFrame under verification
    expected: pd.DataFrame,  # The official reference DataFrame from the laboratory
    rtol: float = 1e-9,  # Relative numerical tolerance
    atol: float = 1e-12,  # Absolute numerical tolerance for values near to zero
    sort_by: list[str] | str | None = None,  # Columns used to sort both tables deterministically
) -> None:

    # Extract column lists to verify that both DataFrames represent identical metrics
    actual_cols = list(actual.columns)
    expected_cols = list(expected.columns)

    # Check that both DataFrames contain the exact same set of column names
    if sorted(actual_cols) != sorted(expected_cols):
        missing = set(expected_cols) - set(actual_cols)
        extra = set(actual_cols) - set(expected_cols)
        raise AssertionError(
            f"Schema mismatch!\n"
            f"  Missing columns in actual: {sorted(missing)}\n"
            f"  Unexpected extra columns: {sorted(extra)}"
        )

    # Reorder columns of both DataFrames using expected_cols as canonical schema
    actual_aligned = actual[expected_cols].copy()
    expected_aligned = expected[expected_cols].copy()

    # Ensure both datasets have identical sample counts
    if len(actual_aligned) != len(expected_aligned):
        raise AssertionError(
            f"Row count mismatch! Actual has {len(actual_aligned)} rows, "
            f"expected {len(expected_aligned)} rows."
        )

    # Deterministic row sorting
    # If a sorting key is provided, sort both tables and reset the numeric index
    if sort_by is not None:
        actual_aligned = actual_aligned.sort_values(by=sort_by).reset_index(drop=True)
        expected_aligned = expected_aligned.sort_values(by=sort_by).reset_index(drop=True)
    else:
        actual_aligned = actual_aligned.reset_index(drop=True)
        expected_aligned = expected_aligned.reset_index(drop=True)

    # Column by column comparison
    for col in expected_cols:
        act_series = actual_aligned[col]
        exp_series = expected_aligned[col]

        # Case 1: numerical data
        if np.issubdtype(act_series.dtype, np.number) and np.issubdtype(
            exp_series.dtype, np.number
        ):
            act_vals = act_series.to_numpy()
            exp_vals = exp_series.to_numpy()

            both_nan = np.isnan(act_vals) & np.isnan(exp_vals)

            # Check if values fall within tolerance: |act - exp| <= atol + rtol * |exp|
            close_mask = np.isclose(act_vals, exp_vals, rtol=rtol, atol=atol) | both_nan

            if not np.all(close_mask):
                # Retrieve all indices where values mismatch
                diff_indices = np.where(~close_mask)[0]
                first_idx = int(diff_indices[0])

                actual_val = act_vals[first_idx]
                expected_val = exp_vals[first_idx]

                # Compute absolute and relative discrepancies for reporting
                delta = (
                    abs(actual_val - expected_val)
                    if not (np.isnan(actual_val) or np.isnan(expected_val))
                    else np.nan
                )
                rel_diff = (
                    (delta / abs(expected_val))
                    if expected_val != 0 and not np.isnan(delta)
                    else delta
                )

                raise AssertionError(
                    f"Regression detected in metric '{col}'!\n"
                    f"  Total mismatching rows: {len(diff_indices)} / {len(act_vals)}\n"
                    f"  First mismatch at row {first_idx}:\n"
                    f"    Actual value:   {actual_val}\n"
                    f"    Expected value: {expected_val}\n"
                    f"    Absolute delta: {delta}\n"
                    f"    Relative delta: {rel_diff}\n"
                    f"    Tolerances:     rtol={rtol}, atol={atol}"
                )
        # Case 2: categorical or text columns
        else:
            if not act_series.equals(exp_series):
                mismatches = act_series != exp_series
                first_idx = int(np.where(mismatches)[0][0])
                raise AssertionError(
                    f"Mismatch in categorical/text column '{col}' at row {first_idx}:\n"
                    f"  Actual:   '{act_series.iloc[first_idx]}'\n"
                    f"  Expected: '{exp_series.iloc[first_idx]}'"
                )
