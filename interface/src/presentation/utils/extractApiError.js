// Convertit une erreur axios issue de l'API Flask en message utilisateur lisible.
// Le backend renvoie :
//   - { error: "validation_error", details: [{ loc, msg, ... }, ...] } pour Pydantic
//   - { error: "...", message: "..." } pour les erreurs metier (UserAlreadyExists, ...)
export function extractApiError(err, fallback = "Une erreur est survenue") {
  const data = err?.response?.data;
  if (!data) return fallback;

  if (data.error === "validation_error" && Array.isArray(data.details)) {
    return data.details.map((d) => d.msg).filter(Boolean).join(" - ") || fallback;
  }
  if (data.message) return data.message;
  if (typeof data.error === "string") return data.error;
  return fallback;
}
