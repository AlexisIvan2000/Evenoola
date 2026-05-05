import { api } from "./client";

export const spotifyApi = {
  // time_range : "short_term" | "medium_term" | "long_term"
  // limit : 1..50
  topArtists({ time_range = "medium_term", limit = 20 } = {}) {
    return api
      .get("/spotify/me/top-artists", { params: { time_range, limit } })
      .then((r) => r.data);
  },
};
