"""Operator accounts in SQLite, managed from the terminal with python -m app.users."""

import argparse
import contextlib
import getpass
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

from app.config import get_settings
from app.security import hash_password


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "username TEXT PRIMARY KEY, password_hash TEXT NOT NULL, created_at TEXT NOT NULL)"
    )
    return conn


def create_user(db_path: Path, username: str, password: str) -> None:
    """Store a new user with the argon2id hash of the password, never the password itself."""
    if not username.strip():
        raise ValueError("Username must not be empty")
    password_hash = hash_password(password)
    created_at = datetime.now(UTC).isoformat()
    # closing() closes the connection; "with conn" commits, or rolls back on error.
    with contextlib.closing(_connect(db_path)) as conn, conn:
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, password_hash, created_at),
            )
        except sqlite3.IntegrityError:
            raise ValueError(f"User '{username}' already exists") from None


def get_password_hash(db_path: Path, username: str) -> str | None:
    """Return the stored hash, or None if the user does not exist."""
    with contextlib.closing(_connect(db_path)) as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()
    return row[0] if row else None


def list_users(db_path: Path) -> list[str]:
    with contextlib.closing(_connect(db_path)) as conn:
        rows = conn.execute("SELECT username FROM users ORDER BY username").fetchall()
    return [row[0] for row in rows]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.users", description="Manage users.")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create", help="create a user, asking for the password")
    create.add_argument("username")
    commands.add_parser("list", help="print one username per line")
    args = parser.parse_args(argv)

    db_path = get_settings().data_dir / "users.db"
    if args.command == "create":
        password = getpass.getpass("Password: ")
        if password != getpass.getpass("Repeat password: "):
            print("Passwords do not match", file=sys.stderr)
            sys.exit(1)
        try:
            create_user(db_path, args.username, password)
        except ValueError as exc:
            print(exc, file=sys.stderr)
            sys.exit(1)
        print(f"User '{args.username}' created")
    else:
        for username in list_users(db_path):
            print(username)


if __name__ == "__main__":
    main()
