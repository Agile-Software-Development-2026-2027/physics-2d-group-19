# Frontend

React 19 + Vite, JavaScript.

```bash
npm ci            # install the exact versions in package-lock.json
npm run dev       # dev server on http://localhost:5173
npm run lint      # ESLint
npm test          # Vitest (jsdom + Testing Library)
npm run build     # production build in dist/
```

In development, requests to `/api` are proxied to the FastAPI backend on `http://localhost:8000`
(start it from `backend/`). In production, set `VITE_API_BASE_URL` at build time if the API is
not served from the same origin (see `.env.example`).
