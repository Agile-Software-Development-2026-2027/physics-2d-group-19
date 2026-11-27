# Service layer for managing reusable experimental setups stored in setups.json

import json
import os
import re
import secrets
import threading
from pathlib import Path

from app.schemas.setup import Setup, SetupCreate

# Lock to guarantee thread-safe read-modify-write operations
_LOCK = threading.Lock()
# Regex to validate 12-character IDs
_ID_REGEX = re.compile(r"^[0-9a-f]{12}$")

# Default setup values seeded on first run
DEFAULT_SETUP_VALUES = {
    "name": "Default",
    "is_default": True,
    "ill": 14,
    "intensity": 180,
    "pix_arr": 1.041667,
    "exp_type": 1,
    "ctr": 0,
    "fluo": 0,
    "lin": 0,
    "axis": 0,
}


class DuplicateSetupName(ValueError):
    """Raised when trying to create/rename a setup with an existing name."""


class CannotDeleteLastSetup(ValueError):
    """Raised when attempting to delete the only existing setup."""


def _setups_path(data_dir: Path) -> Path:
    # Returns the path to data/experiments/setups.json
    return data_dir / "experiments" / "setups.json"


def _generate_id() -> str:
    # Generates a random 12-character hexadecimal string
    return secrets.token_hex(6)


# Reads setups from disk. If the file does not exist, creates the 'Default' setup
def _load_setups_unlocked(path: Path) -> list[Setup]:
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        default_setup = Setup(id=_generate_id(), **DEFAULT_SETUP_VALUES)
        _save_setups_unlocked(path, [default_setup])
        return [default_setup]

    try:
        raw_data = json.loads(path.read_text(encoding="utf-8"))
        return [Setup.model_validate(item) for item in raw_data]
    except (json.JSONDecodeError, ValueError):
        # Fallback in case of an empty or corrupted file
        default_setup = Setup(id=_generate_id(), **DEFAULT_SETUP_VALUES)
        _save_setups_unlocked(path, [default_setup])
        return [default_setup]


# Atomically writes setups to disk using a temporary file and os.replace
def _save_setups_unlocked(path: Path, setups: list[Setup]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    data = [setup.model_dump() for setup in setups]
    tmp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp_path, path)


# Returns all setups with the default one first
def list_setups(data_dir: Path) -> list[Setup]:
    path = _setups_path(data_dir)
    with _LOCK:
        setups = _load_setups_unlocked(path)
    return sorted(setups, key=lambda s: not s.is_default)


# Create a new setup. Raises DuplicateSetupName if name exists
def create_setup(data_dir: Path, data: SetupCreate) -> Setup:
    path = _setups_path(data_dir)
    with _LOCK:
        setups = _load_setups_unlocked(path)

        # Check case-insensitive uniqueness of the name
        norm_name = data.name.lower()
        if any(s.name.lower() == norm_name for s in setups):
            raise DuplicateSetupName(f"A setup named '{data.name}' already exists")

        new_setup = Setup(id=_generate_id(), **data.model_dump())

        # If the new setup is marked as default, clear default from all others
        if new_setup.is_default:
            for s in setups:
                s.is_default = False

        setups.append(new_setup)
        _save_setups_unlocked(path, setups)
        return new_setup


# Update a setup. Raises KeyError if not found, DuplicateSetupName on duplicate
def update_setup(data_dir: Path, setup_id: str, data: SetupCreate) -> Setup:
    if not _ID_REGEX.match(setup_id):
        raise KeyError(f"Invalid setup ID: {setup_id}")

    path = _setups_path(data_dir)
    with _LOCK:
        setups = _load_setups_unlocked(path)

        idx = next((i for i, s in enumerate(setups) if s.id == setup_id), None)
        if idx is None:
            raise KeyError(f"Setup {setup_id} not found")

        # Name must be unique among other setups
        norm_name = data.name.lower()
        if any(s.name.lower() == norm_name and s.id != setup_id for s in setups):
            raise DuplicateSetupName(f"A setup named '{data.name}' already exists")

        updated = Setup(id=setup_id, **data.model_dump())

        if updated.is_default:
            # Demote any other setup that was previously default
            for s in setups:
                s.is_default = False
        elif setups[idx].is_default:
            # If removing default status, make sure another setup becomes default
            other = next((s for s in setups if s.id != setup_id), None)
            if other is not None:
                other.is_default = True
            else:
                updated.is_default = True

        setups[idx] = updated
        _save_setups_unlocked(path, setups)
        return updated


# Delete a setup. Raises KeyError if not found, CannotDeleteLastSetup if it's the last one
def delete_setup(data_dir: Path, setup_id: str) -> None:
    if not _ID_REGEX.match(setup_id):
        raise KeyError(f"Invalid setup ID: {setup_id}")

    path = _setups_path(data_dir)
    with _LOCK:
        setups = _load_setups_unlocked(path)

        # Find the setup to delete
        target = next((s for s in setups if s.id == setup_id), None)

        # If the setup does not exist, raise KeyError
        if target is None:
            raise KeyError(f"Setup {setup_id} not found")

        # Cannot delete if it is the only setup left
        if len(setups) <= 1:
            raise CannotDeleteLastSetup("Cannot delete the only remaining setup")

        was_default = target.is_default
        remaining = [s for s in setups if s.id != setup_id]

        # If the deleted setup was default, promote the first remaining one
        if was_default and remaining:
            remaining[0].is_default = True

        _save_setups_unlocked(path, remaining)
