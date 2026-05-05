import { api } from "./client";

export const eventsApi = {
  // Renvoie { events, source_status, profile_computed_at }
  // lat/lng optionnels : si absents, le backend tombera sur ses fallbacks (spotify country / 422)
  recommended({ lat, lng, radius_km = 50, days_ahead = 60, limit = 30, show_all = false } = {}) {
    const params = { radius_km, days_ahead, limit };
    if (lat != null && lng != null) {
      params.lat = lat;
      params.lng = lng;
    }
    if (show_all) params.show_all = true;
    return api.get("/events/recommended", { params }).then((r) => r.data);
  },

  // Force le recompute du profil musical (3-4 appels Spotify cote backend)
  refreshMusicProfile() {
    return api.post("/me/music-profile/refresh").then((r) => r.data);
  },
};
