import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../application/auth/AuthContext";
import { extractApiError } from "../utils/extractApiError";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
  });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const update = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const onSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(form);
      navigate("/profile", { replace: true });
    } catch (err) {
      setError(extractApiError(err, "Echec de l'inscription"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Inscription</h1>
        <form onSubmit={onSubmit} className="auth-form">
          <div className="form-row">
            <label>
              Prenom
              <input value={form.first_name} onChange={update("first_name")} required />
            </label>
            <label>
              Nom
              <input value={form.last_name} onChange={update("last_name")} required />
            </label>
          </div>
          <label>
            Email
            <input
              type="email"
              value={form.email}
              onChange={update("email")}
              required
              autoComplete="email"
            />
          </label>
          <label>
            Mot de passe
            <input
              type="password"
              value={form.password}
              onChange={update("password")}
              required
              autoComplete="new-password"
            />
            <small>Min. 8 caracteres, 1 majuscule, 1 minuscule, 1 caractere special.</small>
          </label>
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={submitting}>
            {submitting ? "Creation..." : "Creer mon compte"}
          </button>
        </form>
        <p className="auth-switch">
          Deja un compte ? <Link to="/login">Se connecter</Link>
        </p>
      </div>
    </div>
  );
}
