import { useCallback, useEffect, useRef, useState } from "react";

const TIMEOUT_MS = 8000;
const CACHE_MAX_AGE_MS = 30 * 60 * 1000; // 30 min : evite de re-prompter trop souvent
const STORAGE_KEY = "evenoola.location_override";

/**
 * Hook de localisation avec 2 sources, dans l'ordre de priorite :
 *   1. Override choisi par l'user (ville saisie via CityPicker, persiste localStorage)
 *   2. Browser geolocation (prompt natif)
 *
 * Statut renvoye :
 *   - "override"    : on utilise la ville choisie
 *   - "pending"     : geo browser en attente
 *   - "granted"     : geo browser OK
 *   - "denied"      : user a refuse OU timeout 8s
 *   - "unavailable" : navigator.geolocation absent
 *
 * Le caller obtient { coords, label } unifies, peu importe la source, et peut
 * appeler `setOverride(city)` / `clearOverride()` pour basculer.
 */
export function useGeolocation() {
  const [override, setOverrideState] = useState(() => readOverride());
  const [browserState, setBrowserState] = useState({ status: "pending", coords: null, error: null });
  const timeoutRef = useRef(null);

  const requestBrowserGeo = useCallback(() => {
    if (!("geolocation" in navigator)) {
      setBrowserState({ status: "unavailable", coords: null, error: "Geolocation API non supportee" });
      return;
    }
    setBrowserState({ status: "pending", coords: null, error: null });

    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      setBrowserState((s) => (s.status === "pending" ? { status: "denied", coords: null, error: "timeout" } : s));
    }, TIMEOUT_MS + 500);

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        setBrowserState({
          status: "granted",
          coords: { lat: pos.coords.latitude, lng: pos.coords.longitude },
          error: null,
        });
      },
      (err) => {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        setBrowserState({ status: "denied", coords: null, error: err.message });
      },
      { timeout: TIMEOUT_MS, maximumAge: CACHE_MAX_AGE_MS, enableHighAccuracy: false },
    );
  }, []);

  // Tente la geo browser au montage SAUF si on a deja un override.
  useEffect(() => {
    if (override) return;
    requestBrowserGeo();
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [override, requestBrowserGeo]);

  const setOverride = useCallback((city) => {
    // city : { lat, lng, label, country_code? }
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(city));
    } catch { /* mode prive */ }
    setOverrideState(city);
  }, []);

  const clearOverride = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch { /* */ }
    setOverrideState(null);
    requestBrowserGeo();
  }, [requestBrowserGeo]);

  // Resolution finale.
  // IMPORTANT : on renvoie l'objet `override` ou `browserState.coords` SANS le recreer,
  // sinon la reference change a chaque render et boucle dans les useEffect des consumers.
  if (override) {
    return {
      status: "override",
      coords: override,           // stable ref (state)
      label: override.label,
      override,
      setOverride,
      clearOverride,
      retry: requestBrowserGeo,
    };
  }
  return {
    status: browserState.status,
    coords: browserState.coords,  // stable ref (state)
    label: null,
    override: null,
    setOverride,
    clearOverride,
    retry: requestBrowserGeo,
  };
}

function readOverride() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (typeof parsed.lat === "number" && typeof parsed.lng === "number") return parsed;
    return null;
  } catch {
    return null;
  }
}
