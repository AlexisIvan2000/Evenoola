import { api } from "./client";

export const geocodeApi = {
  // Renvoie { results: [{ display_name, lat, lng, country_code, type }] }
  search(q, limit = 5) {
    return api.get("/geocode/search", { params: { q, limit } }).then((r) => r.data);
  },
};
