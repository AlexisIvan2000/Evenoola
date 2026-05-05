import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../../application/auth/AuthContext";

const REASON_LABELS = {
  invalid_state: "Lien d'autorisation invalide ou expire. Reessaie depuis la page de connexion.",
  spotify_error: "Spotify a refuse l'autorisation. Reessaie plus tard.",
  missing_params: "Reponse Spotify incomplete. Reessaie depuis la page de connexion.",
  access_denied: "Tu as refuse d'autoriser Evenoola.",
};

export default function AuthCallbackPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { completeLogin } = useAuth();

  const code = params.get("code");
  const status = params.get("status");
  const reason = params.get("reason");

  const [error, setError] = useState(
    status === "error" ? REASON_LABELS[reason] || "Une erreur est survenue." : null,
  );

  // Garde anti-double-execution : en mode StrictMode (dev), useEffect tourne 2x,
  // et le code one-shot ne peut etre consomme qu'une seule fois cote backend.
  const consumed = useRef(false);

  useEffect(() => {
    if (!code || status === "error" || consumed.current) return;
    consumed.current = true;
    completeLogin(code)
      .then(() => navigate("/profile", { replace: true }))
      .catch((err) => {
        setError(err.response?.data?.message || "Echec de l'echange de code.");
      });
  }, [code, status, completeLogin, navigate]);

  return (
    <div className="auth-page">
      <div className="auth-card">
        {error ? (
          <>
            <h1>Connexion echouee</h1>
            <p className="error">{error}</p>
            <Link to="/login" className="button-link">
              Retour a la connexion
            </Link>
          </>
        ) : (
          <>
            <h1>Connexion en cours...</h1>
            <p className="muted">Recuperation de tes informations Spotify.</p>
          </>
        )}
      </div>
    </div>
  );
}
