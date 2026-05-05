import { useState } from "react";
import { useAuth } from "../../application/auth/AuthContext";
import { SUPPORTED_LOCALES, useI18n } from "../../application/i18n/I18nContext";
import { extractApiError } from "../utils/extractApiError";

export default function LoginPage() {
  const { loginWithSpotify } = useAuth();
  const { t, locale, setLocale } = useI18n();
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const onClick = async () => {
    setError(null);
    setSubmitting(true);
    try {
      await loginWithSpotify();
      // Pas de navigate ici : `loginWithSpotify` redirige le navigateur vers Spotify.
    } catch (err) {
      setError(extractApiError(err, t("login.errorStart")));
      setSubmitting(false);
    }
  };

  return (
    <div className="login-split">
      <aside className="login-left">
        <div className="login-left-inner">
          <h1 className="brand-title">
            <span className="gradient-text">Evenoola</span>
          </h1>
          <img className="brand-logo" src="/assets/evenoola-logo.png" alt="" />
          <div className="brand-slogan">
            <p className="brand-slogan-q">{t("login.brandSloganQ")}</p>
            <p className="brand-slogan-a">{t("login.brandSloganA")}</p>
          </div>
        </div>
      </aside>

      <main className="login-right">
        <header className="login-right-header">
          <div className="lang-selector" role="tablist" aria-label="Langue">
            {SUPPORTED_LOCALES.map((code, i) => (
              <span key={code} style={{ display: "contents" }}>
                {i > 0 && <span className="lang-sep" aria-hidden="true">·</span>}
                <button
                  type="button"
                  role="tab"
                  aria-selected={locale === code}
                  className={`lang-option ${locale === code ? "active" : ""}`}
                  onClick={() => setLocale(code)}
                >
                  {code}
                </button>
              </span>
            ))}
          </div>
        </header>
        <div className="login-right-content">
          <div className="login-right-inner">
            <p className="overline">{t("login.overline")}</p>
            <h2 className="login-title">{t("login.title")}</h2>
            <p className="login-text">{t("login.text")}</p>
            <button className="spotify-button" onClick={onClick} disabled={submitting}>
              <img src="/assets/spotify-icon.svg" alt="" className="spotify-icon" />
              <span>{submitting ? t("login.buttonLoading") : t("login.button")}</span>
            </button>
            {error && <p className="error" style={{ marginTop: 16 }}>{error}</p>}
          </div>
        </div>

        <footer className="login-footer">
          <span>© 2026 Evenoola</span>
          <span className="login-footer-sep" aria-hidden="true">·</span>
          <a href="#mentions-legales">{t("login.footerLegal")}</a>
          <span className="login-footer-sep" aria-hidden="true">·</span>
          <a href="#confidentialite">{t("login.footerPrivacy")}</a>
          <span className="login-footer-sep" aria-hidden="true">·</span>
          <a href="#cgu">{t("login.footerTerms")}</a>
        </footer>
      </main>
    </div>
  );
}
