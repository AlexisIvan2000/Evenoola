import axios from "axios";
import { tokenStorage } from "../storage/tokens";

// Base URL du backend, lue depuis .env (VITE_API_URL).
// Vite n'expose au client que les variables prefixees par VITE_.
// Le prefixe /api/v1 est gere ici pour ne pas le repeter dans chaque appel.
export const API_BASE_URL = import.meta.env.VITE_API_URL?? "http://127.0.0.1:5000";
export const API_PREFIX = "/api/v1";

if (!API_BASE_URL) {
  throw new Error("VITE_API_URL n'est pas defini dans interface/.env");
}

export const api = axios.create({
  baseURL: `${API_BASE_URL}${API_PREFIX}`,
});

// Injection automatique du Bearer token sur chaque requete.
api.interceptors.request.use((config) => {
  const token = tokenStorage.getAccess();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Gestion automatique du refresh sur 401 :
// - Si access_token expire, on tente un refresh une fois
// - Si plusieurs requetes echouent en parallele, elles partagent la meme promesse
//   pour ne pas appeler /auth/refresh plusieurs fois
let refreshPromise = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const status = error.response?.status;

    // Pas un 401, ou requete deja retentee, ou requete de refresh elle-meme : on propage
    if (status !== 401 || originalRequest._retry || originalRequest.url?.includes("/auth/refresh")) {
      return Promise.reject(error);
    }

    const refreshToken = tokenStorage.getRefresh();
    if (!refreshToken) {
      tokenStorage.clear();
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      if (!refreshPromise) {
        // axios "naked" pour eviter une boucle infinie d'intercepteurs
        refreshPromise = axios
          .post(`${API_BASE_URL}${API_PREFIX}/auth/refresh`, { refresh_token: refreshToken })
          .then((res) => {
            const { access_token, refresh_token } = res.data;
            tokenStorage.set(access_token, refresh_token);
            return access_token;
          })
          .finally(() => {
            refreshPromise = null;
          });
      }
      const newAccessToken = await refreshPromise;
      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
      return api(originalRequest);
    } catch (refreshError) {
      tokenStorage.clear();
      return Promise.reject(refreshError);
    }
  }
);
