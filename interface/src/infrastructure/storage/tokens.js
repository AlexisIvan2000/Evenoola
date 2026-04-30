// localStorage centralise pour les tokens JWT (acces + refresh).
// Clefs prefixees pour eviter les collisions en dev sur le meme domaine.

const ACCESS_KEY = "evenoola.access_token";
const REFRESH_KEY = "evenoola.refresh_token";

export const tokenStorage = {
  getAccess() {
    return localStorage.getItem(ACCESS_KEY);
  },
  getRefresh() {
    return localStorage.getItem(REFRESH_KEY);
  },
  set(accessToken, refreshToken) {
    if (accessToken) localStorage.setItem(ACCESS_KEY, accessToken);
    if (refreshToken) localStorage.setItem(REFRESH_KEY, refreshToken);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};
