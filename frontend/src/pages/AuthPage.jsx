import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function AuthPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const [mode, setMode] = useState("login");
  const [nom, setNom] = useState("");
  const [prenom, setPrenom] = useState("");
  const [email, setEmail] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "login") {
        await login(email, motDePasse);
      } else {
        await register(nom, prenom, email, motDePasse);
      }
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <h1>{mode === "login" ? "Connexion" : "Créer un compte"}</h1>

      <form onSubmit={handleSubmit}>
        {mode === "register" && (
          <>
            <label>
              Prénom
              <input value={prenom} onChange={(e) => setPrenom(e.target.value)} required maxLength={100} />
            </label>
            <label>
              Nom
              <input value={nom} onChange={(e) => setNom(e.target.value)} required maxLength={100} />
            </label>
          </>
        )}

        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>

        <label>
          Mot de passe
          <input
            type="password"
            value={motDePasse}
            onChange={(e) => setMotDePasse(e.target.value)}
            required
            minLength={mode === "register" ? 8 : undefined}
          />
          {mode === "register" && <small>8 caractères minimum</small>}
        </label>

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={loading}>
          {loading ? "Chargement..." : mode === "login" ? "Se connecter" : "S'inscrire"}
        </button>
      </form>

      <button type="button" className="link" onClick={() => setMode(mode === "login" ? "register" : "login")}>
        {mode === "login" ? "Pas de compte ? Inscris-toi" : "Déjà un compte ? Connecte-toi"}
      </button>
    </div>
  );
}