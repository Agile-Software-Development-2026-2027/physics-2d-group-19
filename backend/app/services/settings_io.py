from pathlib import Path

from pydantic import ValidationError

from app.services.experiment_settings import to_settings_line
from app.services.experiments_store import experiment_row, list_experiments, save_experiments


# a line of the imported file does not have 10 numbers: the whole file is refused
class BadSettingsLine(Exception):
    pass


def has_ten_numbers(line: str) -> bool:
    pieces = line.split()
    if len(pieces) != 10:
        return False
    for piece in pieces:
        try:
            float(piece)
        except ValueError:
            return False
    return True


# import the settings file of the PO: create the new experiments and update the old ones
def import_settings(data_dir: Path, text: str) -> dict:
    skipped_empty = 0
    errors = []
    to_save = {}

    for number, line in enumerate(text.splitlines(), start=1):
        if line.strip() == "":
            continue
        # nothing is saved until the end, so stopping here writes nothing
        if not has_ten_numbers(line):
            raise BadSettingsLine(f"Line {number}: expected 10 numbers")

        try:
            experiment = experiment_row(line)
        except ValidationError as exc:
            # a value out of its range, e.g. exp_type 9
            problem = exc.errors()[0]
            errors.append({"line": number, "detail": f"{problem['loc'][0]}: {problem['msg']}"})
            continue
        except ValueError:
            # a decimal number where a whole number is needed, e.g. 49.5 as exps
            errors.append({"line": number, "detail": "a whole number is expected"})
            continue

        if experiment is None:
            skipped_empty += 1
        else:
            to_save[experiment.exps] = experiment

    # count before saving: the ones already registered are updated, the others are new
    registered = [experiment.exps for experiment in list_experiments(data_dir)]
    updated = 0
    for exp_id in to_save:
        if exp_id in registered:
            updated += 1
    created = len(to_save) - updated

    save_experiments(data_dir, list(to_save.values()))

    return dict(created=created, updated=updated, skipped_empty=skipped_empty, errors=errors)


# the settings file in the same format as the script of the PO:
# one line for every number from 0 to the highest, with zeros for the unused numbers
def export_settings(data_dir: Path) -> str:
    experiments = {}
    for experiment in list_experiments(data_dir):
        experiments[experiment.exps] = experiment

    if not experiments:
        return ""

    lines = []
    for exp_id in range(max(experiments) + 1):
        if exp_id in experiments:
            lines.append(to_settings_line(experiments[exp_id]))
        else:
            lines.append(f"{exp_id} 0 0 0 0.000000 0 0 0 0 0")

    return "\n".join(lines) + "\n"
