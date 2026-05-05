import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../application/auth/AuthContext";
import { useI18n } from "../../application/i18n/I18nContext";
import { spotifyApi } from "../../infrastructure/api/spotify";
import { usersApi } from "../../infrastructure/api/users";
import { extractApiError } from "../utils/extractApiError";

export default function ProfilePage() {
  const { user, setUser, logout } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();

  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ first_name: "", last_name: "", avatar_url: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const [artists, setArtists] = useState(null);
  const [artistsLoading, setArtistsLoading] = useState(true);
  const [artistsError, setArtistsError] = useState(null);

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

  // Charge les top artists au montage. Spotify est connecte par definition (login = Spotify).
  useEffect(() => {
    spotifyApi
      .topArtists({ time_range: "medium_term", limit: 12 })
      .then((data) => setArtists(data.artists))
      .catch((err) => setArtistsError(extractApiError(err, t("profile.errorArtists"))))
      .finally(() => setArtistsLoading(false));
  }, [t]);

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
      setError(extractApiError(err, t("profile.errorSave")));
    } finally {
      setSaving(false);
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
          {t("profile.logout")}
        </button>
      </header>

      <section className="card">
        <div className="card-header">
          <h2>{t("profile.sectionInfo")}</h2>
          {!editing && (
            <button onClick={() => setEditing(true)}>{t("profile.edit")}</button>
          )}
        </div>

        {editing ? (
          <form onSubmit={onSave} className="profile-form">
            <div className="form-row">
              <label>
                {t("profile.firstName")}
                <input value={form.first_name} onChange={update("first_name")} required />
              </label>
              <label>
                {t("profile.lastName")}
                <input value={form.last_name} onChange={update("last_name")} required />
              </label>
            </div>
            <label>
              {t("profile.avatarUrl")}
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
                {t("profile.cancel")}
              </button>
              <button type="submit" disabled={saving}>
                {saving ? t("profile.saving") : t("profile.save")}
              </button>
            </div>
          </form>
        ) : (
          error && <p className="error">{error}</p>
        )}
      </section>

      <section className="card">
        <div className="card-header">
          <h2>{t("profile.sectionArtists")}</h2>
        </div>
        {artistsLoading ? (
          <div className="artists-grid">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="artist-skeleton">
                <div className="skeleton-circle" />
                <div className="skeleton-line" />
              </div>
            ))}
          </div>
        ) : artistsError ? (
          <p className="error">{artistsError}</p>
        ) : artists?.length ? (
          <div className="artists-grid">
            {artists.map((a, i) => (
              <a
                key={a.id}
                className="artist-card"
                href={a.spotify_url}
                target="_blank"
                rel="noreferrer"
                style={{ "--i": i }}
              >
                <div className="artist-card-img-wrap">
                  {a.image_url && <img src={a.image_url} alt={a.name} />}
                </div>
                <div className="artist-name">{a.name}</div>
                {a.genres?.[0] && <div className="artist-genre muted">{a.genres[0]}</div>}
              </a>
            ))}
          </div>
        ) : (
          <p className="muted">{t("profile.artistsEmpty")}</p>
        )}
      </section>
    </div>
  );
}
