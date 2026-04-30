import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../application/auth/AuthContext";

export function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="loading">Chargement...</div>;
  }
  if (!user) {
    // On memorise d'ou venait l'user pour le rediriger apres login (option future).
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return children;
}
