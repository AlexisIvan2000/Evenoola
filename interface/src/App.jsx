import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./application/auth/AuthContext";
import { RequireAuth } from "./presentation/components/RequireAuth";
import LoginPage from "./presentation/pages/LoginPage";
import ProfilePage from "./presentation/pages/ProfilePage";
import RegisterPage from "./presentation/pages/RegisterPage";
import SpotifyConnectedPage from "./presentation/pages/SpotifyConnectedPage";
import "./App.css";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/profile"
            element={
              <RequireAuth>
                <ProfilePage />
              </RequireAuth>
            }
          />
          <Route
            path="/spotify/connected"
            element={
              <RequireAuth>
                <SpotifyConnectedPage />
              </RequireAuth>
            }
          />
          <Route path="/" element={<Navigate to="/profile" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
