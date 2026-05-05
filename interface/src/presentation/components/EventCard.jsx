import { useI18n } from "../../application/i18n/I18nContext";

const REASON_ICONS = {
  artist_followed: "♥",
  artist_top: "★",
  genre_match: "♫",
};

export function EventCard({ event, index = 0 }) {
  const { t, locale } = useI18n();

  const dateLabel = formatDate(event.start_date, event.start_time, locale);
  const venueLabel = [event.venue?.name, event.venue?.city].filter(Boolean).join(" · ");
  const primary = event.match_reasons?.[0];
  const secondary = event.match_reasons?.slice(1) || [];

  return (
    <a
      className="event-card"
      href={event.url || "#"}
      target="_blank"
      rel="noreferrer"
      style={{ "--i": index }}
    >
      <div className="event-card-img">
        {event.image_url ? (
          <img src={event.image_url} alt="" loading="lazy" />
        ) : (
          <div className="event-card-img-placeholder" />
        )}
        {event.match_score > 0 && (
          <div className="event-card-score">
            {t("events.matchScore", { score: event.match_score })}
          </div>
        )}
      </div>

      <div className="event-card-body">
        <h3 className="event-card-title">{event.name}</h3>
        <p className="event-card-meta">
          {dateLabel}
          {venueLabel && <span className="event-card-meta-sep"> · </span>}
          {venueLabel}
        </p>

        {primary && (
          <p className="event-card-reason-primary">
            <span className="event-card-reason-icon" aria-hidden="true">{REASON_ICONS[primary.type]}</span>
            {primary.label}
          </p>
        )}

        {secondary.length > 0 && (
          <div className="event-card-reasons">
            {secondary.map((r, i) => (
              <span key={i} className={`event-card-reason-chip reason-${r.type}`}>
                <span aria-hidden="true">{REASON_ICONS[r.type]}</span> {r.label}
              </span>
            ))}
          </div>
        )}
      </div>
    </a>
  );
}

function formatDate(dateStr, timeStr, locale) {
  if (!dateStr) return "";
  try {
    const dt = new Date(`${dateStr}T${timeStr || "00:00:00"}`);
    const lang = locale === "EN" ? "en-US" : "fr-FR";
    const opts = timeStr
      ? { day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" }
      : { day: "numeric", month: "long" };
    return dt.toLocaleDateString(lang, opts);
  } catch {
    return dateStr;
  }
}
