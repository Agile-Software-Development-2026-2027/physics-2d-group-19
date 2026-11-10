import os
from pathlib import Path

from app.services.experiment_settings import ExperimentSettings, to_settings_line

RESOURCE_SETTINGS = Path(__file__).parent.parent / "resources" / "talgae_settings.txt"


def settings_path(data_dir: Path) -> Path:
    path = data_dir / "experiments" / "talgae_settings.txt"

    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        contenuto = RESOURCE_SETTINGS.read_bytes()
        path.write_bytes(contenuto)

    return path


def experiment_row(row: str) -> ExperimentSettings | None:
    row = row.strip()
    if row == "":
        return None

    pieces = row.split()
    numbers = []
    for piece in pieces:
        numbers.append(float(piece))

    all_zero = True
    for number in numbers[1:]:
        if number != 0:
            all_zero = False
    if all_zero:
        return None

    return ExperimentSettings(
        exps=int(pieces[0]),
        exp_type=int(pieces[1]),
        ill=int(pieces[2]),
        intensity=float(pieces[3]),
        pix_arr=float(pieces[4]),
        no_skip=(pieces[5] == "1"),
        ctr=int(pieces[6]),
        fluo=int(pieces[7]),
        lin=int(pieces[8]),
        axis=int(pieces[9]),
    )


def list_experiments(data_dir: Path) -> list[ExperimentSettings]:

    path = settings_path(data_dir)
    experiment = []

    with open(path, encoding="utf-8") as file:
        for row in file:
            exp = experiment_row(row)
            if exp is not None:
                experiment.append(exp)
    return experiment


def get_experiment(data_dir: Path, exp_id: int) -> ExperimentSettings:

    all = list_experiments(data_dir)

    for experiment in all:
        if experiment.exps == exp_id:
            return experiment

    raise KeyError(exp_id)


def save_experiment(data_dir: Path, settings: ExperimentSettings) -> None:
    path = settings_path(data_dir)

    text = path.read_bytes().decode("utf-8")
    lines = text.splitlines()

    ending = "\n"
    if "\r\n" in text:
        ending = "\r\n"
    trailing = ""
    if text.endswith("\n"):
        trailing = ending

    new_text = to_settings_line(settings)

    position = None
    insert_at = len(lines)
    for i, line in enumerate(lines):
        exp = experiment_row(line)
        if exp is None:
            continue
        if exp.exps == settings.exps:
            position = i
            break
        if exp.exps > settings.exps and insert_at == len(lines):
            insert_at = i

    if position is not None:
        lines[position] = new_text
    else:
        lines.insert(insert_at, new_text)

    final_text = ending.join(lines) + trailing
    temp_path = path.with_suffix(".tmp")
    temp_path.write_bytes(final_text.encode("utf-8"))
    os.replace(temp_path, path)
