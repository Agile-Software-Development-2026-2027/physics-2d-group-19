# API router for managing experimental setups

from fastapi import APIRouter, HTTPException, status

from app.config import get_settings
from app.schemas.setup import Setup, SetupCreate
from app.services.setups_store import (
    CannotDeleteLastSetup,
    DuplicateSetupName,
    create_setup,
    delete_setup,
    list_setups,
    update_setup,
)

router = APIRouter(prefix="/setups", tags=["setups"])


# Retrieve all saved setups, returning the default setup first
@router.get("", response_model=list[Setup])
def get_setups() -> list[Setup]:
    data_dir = get_settings().data_dir
    return list_setups(data_dir)


# Create a new setup. Raises 409 if name already exists
@router.post("", response_model=Setup, status_code=status.HTTP_201_CREATED)
def post_setup(setup_in: SetupCreate) -> Setup:
    data_dir = get_settings().data_dir
    try:
        return create_setup(data_dir, setup_in)
    except DuplicateSetupName as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


# Update an existing setup. Raises 404 if not found, 409 on duplicate name
@router.put("/{setup_id}", response_model=Setup)
def put_setup(setup_id: str, setup_in: SetupCreate) -> Setup:
    data_dir = get_settings().data_dir
    try:
        return update_setup(data_dir, setup_id, setup_in)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Setup not found"
        ) from exc
    except DuplicateSetupName as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


# Delete a setup. Raises 404 if not found, 409 if it's the last one
@router.delete("/{setup_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_setup(setup_id: str) -> None:
    data_dir = get_settings().data_dir
    try:
        delete_setup(data_dir, setup_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Setup not found"
        ) from exc
    except CannotDeleteLastSetup as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
