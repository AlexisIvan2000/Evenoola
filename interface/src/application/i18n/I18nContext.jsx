import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { translations } from "./translations";

const STORAGE_KEY = "evenoola.locale";
const DEFAULT_LOCALE = "FR";
export const SUPPORTED_LOCALES = ["FR", "EN"];

const I18nContext = createContext(null);

export function I18nProvider({ children }) {
  const [locale, setLocaleState] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return SUPPORTED_LOCALES.includes(stored) ? stored : DEFAULT_LOCALE;
    } catch {
      return DEFAULT_LOCALE;
    }
  });

  // Synchronise <html lang="..."> a chaque changement de locale.
  useEffect(() => {
    document.documentElement.lang = locale.toLowerCase();
  }, [locale]);

  const setLocale = useCallback((next) => {
    if (!SUPPORTED_LOCALES.includes(next)) return;
    setLocaleState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* localStorage indisponible (mode prive) -- on continue, juste sans persistance */
    }
  }, []);

  // t("login.title") -> string. t("events.matchScore", { score: 87 }) -> "87% match".
  // Fallback sur la cle si la traduction manque.
  const t = useCallback(
    (key, vars) => {
      const dict = translations[locale] || translations[DEFAULT_LOCALE];
      let value = key.split(".").reduce((acc, k) => acc?.[k], dict);
      if (typeof value !== "string") return key;
      if (vars) {
        for (const [k, v] of Object.entries(vars)) {
          value = value.replaceAll(`{${k}}`, String(v));
        }
      }
      return value;
    },
    [locale],
  );

  const value = { locale, setLocale, t };

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n doit etre utilise dans <I18nProvider>");
  return ctx;
}
