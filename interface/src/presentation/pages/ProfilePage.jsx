import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../application/auth/AuthContext";
import { spotifyApi } from "../../infrastructure/api/spotify";
import { usersApi } from "../../infrastructure/api/users";
import { extractApiError } from "../utils/extractApiError";

export default function ProfilePage() {
  const { user, setUser, logout } = useAuth();
  const navigate = useNavigate();

  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ first_name: "", last_name: "", avatar_url: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Pre-remplit le formulaire d'edition quand on bascule en mode "editer".
  useEffect(() => {
    if (editing && user) {
      setForm({
        first_name: user.first_name,
        last_name: user.last_name,
        avatar_url: user.avatar_url ?? "",
      });
    }
  }, [editing, user]);

  // ---------- Edition profil ----------

  const update = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const onSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      // avatar_url vide -> on envoie null pour supprimer l'avatar
      const payload = {
        first_name: form.first_name,
        last_name: form.last_name,
        avatar_url: form.avatar_url.trim() === "" ? null : form.avatar_url.trim(),
      };
      const updated = await usersApi.updateProfile(payload);
      setUser(updated);
      setEditing(false);
    } catch (err) {
      setError(extractApiError(err, "Impossible de sauvegarder le profil"));
    } finally {
      setSaving(false);
    }
  };

  // ---------- Connexion Spotify ----------

  const onConnectSpotify = async () => {
    try {
      const { auth_url } = await spotifyApi.connect();
      window.location.href = auth_url;
    } catch (err) {
      setError(extractApiError(err, "Impossible de demarrer la connexion Spotify"));
    }
  };

  const onLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  if (!user) return null;

  return (
    <div className="profile-page">
      <header className="profile-header">
        <div className="avatar">
          {user.avatar_url ? (
            <img src={user.avatar_url} alt="Avatar" />
          ) : (
            <div className="avatar-placeholder">
              {user.first_name[0]}
              {user.last_name[0]}
            </div>
          )}
        </div>
        <div>
          <h1>
            {user.first_name} {user.last_name}
          </h1>
          <p className="muted">{user.email}</p>
        </div>
        <button className="ghost" onClick={onLogout}>
          Se deconnecter
        </button>
      </header>

      <section className="card">
        <div className="card-header">
          <h2>Informations</h2>
          {!editing && (
            <button onClick={() => setEditing(true)}>Modifier</button>
          )}
        </div>

        {editing ? (
          <form onSubmit={onSave} className="profile-form">
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
              URL de l'avatar (laisser vide pour supprimer)
              <input
                type="url"
                value={form.avatar_url}
                onChange={update("avatar_url")}
                placeholder="https://..."
              />
            </label>
            {error && <p className="error">{error}</p>}
            <div className="form-actions">
              <button type="button" className="ghost" onClick={() => setEditing(false)}>
                Annuler
              </button>
              <button type="submit" disabled={saving}>
                {saving ? "Sauvegarde..." : "Enregistrer"}
              </button>
            </div>
          </form>
        ) : (
          error && <p className="error">{error}</p>
        )}
      </section>

      <section className="card">
        <div className="card-header">
          <h2>Spotify</h2>
        </div>
        <p className="muted">
          Connecte ton compte Spotify pour qu'Evenoola te recommande des evenements selon tes
          artistes et genres preferes.
        </p>
        <button onClick={onConnectSpotify}>Connecter Spotify</button>
      </section>
    </div>
  );
}
