import { useState, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const gold = "#c9a227";
const goldDim = "rgba(201,162,39,0.15)";

// ─── DATA ────────────────────────────────────────────────────────────────────
// Fallback defaults (overridden by /options endpoint)
const DEFAULT_OPTIONS = {
  Marque: [],
  Energie: [],
  Boite_vitesse: [],
  Transmission: [],
  Carrosserie: [],
  Gouvernorat: [],
  Couleur_exterieure: [],
  Couleur_interieure: [],
  Sellerie: [],
};

const selectFields = [
  "Marque", "Energie", "Boite_vitesse", "Transmission",
  "Carrosserie", "Gouvernorat", "Couleur_exterieure",
  "Couleur_interieure", "Sellerie",
];

const initialForm = {
  Marque: "",
  Kilometrage: "",
  Energie: "",
  Boite_vitesse: "",
  Puissance_fiscale: "",
  Puissance_ch: "",
  Transmission: "",
  Carrosserie: "",
  Gouvernorat: "",
  Couleur_exterieure: "",
  Couleur_interieure: "",
  Sellerie: "",
  Nombre_places: "",
  Nombre_portes: "",
  Cylindree: "",
  age_voiture: "",
};

const steps = [
  {
    id: 1,
    title: "Identité",
    icon: "🚗",
    fields: [
      "Marque",
      "Carrosserie",
      "Energie",
      "Boite_vitesse",
      "Transmission",
    ],
  },
  {
    id: 2,
    title: "Technique",
    icon: "⚙️",
    fields: [
      "Puissance_fiscale",
      "Puissance_ch",
      "Cylindree",
      "Nombre_places",
      "Nombre_portes",
    ],
  },
  {
    id: 3,
    title: "Historique",
    icon: "📋",
    fields: ["age_voiture", "Kilometrage", "Gouvernorat"],
  },
  {
    id: 4,
    title: "Esthétique",
    icon: "✨",
    fields: ["Couleur_exterieure", "Couleur_interieure", "Sellerie"],
  },
];

const fieldLabels = {
  Marque: "Marque",
  Kilometrage: "Kilométrage (km)",
  Energie: "Type d'énergie",
  Boite_vitesse: "Boîte de vitesses",
  Puissance_fiscale: "Puissance fiscale (CV)",
  Puissance_ch: "Puissance (ch)",
  Transmission: "Transmission",
  Carrosserie: "Carrosserie",
  Gouvernorat: "Gouvernorat",
  Couleur_exterieure: "Couleur extérieure",
  Couleur_interieure: "Couleur intérieure",
  Sellerie: "Sellerie",
  Nombre_places: "Nombre de places",
  Nombre_portes: "Nombre de portes",
  Cylindree: "Cylindrée (cc)",
  age_voiture: "Âge du véhicule (ans)",
};



const numericFields = [
  "Kilometrage",
  "Puissance_fiscale",
  "Puissance_ch",
  "Nombre_places",
  "Nombre_portes",
  "Cylindree",
  "age_voiture",
];

// ─── BACKGROUND COMMUN ───────────────────────────────────────────────────────
function AnimatedBg({ particles }) {
  return (
    <div style={s.bg}>
      <div style={s.bgGrad1} />
      <div style={s.bgGrad2} />
      <div style={s.bgGrad3} />
      <div style={s.grid} />
      {particles.map((p) => (
        <div
          key={p.id}
          style={{
            ...s.particle,
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            animationDuration: `${p.speed}s`,
            animationDelay: `${p.delay}s`,
          }}
        />
      ))}
    </div>
  );
}

// ─── PAGE AUTH (Login / Sign Up) ─────────────────────────────────────────────
function AuthPage({ onSuccess }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({
    nom: "",
    prenom: "",
    email: "",
    password: "",
    confirm: "",
    telephone: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showPass, setShowPass] = useState(false);
  const [showConf, setShowConf] = useState(false);
  const [success, setSuccess] = useState(null);

  const change = (k, v) => {
    setForm((p) => ({ ...p, [k]: v }));
    setError(null);
  };

  const switchMode = (m) => {
    setMode(m);
    setError(null);
    setSuccess(null);
    setForm({
      nom: "",
      prenom: "",
      email: "",
      password: "",
      confirm: "",
      telephone: "",
    });
  };

  const submit = async () => {
    if (!form.email || !form.password) {
      setError("Email et mot de passe obligatoires.");
      return;
    }
    if (mode === "register") {
      if (!form.nom || !form.prenom) {
        setError("Nom et prénom obligatoires.");
        return;
      }
      if (form.password !== form.confirm) {
        setError("Les mots de passe ne correspondent pas.");
        return;
      }
      if (form.password.length < 6) {
        setError("Mot de passe : 6 caractères minimum.");
        return;
      }
    }
    setLoading(true);
    setError(null);
    try {
      const endpoint = mode === "login" ? "/auth/login" : "/auth/register";
      const body =
        mode === "login"
          ? { email: form.email, password: form.password }
          : {
              full_name: `${form.prenom} ${form.nom}`,
              email: form.email,
              password: form.password,
              telephone: form.telephone || null,
            };
      const res = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Erreur serveur");
      if (mode === "register") {
        switchMode("login");
        setTimeout(
          () =>
            setSuccess(
              "✅ Compte créé avec succès ! Connectez-vous maintenant.",
            ),
          50,
        );
      } else {
        localStorage.setItem("ap_token", data.access_token);
        localStorage.setItem("ap_user", JSON.stringify(data.user));
        onSuccess(data.user);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={s.authPage}>
      <div style={s.bgGrad1} />
      <div style={s.bgGrad2} />
      <div style={s.bgGrad3} />
      <div style={s.grid} />
      <div style={s.carSilhouette}>
        <svg viewBox="0 0 900 260" style={{ width: "100%", height: "100%" }}>
          <path
            d="M140,190 L110,190 Q72,190 62,162 L44,112 Q38,92 58,87 L175,78 Q218,52 325,47 L488,47 Q572,47 624,78 L732,87 Q758,92 762,112 L752,162 Q742,190 704,190 L672,190 Q667,222 640,222 Q613,222 608,190 L222,190 Q217,222 190,222 Q163,222 158,190 Z"
            fill={gold}
            opacity="0.04"
          />
          <ellipse
            cx="190"
            cy="196"
            rx="32"
            ry="32"
            fill={gold}
            opacity="0.04"
          />
          <ellipse
            cx="630"
            cy="196"
            rx="32"
            ry="32"
            fill={gold}
            opacity="0.04"
          />
        </svg>
      </div>

      <div style={s.authCard} onKeyDown={(e) => e.key === "Enter" && submit()}>
        <div style={s.authLogo}>
          <span style={{ fontSize: "22px", color: gold }}>◈</span>
          <span
            style={{
              fontFamily: "'Bebas Neue',sans-serif",
              fontSize: "22px",
              letterSpacing: "3px",
              color: "#e8dcc8",
            }}
          >
            AutoPredict <span style={{ color: gold }}>TN</span>
          </span>
        </div>

        <div style={s.authBadge}>
          {mode === "login" ? "🔑 Espace membre" : "🚀 Créer un compte"}
        </div>

        <div style={s.authTabs}>
          <button
            onClick={() => switchMode("login")}
            style={{
              ...s.authTab,
              ...(mode === "login" ? s.authTabActive : {}),
            }}
          >
            Connexion
          </button>
          <button
            onClick={() => switchMode("register")}
            style={{
              ...s.authTab,
              ...(mode === "register" ? s.authTabActive : {}),
            }}
          >
            Inscription
          </button>
        </div>

        <p style={s.authSub}>
          {mode === "login"
            ? "Bienvenue ! Connectez-vous pour continuer."
            : "Créez votre compte gratuit en quelques secondes."}
        </p>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "13px",
            marginBottom: "14px",
          }}
        >
          {mode === "register" && (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "12px",
              }}
            >
              <div style={s.fg}>
                <label style={s.lbl}>Nom</label>
                <input
                  type="text"
                  placeholder="Ben Ali"
                  value={form.nom}
                  onChange={(e) => change("nom", e.target.value)}
                  style={s.inp}
                />
              </div>
              <div style={s.fg}>
                <label style={s.lbl}>Prénom</label>
                <input
                  type="text"
                  placeholder="Ahmed"
                  value={form.prenom}
                  onChange={(e) => change("prenom", e.target.value)}
                  style={s.inp}
                />
              </div>
            </div>
          )}
          <div style={s.fg}>
            <label style={s.lbl}>Adresse e-mail</label>
            <div style={{ position: "relative" }}>
              <span style={s.icoL}>✉</span>
              <input
                type="email"
                placeholder="email@exemple.com"
                value={form.email}
                onChange={(e) => change("email", e.target.value)}
                style={{ ...s.inp, paddingLeft: "34px" }}
              />
            </div>
          </div>
          {mode === "register" && (
            <div style={s.fg}>
              <label style={s.lbl}>
                Téléphone{" "}
                <span style={{ fontSize: "9px", opacity: 0.5 }}>
                  (optionnel)
                </span>
              </label>
              <div style={{ position: "relative" }}>
                <span style={s.icoL}>📱</span>
                <input
                  type="tel"
                  placeholder="+216 XX XXX XXX"
                  value={form.telephone}
                  onChange={(e) => change("telephone", e.target.value)}
                  style={{ ...s.inp, paddingLeft: "34px" }}
                />
              </div>
            </div>
          )}
          <div style={s.fg}>
            <label style={s.lbl}>Mot de passe</label>
            <div style={{ position: "relative" }}>
              <span style={s.icoL}>🔒</span>
              <input
                type={showPass ? "text" : "password"}
                placeholder="••••••••"
                value={form.password}
                onChange={(e) => change("password", e.target.value)}
                style={{ ...s.inp, paddingLeft: "34px", paddingRight: "38px" }}
              />
              <button
                type="button"
                onClick={() => setShowPass((p) => !p)}
                style={s.eyeBtn}
              >
                {showPass ? "🙈" : "👁"}
              </button>
            </div>
          </div>
          {mode === "register" && (
            <div style={s.fg}>
              <label style={s.lbl}>Confirmer le mot de passe</label>
              <div style={{ position: "relative" }}>
                <span style={s.icoL}>🔒</span>
                <input
                  type={showConf ? "text" : "password"}
                  placeholder="••••••••"
                  value={form.confirm}
                  onChange={(e) => change("confirm", e.target.value)}
                  style={{
                    ...s.inp,
                    paddingLeft: "34px",
                    paddingRight: "38px",
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowConf((p) => !p)}
                  style={s.eyeBtn}
                >
                  {showConf ? "🙈" : "👁"}
                </button>
              </div>
            </div>
          )}
        </div>

        {success && (
          <div
            style={{
              padding: "11px 14px",
              background: "rgba(0,255,136,0.07)",
              border: "1px solid rgba(0,255,136,0.25)",
              borderRadius: "10px",
              fontSize: "13px",
              color: "#00ff88",
              marginBottom: "14px",
            }}
          >
            {success}
          </div>
        )}
        {error && <div style={s.errBox}>⚠ {error}</div>}

        <button
          onClick={submit}
          disabled={loading}
          style={{ ...s.authBtn, opacity: loading ? 0.75 : 1 }}
        >
          {loading
            ? "⟳ Chargement..."
            : mode === "login"
              ? "🔑 Se connecter"
              : "🚀 Créer mon compte"}
        </button>

        <p
          style={{
            textAlign: "center",
            fontSize: "13px",
            color: "rgba(232,220,200,0.35)",
            marginBottom: "20px",
          }}
        >
          {mode === "login" ? "Pas encore de compte ? " : "Déjà inscrit ? "}
          <span
            style={{
              color: gold,
              cursor: "pointer",
              fontWeight: "600",
              textDecoration: "underline",
            }}
            onClick={() => switchMode(mode === "login" ? "register" : "login")}
          >
            {mode === "login" ? "S'inscrire gratuitement" : "Se connecter"}
          </span>
        </p>

        <div
          style={{
            textAlign: "center",
            fontSize: "10px",
            color: "rgba(232,220,200,0.2)",
            letterSpacing: "1px",
            textTransform: "uppercase",
            borderTop: `1px solid ${goldDim}`,
            paddingTop: "16px",
          }}
        >
          🇹🇳 Marché automobile tunisien · Gratuit · Sécurisé
        </div>
      </div>
    </div>
  );
}

// ─── HEADER ──────────────────────────────────────────────────────────────────
function Header({ page, onNav, apiStatus, user, onLogout }) {
  return (
    <header style={s.header}>
      <div style={s.headerInner}>
        <div style={s.logo} onClick={() => onNav("home")}>
          <span style={s.logoMark}>◈</span>
          <span style={s.logoText}>
            AutoPredict <span style={s.logoTN}>TN</span>
          </span>
        </div>
        <nav style={s.nav}>
          <button
            onClick={() => onNav("home")}
            style={{ ...s.navBtn, ...(page === "home" ? s.navBtnActive : {}) }}
          >
            Accueil
          </button>
          <button
            onClick={() => onNav("predict")}
            style={{
              ...s.navBtn,
              ...(page === "predict" ? s.navBtnActive : {}),
            }}
          >
            Prédiction
          </button>
        </nav>
        <div style={s.apiPill}>
          <span
            style={{
              ...s.dot,
              background:
                apiStatus === "online"
                  ? "#00ff88"
                  : apiStatus === "offline"
                    ? "#ff4455"
                    : "#ffaa00",
            }}
          />
          <span style={s.dotLabel}>
            {apiStatus === "online"
              ? "API en ligne"
              : apiStatus === "offline"
                ? "API hors ligne"
                : "Connexion..."}
          </span>
        </div>
        {user && (
          <div style={s.userArea}>
            <span style={s.userAvatar}>
              {(user.prenom || user.full_name || "U")[0].toUpperCase()}
            </span>
            <span style={s.userName}>
              {user.prenom ? `${user.prenom} ${user.nom}` : user.full_name}
            </span>
            <button onClick={onLogout} style={s.logoutBtn}>
              Déconnexion
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

// ─── HOME PAGE (avec nouvelle section "Nos véhicules en vedette") ───────────
function HomePage({ onStart }) {
  const stats = [
    { value: "50K+", label: "Véhicules analysés" },
    { value: "94%", label: "Précision du modèle" },
    { value: "24", label: "Gouvernorats couverts" },
    { value: "2s", label: "Temps de réponse" },
  ];

  const vehicules = [
    {
      marque: "Toyota",
      modele: "Corolla",
      prix: "22 500",
      annee: "2022",
      kilometrage: "30 000",
      energie: "Hybride",
      image:
        "https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80",
    },
    {
      marque: "Volkswagen",
      modele: "Golf",
      prix: "18 900",
      annee: "2021",
      kilometrage: "45 000",
      energie: "Essence",
      image:
        "https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80",
    },
    {
      marque: "Peugeot",
      modele: "3008",
      prix: "26 300",
      annee: "2023",
      kilometrage: "12 000",
      energie: "Diesel",
      image:
        "https://images.unsplash.com/photo-1555215695-3004980ad54e?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80",
    },
    {
      marque: "Renault",
      modele: "Clio",
      prix: "14 200",
      annee: "2020",
      kilometrage: "58 000",
      energie: "Essence",
      image:
        "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80",
    },
  ];

  return (
    <div>
      {/* Section Hero */}
      <section style={s.heroSection}>
        <div style={s.heroBackground}></div>
        <div style={s.heroOverlay}></div>
        <div style={s.heroContent}>
          <div style={s.badge}>
            🏆 Meilleur outil d'estimation automobile en Tunisie
          </div>
          <h1 style={s.heroTitle}>
            Découvrez la Vraie
            <br />
            <span style={s.heroGold}>Valeur de Votre</span>
            <br />
            Voiture d'Occasion
          </h1>
          <p style={s.heroDesc}>
            Notre intelligence artificielle analyse{" "}
            <strong style={{ color: "#e8dcc8" }}>17 critères</strong> de votre
            véhicule pour vous donner une estimation précise basée sur le marché
            tunisien en temps réel.
          </p>
          <div style={s.heroBtns}>
            <button onClick={onStart} style={s.ctaPrimary}>
              <span>🚗</span>Entrer les données de votre voiture
              <span style={s.ctaArrow}>→</span>
            </button>
            <span style={s.ctaNote}>
              Gratuit · Instantané · Sans inscription
            </span>
          </div>
        </div>
      </section>

      {/* Section Statistiques */}
      <section style={s.statsSection}>
        <div style={s.statsGrid}>
          {stats.map((st, i) => (
            <div key={i} style={s.statItem}>
              <div style={s.statValue}>{st.value}</div>
              <div style={s.statLabel}>{st.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Nouvelle section : Véhicules en vedette */}
      <section style={s.showcaseSection}>
        <div style={s.secHead}>
          <span style={s.secTag}>Nos véhicules en vedette</span>
          <h2 style={s.secTitle}>
            Découvrez une sélection <br /> de voitures d'occasion
          </h2>
        </div>
        <div style={s.showcaseGrid}>
          {vehicules.map((v, i) => (
            <div
              key={i}
              style={{ ...s.showcaseCard, animationDelay: `${i * 0.1}s` }}
              className="showcaseCard"
            >
              <div
                style={{ ...s.showcaseImg, backgroundImage: `url(${v.image})` }}
                className="showcaseImg"
              />
              <div style={s.showcaseOverlay} />
              <div style={s.showcaseContent}>
                <h3 style={s.showcaseTitle}>
                  {v.marque} {v.modele}
                </h3>
                <div style={s.showcasePrice}>{v.prix} TND</div>
                <div style={s.showcaseSpecs}>
                  <span>{v.annee}</span> • <span>{v.kilometrage} km</span> •{" "}
                  <span>{v.energie}</span>
                </div>
                <button style={s.showcaseBtn} onClick={onStart}>
                  Estimer ce modèle
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

// ─── PREDICT PAGE ─────────────────────────────────────────────────────────────
function PredictPage() {
  const [form, setForm] = useState(initialForm);
  const [step, setStep] = useState(0);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [options, setOptions] = useState(DEFAULT_OPTIONS);
  const [ranges, setRanges] = useState({});
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    { id: "w", role: "bot", text: '👋 Je suis votre assistant IA automobile.\n\nDécrivez-moi une voiture (ex: "Peugeot 308 diesel 2019", "Golf 7 automatique 80000 km") et je remplirai le formulaire.' },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  // Fetch possible values from the backend on mount
  useEffect(() => {
    fetch(`${API_URL}/options`)
      .then((res) => res.json())
      .then((data) => {
        if (data.options) setOptions((prev) => ({ ...prev, ...data.options }));
        if (data.numeric_ranges) setRanges(data.numeric_ranges);
      })
      .catch(() => {
        /* keep defaults on failure */
      });
  }, []);

  const cur = steps[step];

  const rangeError = (field) => {
    const r = ranges[field];
    if (!r || form[field] === "" || form[field] === null) return null;
    const v = Number(form[field]);
    if (v < r.min || v > r.max) return `Valeur entre ${r.min} et ${r.max}`;
    return null;
  };

  const isValid = () =>
    cur.fields.every((f) => form[f] !== "" && form[f] !== null) &&
    cur.fields.filter((f) => numericFields.includes(f)).every((f) => !rangeError(f));

  const handleChange = (k, v) => {
    setForm((p) => ({ ...p, [k]: v }));
    setError(null);
  };
  const handleNext = () => {
    if (!isValid()) {
      setError("Veuillez remplir tous les champs.");
      return;
    }
    setError(null);
    setStep((s) => s + 1);
  };
  const handleBack = () => {
    setError(null);
    setStep((s) => s - 1);
  };
  const handleReset = () => {
    setForm(initialForm);
    setStep(0);
    setResult(null);
    setError(null);
  };

  // ─── Chatbot logic ──────────────────────────────────────────────
  const addChatMsg = (msg) =>
    setChatMessages((prev) => [...prev, { ...msg, id: String(Date.now()) + Math.random() }]);

  const buildChatHistory = () =>
    chatMessages.filter((m) => m.id !== "w").map((m) => ({ role: m.role === "bot" ? "bot" : "user", text: m.text }));

  const chatSend = async (text) => {
    const q = (text || chatInput).trim();
    if (!q || chatLoading) return;
    addChatMsg({ role: "user", text: q });
    setChatInput("");
    setChatLoading(true);
    try {
      const history = buildChatHistory();
      const res = await fetch(`${API_URL}/autofill`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, history }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Erreur serveur");
      if (data.matched && !data.parse_error) {
        const hasFields = Object.keys(data).some((k) => fieldLabels[k] && data[k] != null);
        addChatMsg({ role: "bot", text: data.message || "🎯 Caractéristiques identifiées :", autofillData: hasFields ? data : undefined });
      } else {
        addChatMsg({ role: "bot", text: data.message || "❌ Je n'ai pas pu identifier cette voiture." });
      }
    } catch (e) {
      addChatMsg({ role: "bot", text: `⚠️ ${e.message}` });
    } finally {
      setChatLoading(false);
    }
  };

  const applyAutofill = (data) => {
    const newForm = { ...form };
    const fields = [
      "Marque", "Energie", "Boite_vitesse", "Transmission", "Carrosserie",
      "Gouvernorat", "Couleur_exterieure", "Couleur_interieure", "Sellerie",
      "Puissance_fiscale", "Puissance_ch", "Nombre_places", "Nombre_portes",
      "Cylindree", "Kilometrage", "age_voiture",
    ];
    fields.forEach((k) => {
      if (data[k] != null && data[k] !== "") newForm[k] = String(data[k]);
    });
    setForm(newForm);
    setStep(0);
    addChatMsg({ role: "bot", text: "✅ Formulaire rempli ! Vous pouvez ajuster les valeurs." });
  };

  const handleSubmit = async () => {
    if (!isValid()) {
      setError("Veuillez remplir tous les champs.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const payload = {};
      Object.entries(form).forEach(([k, v]) => {
        payload[k] = numericFields.includes(k) ? Number(v) : v;
      });
      const res = await fetch(`${API_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const e = await res.json();
        throw new Error(e.detail || "Erreur serveur");
      }
      setResult(await res.json());
    } catch (e) {
      setError(e.message || "Impossible de contacter l'API.");
    } finally {
      setLoading(false);
    }
  };

  const renderField = (field) => {
    if (selectFields.includes(field))
      return (
        <div key={field} style={s.fieldGroup}>
          <label style={s.label}>{fieldLabels[field]}</label>
          <div style={s.selWrap}>
            <select
              value={form[field]}
              onChange={(e) => handleChange(field, e.target.value)}
              style={s.select}
            >
              <option value="">— Sélectionner —</option>
              {(options[field] || []).map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
            <span style={s.arrow}>▾</span>
          </div>
        </div>
      );
    const r = ranges[field];
    const rErr = rangeError(field);
    return (
      <div key={field} style={s.fieldGroup}>
        <label style={s.label}>
          {fieldLabels[field]}
          {r && <span style={s.rangeHint}> ({r.min} – {r.max})</span>}
        </label>
        <input
          type="number"
          value={form[field]}
          onChange={(e) => handleChange(field, e.target.value)}
          placeholder={r ? `${r.min} – ${r.max}` : "0"}
          min={r ? r.min : 0}
          max={r ? r.max : undefined}
          style={{
            ...s.input,
            ...(rErr ? { borderColor: "rgba(255,68,85,0.6)" } : {}),
          }}
        />
        {rErr && <span style={s.fieldErr}>{rErr}</span>}
      </div>
    );
  };

  if (result)
    return (
      <div style={s.resWrap}>
        <div style={s.resCard}>
          <div style={s.resGlow} />
          <div style={s.resEmoji}>🏆</div>
          <div style={s.resLbl}>Prix estimé pour votre véhicule</div>
          <div style={s.resPrice}>
            {typeof result.predicted_price === "number"
              ? result.predicted_price.toLocaleString("fr-TN", {
                  maximumFractionDigits: 0,
                })
              : "—"}
            <span style={s.resCur}> TND</span>
          </div>
          <div style={s.resTags}>
            <span style={s.tag}>📍 {form.Marque}</span>
            <span style={s.tag}>📅 {form.age_voiture} ans</span>
            <span style={s.tag}>
              🛣️ {Number(form.Kilometrage).toLocaleString()} km
            </span>
            <span style={s.tag}>⚡ {form.Energie}</span>
            <span style={s.tag}>⚙️ {form.Boite_vitesse}</span>
            <span style={s.tag}>🏎️ {form.Carrosserie}</span>
          </div>
          <button onClick={handleReset} style={s.resetBtn}>
            ↩ Nouvelle estimation
          </button>
        </div>
      </div>
    );

  return (
    <div style={s.predWrap}>
      <div style={s.predHead}>
        <span style={s.secTag}>Formulaire de prédiction</span>
        <h2 style={s.predTitle}>Renseignez votre véhicule</h2>
        <p style={s.predSub}>
          Complétez les 4 étapes pour obtenir votre estimation
        </p>
      </div>
      <div style={s.formCard}>
        <div style={s.stepBar}>
          {steps.map((st, i) => (
            <div key={st.id} style={s.stepItem}>
              <div
                onClick={() => i < step && setStep(i)}
                style={{
                  ...s.stepCirc,
                  ...(i < step ? s.sDone : i === step ? s.sActive : s.sPend),
                }}
              >
                {i < step ? "✓" : st.icon}
              </div>
              <span style={{ ...s.stepLbl, opacity: i === step ? 1 : 0.3 }}>
                {st.title}
              </span>
              {i < steps.length - 1 && (
                <div
                  style={{
                    ...s.stepLine,
                    background: i < step ? gold : "rgba(255,255,255,0.07)",
                  }}
                />
              )}
            </div>
          ))}
        </div>
        <div style={s.formBody}>
          <div style={s.formStepHead}>
            <span style={s.stepCount}>
              Étape {step + 1} sur {steps.length}
            </span>
            <h3 style={s.stepName}>
              {cur.icon} {cur.title}
            </h3>
          </div>
          <div style={s.fieldsGrid}>
            {cur.fields.map((f) => renderField(f))}
          </div>
          {error && <div style={s.errBox}>⚠ {error}</div>}
          <div style={s.btnRow}>
            {step > 0 && (
              <button onClick={handleBack} style={s.backBtn}>
                ← Retour
              </button>
            )}
            {step < steps.length - 1 ? (
              <button onClick={handleNext} style={s.nextBtn}>
                Suivant →
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={loading}
                style={s.subBtn}
              >
                {loading ? "⟳ Analyse en cours..." : "🔮 Prédire le prix"}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Chatbot FAB */}
      <button onClick={() => setChatOpen((o) => !o)} style={s.chatFab}>
        {chatOpen ? "✕" : "🤖"}
      </button>

      {/* Chatbot Panel */}
      {chatOpen && (
        <div style={s.chatPanel}>
          <div style={s.chatHeader}>
            <span style={{ fontSize: 22 }}>🤖</span>
            <div>
              <div style={{ fontWeight: 700, color: "#e8dcc8", fontSize: 14 }}>AutoBot IA</div>
              <div style={{ fontSize: 11, color: "rgba(232,220,200,0.4)" }}>Propulsé par Gemini</div>
            </div>
            <button onClick={() => { setChatMessages([{ id: "w", role: "bot", text: '👋 Décrivez-moi une voiture et je remplirai le formulaire.' }]); }} style={s.chatResetBtn}>🔄</button>
          </div>
          <div style={s.chatBody} ref={(el) => { if (el) el.scrollTop = el.scrollHeight; }}>
            {chatMessages.map((msg) => (
              <div key={msg.id} style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start", marginBottom: 10 }}>
                {msg.role === "bot" && <span style={{ fontSize: 18, marginRight: 6, marginTop: 2 }}>🤖</span>}
                <div style={msg.role === "bot" ? s.chatBubbleBot : s.chatBubbleUser}>
                  <div style={{ fontSize: 13, lineHeight: "20px", color: msg.role === "bot" ? "#e8dcc8" : "#04090f", whiteSpace: "pre-wrap" }}>{msg.text}</div>
                  {msg.autofillData && (
                    <div style={s.chatPreview}>
                      {Object.entries(msg.autofillData).filter(([k]) => fieldLabels[k] && msg.autofillData[k] != null).map(([k, v]) => (
                        <div key={k} style={s.chatPreviewRow}>
                          <span style={{ fontSize: 11, color: "rgba(232,220,200,0.4)" }}>{fieldLabels[k]}</span>
                          <span style={{ fontSize: 12, color: gold, fontWeight: 600 }}>{String(v)}</span>
                        </div>
                      ))}
                      <button onClick={() => applyAutofill(msg.autofillData)} style={s.chatApplyBtn}>✅ Appliquer au formulaire</button>
                    </div>
                  )}

                </div>
                {msg.role === "user" && <span style={{ fontSize: 18, marginLeft: 6, marginTop: 2 }}>👤</span>}
              </div>
            ))}
            {chatLoading && (
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 18 }}>🤖</span>
                <div style={{ ...s.chatBubbleBot, fontStyle: "italic", fontSize: 12, color: "rgba(232,220,200,0.4)" }}>Recherche en cours…</div>
              </div>
            )}
          </div>
          <div style={s.chatInputRow}>
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && chatSend()}
              placeholder='Décrivez votre voiture…'
              style={s.chatInput}
              disabled={chatLoading}
            />
            <button onClick={() => chatSend()} disabled={!chatInput.trim() || chatLoading} style={{ ...s.chatSendBtn, opacity: chatInput.trim() && !chatLoading ? 1 : 0.4 }}>➤</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── ROOT APP ─────────────────────────────────────────────────────────────────
export default function App() {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("ap_user"));
    } catch {
      return null;
    }
  });

  const [page, setPage] = useState(() => {
    const token = localStorage.getItem("ap_token");
    const saved = localStorage.getItem("ap_user");
    return token && saved ? "home" : "auth";
  });

  const [apiStatus, setApiStatus] = useState(null);
  const [particles] = useState(() =>
    Array.from({ length: 25 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      speed: Math.random() * 30 + 20,
      delay: Math.random() * 5,
    })),
  );

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((r) => (r.ok ? setApiStatus("online") : setApiStatus("offline")))
      .catch(() => setApiStatus("offline"));
  }, []);

  const handleAuthSuccess = (userData) => {
    setUser(userData);
    setPage("home");
  };

  const handleLogout = () => {
    localStorage.removeItem("ap_token");
    localStorage.removeItem("ap_user");
    setUser(null);
    setPage("auth");
  };

  if (page === "auth") {
    return (
      <>
        <AuthPage onSuccess={handleAuthSuccess} />
        <style>{`
          @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600;700&display=swap');
          *,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
          body{background:#04090f;overflow-x:hidden;}
          input::placeholder{color:rgba(232,220,200,0.22);}
          input:focus{outline:none;border-color:#c9a227!important;box-shadow:0 0 0 3px rgba(201,162,39,0.14);}
          button{font-family:'DM Sans',sans-serif;cursor:pointer;}
          button:hover{filter:brightness(1.08);}
        `}</style>
      </>
    );
  }

  return (
    <div style={s.root}>
      <AnimatedBg particles={particles} />
      <Header
        page={page}
        onNav={setPage}
        apiStatus={apiStatus}
        user={user}
        onLogout={handleLogout}
      />
      {page === "home" && <HomePage onStart={() => setPage("predict")} />}
      {page === "predict" && <PredictPage />}
      <footer style={s.footer}>
        AutoPredict TN · Powered by FastAPI + MLflow + React · © 2026
      </footer>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600;700&display=swap');
        *,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
        body{background:#04090f;overflow-x:hidden;}
        @keyframes float{0%,100%{transform:translateY(0);opacity:.45}50%{transform:translateY(-26px);opacity:.9}}
        @keyframes fadeUp{from{opacity:0;transform:translateY(22px)}to{opacity:1;transform:translateY(0)}}
        @keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(201,162,39,.4)}50%{box-shadow:0 0 18px 6px rgba(201,162,39,.2)}}
        @keyframes zoom{0%{transform:scale(1)}100%{transform:scale(1.05)}}
        select option{background:#0a1625;color:#e8dcc8;}
        input[type=number]::-webkit-inner-spin-button{-webkit-appearance:none;}
        input::placeholder{color:rgba(232,220,200,.22);}
        input:focus,select:focus{outline:none;border-color:#c9a227!important;box-shadow:0 0 0 3px rgba(201,162,39,.14);}
        button{font-family:'DM Sans',sans-serif;cursor:pointer;}
        button:hover{filter:brightness(1.08);}
        ::-webkit-scrollbar{width:5px;}
        ::-webkit-scrollbar-thumb{background:#c9a22733;border-radius:3px;}

        /* Hover effects for showcase cards */
        .showcaseCard:hover .showcaseImg {
          transform: scale(1.1);
        }
        .showcaseCard:hover {
          transform: scale(1.02);
          box-shadow: 0 25px 40px -10px rgba(201, 162, 39, 0.4);
        }
        .showcaseBtn:hover {
          background: gold;
          color: #04090f;
        }
      `}</style>
    </div>
  );
}

// ─── STYLES ───────────────────────────────────────────────────────────────────
const s = {
  root: {
    minHeight: "100vh",
    fontFamily: "'DM Sans',sans-serif",
    color: "#e8dcc8",
    position: "relative",
  },

  bg: { position: "fixed", inset: 0, zIndex: 0, pointerEvents: "none" },
  bgGrad1: {
    position: "fixed",
    inset: 0,
    zIndex: 0,
    background:
      "radial-gradient(ellipse 90% 70% at 15% 5%, #081422 0%, #04090f 65%)",
    pointerEvents: "none",
  },
  bgGrad2: {
    position: "fixed",
    bottom: "-20%",
    right: "-8%",
    width: "700px",
    height: "700px",
    borderRadius: "50%",
    background:
      "radial-gradient(circle,rgba(201,162,39,0.05)0%,transparent 70%)",
    pointerEvents: "none",
    zIndex: 0,
  },
  bgGrad3: {
    position: "fixed",
    top: "30%",
    left: "-5%",
    width: "400px",
    height: "400px",
    borderRadius: "50%",
    background:
      "radial-gradient(circle,rgba(30,60,100,0.12)0%,transparent 70%)",
    pointerEvents: "none",
    zIndex: 0,
  },
  grid: {
    position: "fixed",
    inset: 0,
    zIndex: 0,
    backgroundImage:
      "linear-gradient(rgba(201,162,39,0.022)1px,transparent 1px),linear-gradient(90deg,rgba(201,162,39,0.022)1px,transparent 1px)",
    backgroundSize: "70px 70px",
    pointerEvents: "none",
  },
  particle: {
    position: "absolute",
    borderRadius: "50%",
    background: "rgba(201,162,39,0.32)",
    animation: "float linear infinite",
  },

  authPage: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "24px",
    position: "relative",
    overflow: "hidden",
    fontFamily: "'DM Sans',sans-serif",
    color: "#e8dcc8",
  },
  authCard: {
    position: "absolute",
    zIndex: 10,
    width: "100%",
    maxWidth: "480px",
    background: "rgba(8,18,32,0.92)",
    border: `1px solid rgba(201,162,39,0.22)`,
    borderRadius: "28px",
    padding: "44px 40px 32px",
    backdropFilter: "blur(28px)",
    boxShadow: "0 40px 80px rgba(0,0,0,0.55)",
  },
  authLogo: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "10px",
    marginBottom: "16px",
  },
  authBadge: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "7px 18px",
    background: goldDim,
    border: `1px solid rgba(201,162,39,0.3)`,
    borderRadius: "20px",
    fontSize: "12px",
    color: gold,
    letterSpacing: "0.5px",
    marginBottom: "20px",
  },
  authTabs: {
    display: "flex",
    background: "rgba(255,255,255,0.03)",
    borderRadius: "12px",
    padding: "4px",
    marginBottom: "16px",
    border: `1px solid ${goldDim}`,
  },
  authTab: {
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
  authTabActive: { background: goldDim, color: gold, fontWeight: "700" },
  authSub: {
    textAlign: "center",
    fontSize: "13px",
    color: "rgba(232,220,200,0.42)",
    marginBottom: "22px",
    letterSpacing: "0.3px",
    lineHeight: 1.6,
  },
  authBtn: {
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
    marginBottom: "16px",
  },

  fg: { display: "flex", flexDirection: "column", gap: "5px" },
  lbl: {
    fontSize: "10px",
    letterSpacing: "1.5px",
    textTransform: "uppercase",
    color: gold,
    opacity: 0.72,
  },
  inp: {
    width: "100%",
    padding: "11px 14px",
    background: "rgba(255,255,255,0.04)",
    border: `1px solid rgba(201,162,39,0.2)`,
    borderRadius: "11px",
    color: "#e8dcc8",
    fontSize: "14px",
    fontFamily: "'DM Sans',sans-serif",
    transition: "border-color 0.2s",
    boxSizing: "border-box",
  },
  icoL: {
    position: "absolute",
    left: "11px",
    top: "50%",
    transform: "translateY(-50%)",
    fontSize: "13px",
    pointerEvents: "none",
    opacity: 0.5,
    zIndex: 1,
  },
  eyeBtn: {
    position: "absolute",
    right: "10px",
    top: "50%",
    transform: "translateY(-50%)",
    background: "transparent",
    border: "none",
    fontSize: "14px",
    cursor: "pointer",
    opacity: 0.5,
    padding: "2px",
  },

  header: {
    position: "relative",
    zIndex: 100,
    height: "66px",
    display: "flex",
    alignItems: "center",
    padding: "0 40px",
    borderBottom: `1px solid ${goldDim}`,
    backdropFilter: "blur(16px)",
    background: "rgba(4,9,15,0.65)",
  },
  headerInner: {
    maxWidth: "1200px",
    margin: "0 auto",
    width: "100%",
    display: "flex",
    alignItems: "center",
    gap: "20px",
  },
  logo: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    cursor: "pointer",
    flexShrink: 0,
  },
  logoMark: { fontSize: "20px", color: gold },
  logoText: {
    fontFamily: "'Bebas Neue',sans-serif",
    fontSize: "20px",
    letterSpacing: "3px",
  },
  logoTN: { color: gold },
  nav: { display: "flex", gap: "4px", flex: 1 },
  navBtn: {
    padding: "6px 16px",
    background: "transparent",
    border: "none",
    borderRadius: "8px",
    color: "rgba(232,220,200,0.45)",
    fontSize: "13px",
    letterSpacing: "0.5px",
    transition: "all 0.2s",
  },
  navBtnActive: { background: goldDim, color: gold, fontWeight: "600" },
  apiPill: {
    display: "flex",
    alignItems: "center",
    gap: "7px",
    padding: "5px 12px",
    borderRadius: "20px",
    background: "rgba(255,255,255,0.04)",
    border: "1px solid rgba(255,255,255,0.07)",
    flexShrink: 0,
  },
  dot: { width: "7px", height: "7px", borderRadius: "50%", flexShrink: 0 },
  dotLabel: {
    fontSize: "11px",
    opacity: 0.65,
    letterSpacing: ".5px",
    whiteSpace: "nowrap",
  },
  userArea: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    flexShrink: 0,
  },
  userAvatar: {
    width: "30px",
    height: "30px",
    borderRadius: "50%",
    background: `linear-gradient(135deg,${gold},#9e7b16)`,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "13px",
    fontWeight: "700",
    color: "#04090f",
    flexShrink: 0,
  },
  userName: {
    fontSize: "12px",
    color: "rgba(232,220,200,0.65)",
    maxWidth: "120px",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  logoutBtn: {
    padding: "5px 12px",
    background: "transparent",
    border: "1px solid rgba(255,68,85,0.3)",
    borderRadius: "8px",
    color: "#ff8899",
    fontSize: "11px",
    cursor: "pointer",
    transition: "all 0.2s",
    whiteSpace: "nowrap",
  },

  // HOME PAGE
  heroSection: {
    position: "relative",
    zIndex: 10,
    minHeight: "90vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "80px 24px 60px",
    overflow: "hidden",
  },
  heroBackground: {
    position: "absolute",
    inset: 0,
    zIndex: 0,
    backgroundImage:
      "url('https://i.pinimg.com/1200x/9f/6b/b5/9f6bb5e1dd1c086b00812bf6df3050c4.jpg')",
    backgroundSize: "cover",
    backgroundPosition: "center",
    backgroundRepeat: "no-repeat",
    filter: "brightness(0.7)",
    transition: "transform 0.3s ease",
    animation: "zoom 20s infinite alternate",
  },
  heroOverlay: {
    position: "absolute",
    inset: 0,
    zIndex: 1,
    background:
      "radial-gradient(circle at 30% 50%, rgba(0,0,0,0.2) 0%, rgba(0,0,0,0.7) 100%)",
  },
  heroContent: {
    maxWidth: "800px",
    textAlign: "center",
    position: "relative",
    zIndex: 2,
  },
  badge: {
    display: "inline-flex",
    alignItems: "center",
    gap: "8px",
    padding: "8px 20px",
    background: goldDim,
    border: `1px solid rgba(201,162,39,0.3)`,
    borderRadius: "24px",
    fontSize: "12px",
    color: gold,
    letterSpacing: "0.5px",
    marginBottom: "28px",
    animation: "fadeUp 0.5s 0.1s both",
  },
  heroTitle: {
    fontFamily: "'Bebas Neue',sans-serif",
    fontSize: "clamp(32px, 6vw, 60px)",
    lineHeight: 1.2,
    letterSpacing: "2px",
    marginBottom: "24px",
    animation: "fadeUp 0.5s 0.2s both",
    textShadow: "0 2px 10px rgba(0,0,0,0.5)",
  },
  heroGold: { color: gold, textShadow: "0 0 50px rgba(201,162,39,0.3)" },
  heroDesc: {
    fontSize: "clamp(14px,1.8vw,16px)",
    lineHeight: 1.8,
    color: "rgba(232,220,200,0.9)",
    maxWidth: "560px",
    margin: "0 auto 38px",
    animation: "fadeUp 0.5s 0.3s both",
    textShadow: "0 1px 4px rgba(0,0,0,0.6)",
  },
  heroBtns: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "14px",
    animation: "fadeUp 0.5s 0.4s both",
  },
  ctaPrimary: {
    display: "inline-flex",
    alignItems: "center",
    gap: "12px",
    padding: "18px 38px",
    background: `linear-gradient(135deg,${gold},#9e7b16)`,
    border: "none",
    borderRadius: "14px",
    color: "#04090f",
    fontSize: "16px",
    fontWeight: "700",
    letterSpacing: "0.3px",
    boxShadow: "0 12px 36px rgba(201,162,39,0.32)",
    transition: "all 0.25s",
  },
  ctaArrow: { fontSize: "18px" },
  ctaNote: {
    fontSize: "12px",
    color: "rgba(232,220,200,0.7)",
    letterSpacing: "1px",
    textShadow: "0 1px 3px rgba(0,0,0,0.5)",
  },

  statsSection: {
    position: "relative",
    zIndex: 10,
    padding: "0 24px 64px",
    display: "flex",
    justifyContent: "center",
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(4,1fr)",
    maxWidth: "900px",
    width: "100%",
    border: `1px solid ${goldDim}`,
    borderRadius: "20px",
    overflow: "hidden",
    background: "rgba(4,9,15,0.7)",
    backdropFilter: "blur(12px)",
  },
  statItem: {
    padding: "30px 20px",
    textAlign: "center",
    borderRight: `1px solid ${goldDim}`,
  },
  statValue: {
    fontFamily: "'Bebas Neue',sans-serif",
    fontSize: "44px",
    color: gold,
    lineHeight: 1,
  },
  statLabel: {
    fontSize: "11px",
    color: "rgba(232,220,200,0.4)",
    letterSpacing: "1px",
    marginTop: "6px",
    textTransform: "uppercase",
  },

  // Nouvelle section showcase
  showcaseSection: {
    position: "relative",
    zIndex: 10,
    maxWidth: "1200px",
    margin: "0 auto",
    padding: "40px 24px 80px",
  },
  showcaseGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
    gap: "30px",
    marginTop: "40px",
  },
  showcaseCard: {
    position: "relative",
    borderRadius: "20px",
    overflow: "hidden",
    height: "380px",
    display: "flex",
    alignItems: "flex-end",
    padding: "24px",
    transition: "transform 0.3s ease, box-shadow 0.3s ease",
    animation: "fadeUp 0.5s both",
    cursor: "pointer",
    boxShadow: "0 20px 30px -10px rgba(0,0,0,0.5)",
  },
  showcaseImg: {
    position: "absolute",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    backgroundSize: "cover",
    backgroundPosition: "center",
    transition: "transform 0.5s ease",
    zIndex: 0,
  },
  showcaseOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    background:
      "linear-gradient(to top, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.3) 70%, transparent 100%)",
    zIndex: 1,
  },
  showcaseContent: {
    position: "relative",
    zIndex: 2,
    color: "#fff",
    width: "100%",
    textShadow: "0 2px 5px rgba(0,0,0,0.5)",
  },
  showcaseTitle: {
    fontFamily: "'Bebas Neue', sans-serif",
    fontSize: "28px",
    letterSpacing: "1px",
    marginBottom: "6px",
    color: gold,
    lineHeight: 1.2,
  },
  showcasePrice: {
    fontSize: "22px",
    fontWeight: "700",
    marginBottom: "8px",
    color: "#fff",
  },
  showcaseSpecs: {
    fontSize: "13px",
    opacity: 0.8,
    marginBottom: "16px",
    display: "flex",
    gap: "8px",
    flexWrap: "wrap",
  },
  showcaseBtn: {
    background: "transparent",
    border: `1px solid ${gold}`,
    color: gold,
    padding: "8px 18px",
    borderRadius: "30px",
    fontSize: "13px",
    fontWeight: "600",
    cursor: "pointer",
    transition: "all 0.2s",
    fontFamily: "'DM Sans', sans-serif",
  },

  // Pour compatibilité avec l'ancien secHead / secTitle (déjà utilisés)
  secHead: { textAlign: "center", marginBottom: "48px" },
  secTag: {
    fontSize: "11px",
    letterSpacing: "3px",
    textTransform: "uppercase",
    color: gold,
    opacity: 0.8,
  },
  secTitle: {
    fontFamily: "'Bebas Neue',sans-serif",
    fontSize: "clamp(30px,5vw,50px)",
    letterSpacing: "2px",
    marginTop: "12px",
    lineHeight: 1.1,
  },

  // Styles pour PredictPage (inchangés)
  predWrap: {
    position: "relative",
    zIndex: 10,
    maxWidth: "820px",
    margin: "0 auto",
    padding: "48px 24px 80px",
  },
  predHead: { textAlign: "center", marginBottom: "32px" },
  predTitle: {
    fontFamily: "'Bebas Neue',sans-serif",
    fontSize: "clamp(34px,6vw,54px)",
    letterSpacing: "2px",
    marginTop: "10px",
  },
  predSub: {
    fontSize: "14px",
    color: "rgba(232,220,200,0.4)",
    marginTop: "8px",
  },
  formCard: {
    background: "rgba(8,18,32,0.88)",
    border: `1px solid ${goldDim}`,
    borderRadius: "24px",
    overflow: "hidden",
    backdropFilter: "blur(24px)",
    boxShadow: "0 40px 80px rgba(0,0,0,0.5)",
  },
  stepBar: {
    display: "flex",
    alignItems: "center",
    padding: "26px 34px 22px",
    borderBottom: `1px solid ${goldDim}`,
    background: "rgba(0,0,0,0.22)",
  },
  stepItem: { display: "flex", alignItems: "center", flex: 1 },
  stepCirc: {
    width: "40px",
    height: "40px",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "16px",
    fontWeight: "bold",
    flexShrink: 0,
    cursor: "pointer",
    transition: "all 0.3s",
    zIndex: 1,
  },
  sActive: {
    background: gold,
    color: "#04090f",
    animation: "pulse 2s infinite",
    boxShadow: "0 0 20px rgba(201,162,39,0.4)",
  },
  sDone: { background: goldDim, color: gold, border: `1px solid ${gold}` },
  sPend: {
    background: "rgba(255,255,255,0.03)",
    color: "rgba(255,255,255,0.22)",
    border: "1px solid rgba(255,255,255,0.07)",
  },
  stepLbl: {
    fontSize: "11px",
    letterSpacing: "1px",
    textTransform: "uppercase",
    marginLeft: "9px",
    whiteSpace: "nowrap",
    transition: "opacity 0.3s",
  },
  stepLine: {
    flex: 1,
    height: "1px",
    margin: "0 10px",
    transition: "background 0.3s",
  },
  formBody: { padding: "34px" },
  formStepHead: { marginBottom: "26px" },
  stepCount: {
    fontSize: "11px",
    color: gold,
    letterSpacing: "2px",
    textTransform: "uppercase",
    opacity: 0.65,
  },
  stepName: {
    fontFamily: "'Bebas Neue',sans-serif",
    fontSize: "24px",
    letterSpacing: "2px",
    marginTop: "4px",
  },
  fieldsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill,minmax(210px,1fr))",
    gap: "16px",
    marginBottom: "26px",
  },
  fieldGroup: { display: "flex", flexDirection: "column", gap: "7px" },
  label: {
    fontSize: "10px",
    letterSpacing: "1.5px",
    textTransform: "uppercase",
    color: gold,
    opacity: 0.72,
  },
  selWrap: { position: "relative" },
  select: {
    width: "100%",
    padding: "11px 14px",
    background: "rgba(255,255,255,0.04)",
    border: `1px solid rgba(201,162,39,0.2)`,
    borderRadius: "10px",
    color: "#e8dcc8",
    fontSize: "14px",
    appearance: "none",
    transition: "border-color 0.2s",
  },
  arrow: {
    position: "absolute",
    right: "12px",
    top: "50%",
    transform: "translateY(-50%)",
    color: gold,
    pointerEvents: "none",
    fontSize: "11px",
  },
  input: {
    width: "100%",
    padding: "11px 14px",
    background: "rgba(255,255,255,0.04)",
    border: `1px solid rgba(201,162,39,0.2)`,
    borderRadius: "10px",
    color: "#e8dcc8",
    fontSize: "14px",
    transition: "border-color 0.2s",
  },
  errBox: {
    padding: "11px 14px",
    background: "rgba(255,68,85,0.07)",
    border: "1px solid rgba(255,68,85,0.22)",
    borderRadius: "10px",
    fontSize: "13px",
    color: "#ff8899",
    marginBottom: "18px",
  },
  rangeHint: {
    fontSize: "9px",
    opacity: 0.55,
    fontWeight: 400,
    letterSpacing: "0.5px",
  },
  fieldErr: {
    fontSize: "11px",
    color: "#ff8899",
    marginTop: "2px",
  },
  btnRow: { display: "flex", gap: "10px", justifyContent: "flex-end" },
  backBtn: {
    padding: "12px 22px",
    background: "transparent",
    border: `1px solid rgba(201,162,39,0.25)`,
    borderRadius: "11px",
    color: gold,
    fontSize: "14px",
    transition: "all 0.2s",
  },
  nextBtn: {
    padding: "12px 30px",
    background: `linear-gradient(135deg,${gold},#9e7b16)`,
    border: "none",
    borderRadius: "11px",
    color: "#04090f",
    fontSize: "14px",
    fontWeight: "700",
    boxShadow: "0 8px 22px rgba(201,162,39,0.27)",
    transition: "all 0.2s",
  },
  subBtn: {
    padding: "13px 34px",
    background: `linear-gradient(135deg,${gold},#9e7b16)`,
    border: "none",
    borderRadius: "11px",
    color: "#04090f",
    fontSize: "15px",
    fontWeight: "700",
    boxShadow: "0 8px 28px rgba(201,162,39,0.32)",
    transition: "all 0.2s",
  },

  resWrap: {
    position: "relative",
    zIndex: 10,
    maxWidth: "660px",
    margin: "0 auto",
    padding: "48px 24px 80px",
  },
  resCard: {
    background: "rgba(8,18,32,0.92)",
    border: `1px solid rgba(201,162,39,0.28)`,
    borderRadius: "24px",
    padding: "60px 40px",
    textAlign: "center",
    position: "relative",
    overflow: "hidden",
    boxShadow: "0 40px 80px rgba(0,0,0,0.5)",
    animation: "fadeUp 0.6s ease both",
  },
  resGlow: {
    position: "absolute",
    top: "-50%",
    left: "50%",
    transform: "translateX(-50%)",
    width: "500px",
    height: "500px",
    borderRadius: "50%",
    background:
      "radial-gradient(circle,rgba(201,162,39,0.09)0%,transparent 65%)",
    pointerEvents: "none",
  },
  resEmoji: { fontSize: "50px", marginBottom: "16px" },
  resLbl: {
    fontSize: "11px",
    letterSpacing: "4px",
    textTransform: "uppercase",
    color: gold,
    opacity: 0.75,
    marginBottom: "16px",
  },
  resPrice: {
    fontFamily: "'Bebas Neue',sans-serif",
    fontSize: "clamp(58px,11vw,96px)",
    letterSpacing: "2px",
    lineHeight: 1,
    marginBottom: "10px",
    textShadow: "0 0 50px rgba(201,162,39,0.25)",
  },
  resCur: { fontSize: "0.35em", color: gold, verticalAlign: "middle" },
  resTags: {
    display: "flex",
    flexWrap: "wrap",
    gap: "10px",
    justifyContent: "center",
    margin: "28px 0",
    padding: "18px",
    background: "rgba(255,255,255,0.025)",
    borderRadius: "14px",
    border: `1px solid ${goldDim}`,
  },
  tag: {
    fontSize: "13px",
    padding: "6px 14px",
    background: goldDim,
    borderRadius: "20px",
    color: gold,
  },
  resetBtn: {
    padding: "12px 30px",
    background: "transparent",
    border: `1px solid rgba(201,162,39,0.32)`,
    borderRadius: "11px",
    color: gold,
    fontSize: "14px",
    transition: "all 0.2s",
  },

  footer: {
    position: "relative",
    zIndex: 10,
    textAlign: "center",
    padding: "22px",
    fontSize: "11px",
    opacity: 0.22,
    letterSpacing: "1.5px",
    textTransform: "uppercase",
    borderTop: `1px solid ${goldDim}`,
  },

  // ─── Chatbot styles ────────────────────────────────────────────
  chatFab: {
    position: "fixed",
    bottom: 28,
    right: 28,
    width: 56,
    height: 56,
    borderRadius: 28,
    background: gold,
    border: "none",
    fontSize: 26,
    cursor: "pointer",
    zIndex: 1000,
    boxShadow: `0 6px 24px rgba(201,162,39,0.4)`,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "transform 0.2s",
    color: "#04090f",
    fontWeight: 700,
  },
  chatPanel: {
    position: "fixed",
    bottom: 96,
    right: 28,
    width: 380,
    maxHeight: "70vh",
    background: "#04090f",
    border: `1px solid ${goldDim}`,
    borderRadius: 20,
    zIndex: 999,
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    boxShadow: "0 20px 60px rgba(0,0,0,0.6)",
  },
  chatHeader: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "14px 18px",
    background: "rgba(201,162,39,0.08)",
    borderBottom: `1px solid ${goldDim}`,
  },
  chatResetBtn: {
    marginLeft: "auto",
    width: 30,
    height: 30,
    borderRadius: 15,
    background: "rgba(255,255,255,0.06)",
    border: "none",
    fontSize: 14,
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  chatBody: {
    flex: 1,
    overflowY: "auto",
    padding: "14px",
    maxHeight: "50vh",
  },
  chatBubbleBot: {
    maxWidth: "80%",
    background: "rgba(201,162,39,0.1)",
    border: `1px solid rgba(201,162,39,0.2)`,
    borderRadius: "16px 16px 16px 4px",
    padding: 12,
  },
  chatBubbleUser: {
    maxWidth: "80%",
    background: gold,
    borderRadius: "16px 16px 4px 16px",
    padding: 12,
  },
  chatPreview: {
    marginTop: 10,
    background: "rgba(0,0,0,0.2)",
    borderRadius: 12,
    padding: 10,
  },
  chatPreviewRow: {
    display: "flex",
    justifyContent: "space-between",
    padding: "3px 0",
    borderBottom: "1px solid rgba(255,255,255,0.05)",
  },
  chatApplyBtn: {
    marginTop: 10,
    width: "100%",
    padding: "10px",
    background: gold,
    border: "none",
    borderRadius: 10,
    color: "#04090f",
    fontWeight: 700,
    fontSize: 13,
    cursor: "pointer",
  },
  chatInputRow: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "10px 14px",
    borderTop: `1px solid ${goldDim}`,
    background: "rgba(8,18,32,0.95)",
  },
  chatInput: {
    flex: 1,
    background: "rgba(255,255,255,0.06)",
    border: `1px solid rgba(201,162,39,0.2)`,
    borderRadius: 20,
    padding: "10px 16px",
    fontSize: 14,
    color: "#e8dcc8",
    outline: "none",
  },
  chatSendBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    background: gold,
    border: "none",
    fontSize: 16,
    color: "#04090f",
    fontWeight: 700,
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
};

// Ajout de l'animation zoom pour l'image de fond (déjà inclus dans le style global)
// document.head.appendChild... n'est pas nécessaire car on a mis @keyframes dans le style global.
// On peut le retirer pour éviter les doublons.
