import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../application/auth/AuthContext";
import { SUPPORTED_LOCALES, useI18n } from "../../application/i18n/I18nContext";
import { eventsApi } from "../../infrastructure/api/events";
import { CityPicker } from "../components/CityPicker";
import { EventCard } from "../components/EventCard";
import { useGeolocation } from "../hooks/useGeolocation";
import { extractApiError } from "../utils/extractApiError";

const SOURCE_STATUS_KEY = {
  cached: "events.sourceCached",
  rate_limited: "events.sourceRateLimited",
  quota_exhausted: "events.sourceQuotaExhausted",
  error: "events.sourceError",
};

export default function EventsPage() {
  const { t, locale, setLocale } = useI18n();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const geo = useGeolocation();

  const [data, setData] = useState(null);   // { events, source_status, profile_computed_at, total_found }
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [showAll, setShowAll] = useState(false);

  // Sources de verite : on lit directement lat/lng/status pour eviter toute
  // instabilite de reference. Pas de useCallback => pas de boucle de deps.
  const fetchEvents = async (lat, lng, showAllParam = showAll) => {
    setLoading(true);
    setError(null);
    try {
      const params = { show_all: showAllParam };
      if (lat != null && lng != null) {
        params.lat = lat;
        params.lng = lng;
      }
      const response = await eventsApi.recommended(params);
      setData(response);
    } catch (err) {
      setError(extractApiError(err, t("events.errorLoad")));
    } finally {
      setLoading(false);
    }
  };

  // Lance la requete des qu'on a un statut geo definitif OU quand showAll bascule.
  const lat = geo.coords?.lat;
  const lng = geo.coords?.lng;
  useEffect(() => {
    if (geo.status === "pending") return;
    fetchEvents(lat, lng, showAll);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [geo.status, lat, lng, showAll]);

  const onRefreshProfile = async () => {
    setRefreshing(true);
    setError(null);
    try {
      await eventsApi.refreshMusicProfile();
      await fetchEvents(lat, lng);
    } catch (err) {
      setError(extractApiError(err, t("events.errorLoad")));
    } finally {
      setRefreshing(false);
    }
  };

  const onLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="events-page">
      <header className="events-header">
        <div className="events-header-brand">
          <span className="events-brand-name gradient-text">Evenoola</span>
        </div>
        <div className="events-header-actions">
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
          <Link to="/profile" className="header-link">
            {t("events.profileLink")}
          </Link>
          <button className="ghost" onClick={onLogout}>
            {t("events.logout")}
          </button>
        </div>
      </header>

      <section className="events-hero">
        <div>
          <h1 className="events-title">{t("events.title")}</h1>
          <p className="events-subtitle muted">{t("events.subtitle")}</p>
        </div>
        <div className="events-hero-actions">
          {data?.profile_computed_at && (
            <span className="events-profile-fresh muted">
              {t("events.profileFresh", { date: formatProfileDate(data.profile_computed_at, locale) })}
            </span>
          )}
          <button onClick={onRefreshProfile} disabled={refreshing}>
            {refreshing ? t("events.refreshing") : t("events.refreshProfile")}
          </button>
        </div>
      </section>

      <section className="events-location">
        <span className="events-location-label">
          {geo.label || t("events.currentLocation")}
        </span>
        <button type="button" className="ghost" onClick={() => setPickerOpen(true)}>
          {t("events.changeCity")}
        </button>
        {geo.override && (
          <button type="button" className="ghost" onClick={geo.clearOverride}>
            {t("events.useMyLocation")}
          </button>
        )}
      </section>

      {/* Banniere geoloc */}
      {geo.status === "denied" && (
        <div className="banner banner-warn">
          <span>{t("events.geoDenied")}</span>
          <button className="ghost" onClick={geo.retry}>
            {t("events.geoRetry")}
          </button>
        </div>
      )}
      {geo.status === "unavailable" && (
        <div className="banner banner-warn">
          {t("events.geoUnavailable")}
        </div>
      )}

      {/* Banniere source_status */}
      {data?.source_status && SOURCE_STATUS_KEY[data.source_status] && (
        <div className={`banner banner-${data.source_status}`}>
          {t(SOURCE_STATUS_KEY[data.source_status])}
        </div>
      )}

      {/* Contenu principal */}
      {geo.status === "pending" && !data && (
        <div className="events-placeholder">
          <div className="loading-spinner" aria-hidden="true" />
          <p className="muted">{t("events.geoPending")}</p>
        </div>
      )}

      {loading && (
        <div className="events-grid">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="event-card-skeleton">
              <div className="event-card-skeleton-img" />
              <div className="event-card-skeleton-line w70" />
              <div className="event-card-skeleton-line w40" />
            </div>
          ))}
        </div>
      )}

      {!loading && error && <p className="error">{error}</p>}

      {!loading && !error && data?.events?.length === 0 && (
        <div className="events-placeholder">
          {data.total_found > 0 ? (
            <>
              <p>{t("events.noMatchFound", { total: data.total_found })}</p>
              <button onClick={() => setShowAll(true)}>{t("events.showAll")}</button>
            </>
          ) : (
            <>
              <p>{t("events.empty")}</p>
              <p className="muted">{t("events.emptyHint")}</p>
            </>
          )}
        </div>
      )}

      {!loading && !error && data?.events?.length > 0 && showAll && (
        <div className="banner banner-cached" style={{ marginBottom: 16 }}>
          <span>{t("events.showingAll")}</span>
          <button className="ghost" onClick={() => setShowAll(false)}>
            {t("events.showMatchOnly")}
          </button>
        </div>
      )}

      {!loading && !error && data?.events?.length > 0 && (
        <div className="events-grid">
          {data.events.map((ev, i) => (
            <EventCard key={ev.id} event={ev} index={i} />
          ))}
        </div>
      )}

      <CityPicker
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        onSelect={geo.setOverride}
      />
    </div>
  );
}

function formatProfileDate(iso, locale) {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(locale === "EN" ? "en-US" : "fr-FR", {
      day: "numeric",
      month: "short",
    });
  } catch {
    return iso;
  }
}
