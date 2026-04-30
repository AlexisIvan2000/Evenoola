import { api } from "./client";

export const authApi = {
  register(data) {
    return api.post("/auth/register", data).then((r) => r.data);
  },
  login(data) {
    return api.post("/auth/login", data).then((r) => r.data);
  },
  logout(refreshToken) {
    return api.post("/auth/logout", { refresh_token: refreshToken });
  },
};
