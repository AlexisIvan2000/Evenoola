import { useEffect, useRef, useState } from "react";
import { useI18n } from "../../application/i18n/I18nContext";
import { geocodeApi } from "../../infrastructure/api/geocode";

const DEBOUNCE_MS = 300;

export function CityPicker({ open, onClose, onSelect }) {
  const { t } = useI18n();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  // Reset etat a l'ouverture + autofocus
  useEffect(() => {
    if (!open) return;
    setQuery("");
    setResults([]);
    setError(null);
    const id = setTimeout(() => inputRef.current?.focus(), 50);
    return () => clearTimeout(id);
  }, [open]);

  // Debounced search
  useEffect(() => {
    if (!open) return;
    if (query.trim().length < 2) {
      setResults([]);
      return;
    }
    const id = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await geocodeApi.search(query, 6);
        setResults(data.results || []);
      } catch (err) {
        setError(err.response?.data?.message || t("city.errorSearch"));
      } finally {
        setLoading(false);
      }
    }, DEBOUNCE_MS);
    return () => clearTimeout(id);
  }, [query, open, t]);

  // Esc pour fermer
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const handlePick = (r) => {
    onSelect({
      lat: r.lat,
      lng: r.lng,
      label: shortLabel(r.display_name),
      country_code: r.country_code,
    });
    onClose();
  };

  return (
    <div className="city-picker-backdrop" onClick={onClose}>
      <div className="city-picker" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
        <div className="city-picker-header">
          <h2>{t("city.title")}</h2>
          <button type="button" className="city-picker-close ghost" onClick={onClose} aria-label="Fermer">×</button>
        </div>
        <input
          ref={inputRef}
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t("city.placeholder")}
          autoComplete="off"
        />
        {error && <p className="error" style={{ marginTop: 12 }}>{error}</p>}
        <div className="city-picker-results">
          {loading && <p className="muted" style={{ padding: "12px 4px" }}>{t("city.searching")}</p>}
          {!loading && query.length >= 2 && results.length === 0 && !error && (
            <p className="muted" style={{ padding: "12px 4px" }}>{t("city.noResults")}</p>
          )}
          {results.map((r, i) => (
            <button
              key={`${r.lat},${r.lng},${i}`}
              type="button"
              className="city-picker-result"
              onClick={() => handlePick(r)}
            >
              <span className="city-picker-result-name">{shortLabel(r.display_name)}</span>
              <span className="city-picker-result-detail muted">{r.display_name}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// Nominatim renvoie souvent "Paris, Île-de-France, France métropolitaine, France"
// → on prend juste la 1ere et la derniere partie pour un libelle compact.
function shortLabel(displayName) {
  if (!displayName) return "";
  const parts = displayName.split(",").map((s) => s.trim()).filter(Boolean);
  if (parts.length <= 2) return parts.join(", ");
  return `${parts[0]}, ${parts[parts.length - 1]}`;
}
