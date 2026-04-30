import { useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";

const REASON_LABELS = {
  invalid_state: "Lien d'autorisation invalide ou expire. Reessaie depuis ton profil.",
  user_not_found: "Utilisateur introuvable. Tu dois etre connecte avant de connecter Spotify.",
  spotify_error: "Spotify a refuse l'autorisation. Reessaie plus tard.",
  missing_params: "Reponse Spotify incomplete. Reessaie depuis ton profil.",
  access_denied: "Tu as refuse d'autoriser Evenoola.",
};

export default function SpotifyConnectedPage() {
  const [params] = useSearchParams();
  const status = params.get("status");
  const reason = params.get("reason");
  const displayName = params.get("display_name");

  useEffect(() => {
    document.title =
      status === "success" ? "Spotify connecte" : "Echec de connexion Spotify";
  }, [status]);

  return (
    <div className="auth-page">
      <div className="auth-card">
        {status === "success" ? (
          <>
            <h1>Spotify connecte</h1>
            <p>
              {displayName
                ? `Bienvenue ${displayName} ! Ton compte Spotify est maintenant lie a Evenoola.`
                : "Ton compte Spotify est maintenant lie a Evenoola."}
            </p>
          </>
        ) : (
          <>
            <h1>Connexion Spotify echouee</h1>
            <p className="error">{REASON_LABELS[reason] || "Une erreur est survenue."}</p>
          </>
        )}
        <Link to="/profile" className="button-link">
          Retour a mon profil
        </Link>
      </div>
    </div>
  );
}
