import { api } from "./client";

export const authApi = {
  // Demarre le login Spotify : renvoie { auth_url } pour rediriger le navigateur.
  spotifyLoginUrl() {
    return api.get("/auth/spotify/login").then((r) => r.data);
  },
  // Echange un code one-shot (recu en query du callback) contre la paire de JWT.
  exchange(code) {
    return api.post("/auth/exchange", { code }).then((r) => r.data);
  },
  logout(refreshToken) {
    return api.post("/auth/logout", { refresh_token: refreshToken });
  },
};
