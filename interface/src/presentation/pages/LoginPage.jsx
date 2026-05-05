import { useState } from "react";
import { useAuth } from "../../application/auth/AuthContext";
import { extractApiError } from "../utils/extractApiError";

export default function LoginPage() {
  const { loginWithSpotify } = useAuth();
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const onClick = async () => {
    setError(null);
    setSubmitting(true);
    try {
      await loginWithSpotify();
      // Pas de navigate ici : `loginWithSpotify` redirige le navigateur vers Spotify.
    } catch (err) {
      setError(extractApiError(err, "Impossible de demarrer la connexion Spotify"));
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Bienvenue sur Evenoola</h1>
        <p className="muted">
          Connecte-toi avec ton compte Spotify pour decouvrir des evenements selon tes
          artistes et genres preferes.
        </p>
        <button className="spotify-button" onClick={onClick} disabled={submitting}>
          {submitting ? "Redirection..." : "Se connecter avec Spotify"}
        </button>
        {error && <p className="error">{error}</p>}
      </div>
    </div>
  );
}
