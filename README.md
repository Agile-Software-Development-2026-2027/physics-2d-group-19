# Moving Chlamydomonas

Web application for tracking and physical analysis of *Chlamydomonas* algae cells.

## First setup and operator account

Before using the application, initialize the virtual environment and create the first operator account from `backend/`:

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.users create operator
```

The command prompts for the password twice without echoing it. Passwords are never stored in plain text and are hashed using Argon2id.

To list existing operator accounts:

```bash
python -m app.users list
```

## Running the application
In two separate terminals:

1. Backend (port 8000):

``` bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

2. Frontend (port 5173):

``` bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser and log in with your operator credentials.

## How we work

- `main` is protected: nobody can push to it, every change goes through a pull request.
- Branches are short-lived (less than a day) and pull requests are small (less than 200 lines).
- A pull request needs the approval of a teammate and a green CI, and must be up to date with
  `main`. It is merged with a squash merge.
- The backlog and the sprints are on the Jira board of the team, not in this repository.
- The title of a pull request starts with the key of the Jira issue it implements:
  `ABC-12 Add the login form`.
- If `main` is red, fixing it comes before anything else.

## CI

`.github/workflows/ci.yml` runs on every pull request. It starts empty and always passes: add
the steps that build and test the project as soon as there is something to test.
