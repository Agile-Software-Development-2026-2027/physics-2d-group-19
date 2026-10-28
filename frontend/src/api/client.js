export const setToken = (token) => sessionStorage.setItem('token', token);
export const getToken = () => sessionStorage.getItem('token');
export const removeToken = () => sessionStorage.removeItem('token');

const BASE_URL = '/api';

export async function apiFetch(endpoint, options = {}) {
  const token = getToken();

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      removeToken();
      throw new Error('Sessione scaduta. Effettua nuovamente il login.');
    }
    if (response.status === 400) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || 'Parametri non validi.');
    }
    if (response.status === 404) {
      throw new Error('Risorsa non trovata sul server.');
    }
    throw new Error(`Errore di comunicazione col server (${response.status})`);
  }

  if (response.status === 204) return null;
  return await response.json();
}


// Autenticazione
export async function login(username, password) {
  const data = await apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  if (data.access_token) setToken(data.access_token);
  return data;
}

// Lettura parametri predefiniti
export async function fetchDefaults() {
  return await apiFetch('/params/defaults');
}

// Invio file multipart (es. video o immagini di calibrazione)
export async function uploadFile(endpoint, file) {
  const formData = new FormData();
  formData.append('file', file);

  const token = getToken();
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) throw new Error('Caricamento del file fallito.');
  return await response.json();
}
