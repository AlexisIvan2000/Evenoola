import { api } from "./client";

export const usersApi = {
  me() {
    return api.get("/me").then((r) => r.data);
  },
  updateProfile(data) {
    return api.patch("/me/profile", data).then((r) => r.data);
  },
};
