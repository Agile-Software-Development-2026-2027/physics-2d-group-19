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


# the numbers in exp_ids that are already registered
def find_existing(data_dir: Path, exp_ids: list[int]) -> list[int]:
    registered = []
    for experiment in list_experiments(data_dir):
        registered.append(experiment.exps)

    existing = []
    for exp_id in exp_ids:
        if exp_id in registered:
            existing.append(exp_id)
    return existing


# put the line of one experiment in the right place of the file
def put_line(lines: list[str], settings: ExperimentSettings) -> None:
    new_line = to_settings_line(settings)

    for i, line in enumerate(lines):
        pieces = line.split()
        if not pieces:
            continue
        number = int(pieces[0])

        # the experiment is already in the file (also as a row of zeros): replace it
        if number == settings.exps:
            lines[i] = new_line
            return

        # first experiment with a higher number: insert the new line before it
        if number > settings.exps:
            lines.insert(i, new_line)
            return

    # it is the highest number: add it at the end
    lines.append(new_line)


# read the file once, put all the experiments in it, write it once
def save_experiments(data_dir: Path, experiments: list[ExperimentSettings]) -> None:
    path = settings_path(data_dir)
    text = path.read_bytes().decode("utf-8")

    # keep the same line ending as the original file
    ending = "\n"
    if "\r\n" in text:
        ending = "\r\n"

    lines = text.splitlines()
    for settings in experiments:
        put_line(lines, settings)

    new_text = ending.join(lines)
    if text.endswith("\n"):
        new_text = new_text + ending

    # write a temporary file, then swap it with the real one
    temp_path = path.with_suffix(".tmp")
    temp_path.write_bytes(new_text.encode("utf-8"))
    os.replace(temp_path, path)


def save_experiment(data_dir: Path, settings: ExperimentSettings) -> None:
    save_experiments(data_dir, [settings])
