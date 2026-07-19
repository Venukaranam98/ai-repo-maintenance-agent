import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

let authToken = null;

export function setAuthToken(token) {
  authToken = token;
}

export function getAuthToken() {
  return authToken;
}

const client = axios.create({ baseURL: API_BASE });

client.interceptors.request.use((config) => {
  if (authToken) {
    config.headers.Authorization = `Bearer ${authToken}`;
  }
  return config;
});

export const api = {
  loginUrl: () => `${API_BASE}/auth/github/login`,
  getAvailableRepos: () => client.get("/api/repos/available").then((r) => r.data),
  selectRepos: (full_names) => client.post("/api/repos/select", full_names).then((r) => r.data),
  getMonitoredRepos: () => client.get("/api/repos/monitored").then((r) => r.data),
  getHistory: () => client.get("/api/history").then((r) => r.data),
  triggerScan: (repoId) => client.post(`/api/repos/${repoId}/trigger`).then((r) => r.data),
};

export default client;
