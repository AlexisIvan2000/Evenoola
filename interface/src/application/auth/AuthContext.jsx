import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { authApi } from "../../infrastructure/api/auth";
import { usersApi } from "../../infrastructure/api/users";
import { tokenStorage } from "../../infrastructure/storage/tokens";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  // loading=true tant qu'on n'a pas confirme si l'user est connecte ou non.
  // Sert a l'ecran de RequireAuth pour eviter un flash vers /login.
  const [loading, setLoading] = useState(true);

  // Au montage : si on a un access_token, on tente un /me pour reconstruire la session.
  useEffect(() => {
    const token = tokenStorage.getAccess();
    if (!token) {
      setLoading(false);
      return;
    }
    usersApi
      .me()
      .then(setUser)
      .catch(() => tokenStorage.clear())
      .finally(() => setLoading(false));
  }, []);

  // Demarre le flow Spotify : on redirige le navigateur vers la page de consentement.
  const loginWithSpotify = useCallback(async () => {
    const { auth_url } = await authApi.spotifyLoginUrl();
    window.location.href = auth_url;
  }, []);

  // Apres le redirect Spotify -> backend -> /auth/callback?code=..., on echange
  // le code one-shot contre les vrais JWT puis on reconstruit la session.
  const completeLogin = useCallback(async (exchangeCode) => {
    const tokens = await authApi.exchange(exchangeCode);
    tokenStorage.set(tokens.access_token, tokens.refresh_token);
    const me = await usersApi.me();
    setUser(me);
    return me;
  }, []);

  const logout = useCallback(async () => {
    const refreshToken = tokenStorage.getRefresh();
    if (refreshToken) {
      // On ignore une erreur eventuelle : meme si le serveur refuse, on veut deconnecter cote client.
      try {
        await authApi.logout(refreshToken);
      } catch {
        /* noop */
      }
    }
    tokenStorage.clear();
    setUser(null);
  }, []);

  const value = { user, loading, loginWithSpotify, completeLogin, logout, setUser };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth doit etre utilise dans <AuthProvider>");
  return ctx;
}
