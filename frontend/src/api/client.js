import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  `${window.location.protocol}//${window.location.hostname}:5000`;
const TOKEN_KEY = "legalvault_token";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function getApiError(error, fallback = "Something went wrong.") {
  return error?.response?.data?.message || error?.message || fallback;
}

export function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export const authApi = {
  login: (payload) => api.post("/auth/login", payload),
  register: (payload) => api.post("/auth/register", payload),
  forgotPassword: (payload) => api.post("/auth/forgot-password", payload),
  resetPassword: (payload) => api.post("/auth/reset-password", payload),
  me: () => api.get("/auth/me"),
  profile: () => api.get("/auth/profile"),
  updateProfile: (payload) => api.patch("/auth/profile", payload),
};

export const documentsApi = {
  list: () => api.get("/documents"),
  upload: (file, metadata = {}) => {
    const formData = new FormData();
    formData.append("file", file);
    Object.entries(metadata).forEach(([key, value]) => formData.append(key, value || ""));
    return api.post("/documents/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },
  get: (documentId) => api.get(`/documents/${documentId}`),
  update: (documentId, payload) => api.patch(`/documents/${documentId}`, payload),
  getText: (documentId) => api.get(`/documents/${documentId}/text`),
  getOriginal: (documentId) =>
    api.get(`/documents/${documentId}/original`, {
      responseType: "blob",
    }),
  delete: (documentId) => api.delete(`/documents/${documentId}`),
  process: (documentId) => api.post(`/documents/${documentId}/process`),
  summarize: (documentId, sentenceCount = 3) => api.post(`/documents/${documentId}/summarize`, { sentence_count: sentenceCount }),
  search: (query) => api.post("/search", { query }),
  recommendations: (documentId, options = {}) =>
    api.get(`/documents/${documentId}/recommendations`, { params: options }),
};

export const analyticsApi = {
  dashboard: () => api.get("/analytics/dashboard"),
};
