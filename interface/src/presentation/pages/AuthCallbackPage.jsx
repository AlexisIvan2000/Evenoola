import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../../application/auth/AuthContext";
import { useI18n } from "../../application/i18n/I18nContext";

// Mapping reason backend -> cle de traduction.
const REASON_KEYS = {
  invalid_state: "callback.reasonInvalidState",
  spotify_error: "callback.reasonSpotifyError",
  missing_params: "callback.reasonMissingParams",
  access_denied: "callback.reasonAccessDenied",
};

export default function AuthCallbackPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { completeLogin } = useAuth();
  const { t } = useI18n();

  const code = params.get("code");
  const status = params.get("status");
  const reason = params.get("reason");

  const [error, setError] = useState(
    status === "error"
      ? (REASON_KEYS[reason] ? t(REASON_KEYS[reason]) : t("callback.errorGeneric"))
      : null,
  );

  // Garde anti-double-execution : en mode StrictMode (dev), useEffect tourne 2x,
  // et le code one-shot ne peut etre consomme qu'une seule fois cote backend.
  const consumed = useRef(false);

  useEffect(() => {
    if (!code || status === "error" || consumed.current) return;
    consumed.current = true;
    completeLogin(code)
      .then(() => navigate("/events", { replace: true }))
      .catch((err) => {
        setError(err.response?.data?.message || t("callback.errorExchange"));
      });
  }, [code, status, completeLogin, navigate, t]);

  return (
    <div className="auth-page">
      <div className="auth-card callback-card">
        {error ? (
          <>
            <h1>{t("callback.titleError")}</h1>
            <p className="error" style={{ width: "100%" }}>{error}</p>
            <Link to="/login" className="button-link">
              {t("callback.backToLogin")}
            </Link>
          </>
        ) : (
          <>
            <div className="loading-spinner" aria-hidden="true" />
            <h1>
              <span className="gradient-text">{t("callback.titleLoading")}</span>
            </h1>
            <p className="muted" style={{ margin: 0 }}>
              {t("callback.textLoading")}
            </p>
          </>
        )}
      </div>
    </div>
  );
}
