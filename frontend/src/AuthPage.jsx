import { useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const gold = "#c9a227";
const goldDim = "rgba(201,162,39,0.15)";

export default function AuthPage({ onSuccess }) {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    confirm: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (k, v) => {
    setForm((p) => ({ ...p, [k]: v }));
    setError(null);
  };

  const handleSubmit = async () => {
    // Validation basique
    if (!form.email || !form.password) {
      setError("Tous les champs sont obligatoires.");
      return;
    }
    if (mode === "register") {
      if (!form.full_name) {
        setError("Le nom complet est obligatoire.");
        return;
      }
      if (form.password !== form.confirm) {
        setError("Les mots de passe ne correspondent pas.");
        return;
      }
      if (form.password.length < 6) {
        setError("Le mot de passe doit faire au moins 6 caractères.");
        return;
      }
    }

    setLoading(true);
    setError(null);
    try {
      const endpoint = mode === "login" ? "/login" : "/register";
      const body =
        mode === "login"
          ? { email: form.email, password: form.password }
          : {
              full_name: form.full_name,
              email: form.email,
              password: form.password,
            };

      const res = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Erreur serveur");

      if (mode === "login") {
        // Connexion : stocker le token et appeler onSuccess
        localStorage.setItem("ap_token", data.access_token);
        localStorage.setItem("ap_user", JSON.stringify(data.user));
        onSuccess(data.user);
      } else {
        // Inscription réussie : basculer vers login et vider le formulaire
        setMode("login");
        setForm({
          full_name: "",
          email: "",
          password: "",
          confirm: "",
        });
        // Optionnel : afficher un message de succès (pas demandé)
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={s.page}>
      {/* Glow background */}
      <div style={s.glow1} />
      <div style={s.glow2} />

      <div style={s.card}>
        {/* Logo */}
        <div style={s.logo}>
          <span style={s.logoMark}>◈</span>
          <span style={s.logoText}>
            AutoPredict <span style={s.logoTN}>TN</span>
          </span>
        </div>

        {/* Tabs */}
        <div style={s.tabs}>
          <button
            onClick={() => {
              setMode("login");
              setError(null);
            }}
            style={{ ...s.tab, ...(mode === "login" ? s.tabActive : {}) }}
          >
            Connexion
          </button>
          <button
            onClick={() => {
              setMode("register");
              setError(null);
            }}
            style={{ ...s.tab, ...(mode === "register" ? s.tabActive : {}) }}
          >
            Inscription
          </button>
        </div>

        {/* Subtitle */}
        <p style={s.subtitle}>
          {mode === "login"
            ? "Bienvenue ! Connectez-vous pour continuer."
            : "Créez votre compte gratuitement."}
        </p>

        {/* Fields */}
        <div style={s.fields}>
          {mode === "register" && (
            <div style={s.fieldGroup}>
              <label style={s.label}>Nom complet</label>
              <input
                type="text"
                placeholder="Ahmed Ben Ali"
                value={form.full_name}
                onChange={(e) => handleChange("full_name", e.target.value)}
                style={s.input}
              />
            </div>
          )}
          <div style={s.fieldGroup}>
            <label style={s.label}>Adresse e-mail</label>
            <input
              type="email"
              placeholder="email@exemple.com"
              value={form.email}
              onChange={(e) => handleChange("email", e.target.value)}
              style={s.input}
            />
          </div>
          <div style={s.fieldGroup}>
            <label style={s.label}>Mot de passe</label>
            <input
              type="password"
              placeholder="••••••••"
              value={form.password}
              onChange={(e) => handleChange("password", e.target.value)}
              style={s.input}
            />
          </div>
          {mode === "register" && (
            <div style={s.fieldGroup}>
              <label style={s.label}>Confirmer le mot de passe</label>
              <input
                type="password"
                placeholder="••••••••"
                value={form.confirm}
                onChange={(e) => handleChange("confirm", e.target.value)}
                style={s.input}
              />
            </div>
          )}
        </div>

        {error && <div style={s.errBox}>⚠ {error}</div>}

        <button onClick={handleSubmit} disabled={loading} style={s.btn}>
          {loading
            ? "⟳ Chargement..."
            : mode === "login"
              ? "🔑 Se connecter"
              : "🚀 Créer mon compte"}
        </button>

        <p style={s.switchTxt}>
          {mode === "login" ? "Pas encore de compte ? " : "Déjà inscrit ? "}
          <span
            style={s.switchLink}
            onClick={() => {
              setMode(mode === "login" ? "register" : "login");
              setError(null);
            }}
          >
            {mode === "login" ? "S'inscrire" : "Se connecter"}
          </span>
        </p>
      </div>
    </div>
  );
}

const s = {
  page: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "24px",
    position: "relative",
    overflow: "hidden",
    background: "linear-gradient(135deg,#0b1624,#02060d)",
  },
  glow1: {
    position: "fixed",
    top: "-20%",
    left: "-10%",
    width: "600px",
    height: "600px",
    borderRadius: "50%",
    background:
      "radial-gradient(circle,rgba(201,162,39,0.07)0%,transparent 65%)",
    pointerEvents: "none",
  },
  glow2: {
    position: "fixed",
    bottom: "-20%",
    right: "-10%",
    width: "500px",
    height: "500px",
    borderRadius: "50%",
    background:
      "radial-gradient(circle,rgba(132, 142, 154, 0.12)0%,transparent 65%)",
    pointerEvents: "none",
  },
  card: {
    position: "relative",
    zIndex: 10,
    width: "100%",
    maxWidth: "440px",
    background: "rgba(8,18,32,0.92)",
    border: `1px solid rgba(201,162,39,0.22)`,
    borderRadius: "28px",
    padding: "44px 40px",
    backdropFilter: "blur(28px)",
    boxShadow: "0 40px 80px rgba(0,0,0,0.55)",
  },
  logo: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "10px",
    marginBottom: "28px",
  },
  logoMark: { fontSize: "22px", color: gold },
  logoText: {
    fontFamily: "'Bebas Neue',sans-serif",
    fontSize: "22px",
    letterSpacing: "3px",
    color: "#e8dcc8",
  },
  logoTN: { color: gold },
  tabs: {
    display: "flex",
    background: "rgba(255,255,255,0.03)",
    borderRadius: "12px",
    padding: "4px",
    marginBottom: "20px",
    border: `1px solid ${goldDim}`,
  },
  tab: {
    flex: 1,
    padding: "9px",
    border: "none",
    borderRadius: "9px",
    background: "transparent",
    color: "rgba(232,220,200,0.4)",
    fontSize: "14px",
    fontWeight: "500",
    cursor: "pointer",
    transition: "all 0.2s",
    fontFamily: "'DM Sans',sans-serif",
  },
  tabActive: { background: goldDim, color: gold, fontWeight: "700" },
  subtitle: {
    textAlign: "center",
    fontSize: "13px",
    color: "rgba(232,220,200,0.42)",
    marginBottom: "26px",
    letterSpacing: "0.3px",
  },
  fields: {
    display: "flex",
    flexDirection: "column",
    gap: "14px",
    marginBottom: "16px",
  },
  fieldGroup: { display: "flex", flexDirection: "column", gap: "6px" },
  label: {
    fontSize: "10px",
    letterSpacing: "1.5px",
    textTransform: "uppercase",
    color: gold,
    opacity: 0.72,
  },
  input: {
    width: "100%",
    padding: "12px 14px",
    background: "rgba(255,255,255,0.04)",
    border: `1px solid rgba(201,162,39,0.2)`,
    borderRadius: "11px",
    color: "#e8dcc8",
    fontSize: "14px",
    fontFamily: "'DM Sans',sans-serif",
    outline: "none",
    boxSizing: "border-box",
    transition: "border-color 0.2s",
  },
  errBox: {
    padding: "11px 14px",
    background: "rgba(255,68,85,0.07)",
    border: "1px solid rgba(255,68,85,0.22)",
    borderRadius: "10px",
    fontSize: "13px",
    color: "#ff8899",
    marginBottom: "14px",
  },
  btn: {
    width: "100%",
    padding: "14px",
    background: `linear-gradient(135deg,${gold},#9e7b16)`,
    border: "none",
    borderRadius: "12px",
    color: "#04090f",
    fontSize: "15px",
    fontWeight: "700",
    cursor: "pointer",
    boxShadow: "0 10px 28px rgba(201,162,39,0.3)",
    transition: "all 0.25s",
    fontFamily: "'DM Sans',sans-serif",
    marginBottom: "18px",
  },
  switchTxt: {
    textAlign: "center",
    fontSize: "13px",
    color: "rgba(232,220,200,0.35)",
  },
  switchLink: {
    color: gold,
    cursor: "pointer",
    fontWeight: "600",
    textDecoration: "underline",
  },
};
