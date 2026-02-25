import { useState, useEffect } from "react";

// APRÈS
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ─── DATA ───────────────────────────────────────────────────────────────────
const MARQUES = [
  [
    "Toyota",
    "Volkswagen",
    "Renault",
    "Peugeot",
    "Hyundai",
    "Kia",
    "Ford",
    "BMW",
    "Mercedes",
    "Audi",
    "Citroën",
    "Nissan",
    "Honda",
    "Fiat",
    "Dacia",
    "Seat",
    "Opel",
    "Chevrolet",
    "Suzuki",
    "Mazda",
    "Abarth",
    "Alfa Romeo",
    "BAIC YX",
    "BYD",
    "Cadillac",
    "Changan",
    "Chery",
    "Cupra",
    "DS",
    "Dongfeng",
    "GWM",
    "Geely",
    "Hummer",
    "Infiniti",
    "Isuzu",
    "Jaguar",
    "Jeep",
    "Jetour",
    "Lancia",
    "Land Rover",
    "Lexus",
  ],
];
const ENERGIES = ["Essence", "Diesel", "Hybride", "Électrique", "GPL"];
const BOITES = ["Manuelle", "Automatique", "Semi-automatique"];
const TRANSMISSIONS = ["Traction avant", "Propulsion", "4x4", "Intégrale"];
const CARROSSERIES = [
  "Berline",
  "SUV",
  "Citadine",
  "Break",
  "Coupé",
  "Cabriolet",
  "Monospace",
  "Pick-up",
];
const GOUVERNORATS = [
  "Tunis",
  "Ariana",
  "Ben Arous",
  "Manouba",
  "Nabeul",
  "Zaghouan",
  "Bizerte",
  "Béja",
  "Jendouba",
  "Kef",
  "Siliana",
  "Sousse",
  "Monastir",
  "Mahdia",
  "Sfax",
  "Kairouan",
  "Kasserine",
  "Sidi Bouzid",
  "Gabès",
  "Medenine",
  "Tataouine",
  "Gafsa",
  "Tozeur",
  "Kébili",
];
const COULEURS_EXT = [
  "Blanc",
  "Noir",
  "Gris",
  "Argent",
  "Bleu",
  "Rouge",
  "Vert",
  "Beige",
  "Marron",
  "Orange",
  "Jaune",
  "Bordeaux",
];
const COULEURS_INT = ["Noir", "Beige", "Gris", "Crème", "Marron", "Rouge"];
const SELLERIES = ["Tissu", "Cuir", "Semi-cuir", "Alcantara"];

const initialForm = {
  Marque: "",
  Kilometrage: "",
  Energie: "",
  Boite_vitesse: "",
  Puissance_fiscale: "",
  Puissance_ch: "",
  Transmission: "",
  Carrosserie: "",
  Proprietaires: "",
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
    fields: ["age_voiture", "Kilometrage", "Proprietaires", "Gouvernorat"],
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
  Proprietaires: "Nombre de propriétaires",
  Gouvernorat: "Gouvernorat",
  Couleur_exterieure: "Couleur extérieure",
  Couleur_interieure: "Couleur intérieure",
  Sellerie: "Sellerie",
  Nombre_places: "Nombre de places",
  Nombre_portes: "Nombre de portes",
  Cylindree: "Cylindrée (cc)",
  age_voiture: "Âge du véhicule (ans)",
};

const selectOptions = {
  Marque: MARQUES,
  Energie: ENERGIES,
  Boite_vitesse: BOITES,
  Transmission: TRANSMISSIONS,
  Carrosserie: CARROSSERIES,
  Gouvernorat: GOUVERNORATS,
  Couleur_exterieure: COULEURS_EXT,
  Couleur_interieure: COULEURS_INT,
  Sellerie: SELLERIES,
};

const numericFields = [
  "Kilometrage",
  "Puissance_fiscale",
  "Puissance_ch",
  "Proprietaires",
  "Nombre_places",
  "Nombre_portes",
  "Cylindree",
  "age_voiture",
];

const gold = "#c9a227";
const goldDim = "rgba(201,162,39,0.15)";

// ─── ANIMATED BG ─────────────────────────────────────────────────────────────
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

// ─── HEADER ──────────────────────────────────────────────────────────────────
function Header({ page, onNav, apiStatus }) {
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
      </div>
    </header>
  );
}

// ─── HOME PAGE ────────────────────────────────────────────────────────────────
function HomePage({ onStart }) {
  const stats = [
    { value: "50K+", label: "Véhicules analysés" },
    { value: "94%", label: "Précision du modèle" },
    { value: "24", label: "Gouvernorats couverts" },
    { value: "2s", label: "Temps de réponse" },
  ];
  const features = [
    {
      icon: "🤖",
      title: "IA Avancée",
      desc: "Modèle ML entraîné sur des milliers d'annonces du marché tunisien.",
    },
    {
      icon: "⚡",
      title: "Instantané",
      desc: "Obtenez une estimation précise en moins de 2 secondes.",
    },
    {
      icon: "📊",
      title: "Multi-critères",
      desc: "17 paramètres analysés pour une précision maximale.",
    },
    {
      icon: "🇹🇳",
      title: "Marché Local",
      desc: "Calibré spécifiquement pour le marché automobile tunisien.",
    },
  ];

  return (
    <div>
      {/* HERO */}
      <section style={s.heroSection}>
        {/* SVG car silhouette */}
        <div style={s.carSilhouette}>
          <svg viewBox="0 0 900 260" style={{ width: "100%", height: "100%" }}>
            <path
              d="M140,190 L110,190 Q72,190 62,162 L44,112 Q38,92 58,87 L175,78 Q218,52 325,47 L488,47 Q572,47 624,78 L732,87 Q758,92 762,112 L752,162 Q742,190 704,190 L672,190 Q667,222 640,222 Q613,222 608,190 L222,190 Q217,222 190,222 Q163,222 158,190 Z"
              fill={gold}
              opacity="0.06"
            />
            <ellipse
              cx="190"
              cy="196"
              rx="32"
              ry="32"
              fill={gold}
              opacity="0.06"
            />
            <ellipse
              cx="630"
              cy="196"
              rx="32"
              ry="32"
              fill={gold}
              opacity="0.06"
            />
            <rect
              x="200"
              y="90"
              width="240"
              height="85"
              rx="6"
              fill={gold}
              opacity="0.02"
            />
            <rect
              x="460"
              y="90"
              width="180"
              height="85"
              rx="6"
              fill={gold}
              opacity="0.02"
            />
          </svg>
        </div>

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
              <span>🚗</span>
              Entrer les données de votre voiture
              <span style={s.ctaArrow}>→</span>
            </button>
            <span style={s.ctaNote}>
              Gratuit · Instantané · Sans inscription
            </span>
          </div>
        </div>
      </section>

      {/* STATS */}
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

      {/* FEATURES */}
      <section style={s.featSection}>
        <div style={s.secHead}>
          <span style={s.secTag}>Pourquoi nous choisir ?</span>
          <h2 style={s.secTitle}>
            Une technologie au service
            <br />
            de votre patrimoine
          </h2>
        </div>
        <div style={s.featGrid}>
          {features.map((f, i) => (
            <div
              key={i}
              style={{ ...s.featCard, animationDelay: `${i * 0.1}s` }}
            >
              <div style={s.featIcon}>{f.icon}</div>
              <h3 style={s.featTitle}>{f.title}</h3>
              <p style={s.featDesc}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* BOTTOM CTA */}
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

  const cur = steps[step];
  const isValid = () =>
    cur.fields.every((f) => form[f] !== "" && form[f] !== null);

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
    if (selectOptions[field])
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
              {selectOptions[field].map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
            <span style={s.arrow}>▾</span>
          </div>
        </div>
      );
    return (
      <div key={field} style={s.fieldGroup}>
        <label style={s.label}>{fieldLabels[field]}</label>
        <input
          type="number"
          value={form[field]}
          onChange={(e) => handleChange(field, e.target.value)}
          placeholder="0"
          min="0"
          style={s.input}
        />
      </div>
    );
  };

  // RESULT SCREEN
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

  // FORM
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
        {/* Step bar */}
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

        {/* Body */}
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
    </div>
  );
}

// ─── ROOT APP ─────────────────────────────────────────────────────────────────
export default function App() {
  const [page, setPage] = useState("home");
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

  return (
    <div style={s.root}>
      <AnimatedBg particles={particles} />
      <Header page={page} onNav={setPage} apiStatus={apiStatus} />
      {page === "home" ? (
        <HomePage onStart={() => setPage("predict")} />
      ) : (
        <PredictPage />
      )}
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
        select option{background:#0a1625;color:#e8dcc8;}
        input[type=number]::-webkit-inner-spin-button{-webkit-appearance:none;}
        input::placeholder{color:rgba(232,220,200,.22);}
        input:focus,select:focus{outline:none;border-color:#c9a227!important;box-shadow:0 0 0 3px rgba(201,162,39,.14);}
        button{font-family:'DM Sans',sans-serif;cursor:pointer;}
        button:hover{filter:brightness(1.08);}
        ::-webkit-scrollbar{width:5px;}
        ::-webkit-scrollbar-thumb{background:#c9a22733;border-radius:3px;}
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

  // BG
  bg: { position: "fixed", inset: 0, zIndex: 0, pointerEvents: "none" },
  bgGrad1: {
    position: "absolute",
    inset: 0,
    background:
      "radial-gradient(ellipse 90% 70% at 15% 5%, #081422 0%, #04090f 65%)",
  },
  bgGrad2: {
    position: "absolute",
    bottom: "-20%",
    right: "-8%",
    width: "700px",
    height: "700px",
    borderRadius: "50%",
    background:
      "radial-gradient(circle,rgba(201,162,39,0.05)0%,transparent 70%)",
  },
  bgGrad3: {
    position: "absolute",
    top: "30%",
    left: "-5%",
    width: "400px",
    height: "400px",
    borderRadius: "50%",
    background:
      "radial-gradient(circle,rgba(30,60,100,0.12)0%,transparent 70%)",
  },
  grid: {
    position: "absolute",
    inset: 0,
    backgroundImage:
      "linear-gradient(rgba(201,162,39,0.022)1px,transparent 1px),linear-gradient(90deg,rgba(201,162,39,0.022)1px,transparent 1px)",
    backgroundSize: "70px 70px",
  },
  particle: {
    position: "absolute",
    borderRadius: "50%",
    background: "rgba(201,162,39,0.32)",
    animation: "float linear infinite",
  },

  // HEADER
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
    gap: "28px",
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

  // HOME HERO
  heroSection: {
    position: "relative",
    zIndex: 10,
    minHeight: "86vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "80px 24px 60px",
    overflow: "hidden",
  },
  carSilhouette: {
    position: "absolute",
    bottom: "-10px",
    left: "50%",
    transform: "translateX(-50%)",
    width: "900px",
    height: "240px",
    pointerEvents: "none",
    opacity: 1,
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
    fontSize: "clamp(50px,9vw,88px)",
    lineHeight: 1.06,
    letterSpacing: "2px",
    marginBottom: "24px",
    animation: "fadeUp 0.5s 0.2s both",
  },
  heroGold: { color: gold, textShadow: "0 0 50px rgba(201,162,39,0.3)" },
  heroDesc: {
    fontSize: "clamp(14px,1.8vw,16px)",
    lineHeight: 1.8,
    color: "rgba(232,220,200,0.58)",
    maxWidth: "560px",
    margin: "0 auto 38px",
    animation: "fadeUp 0.5s 0.3s both",
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
    color: "rgba(232,220,200,0.3)",
    letterSpacing: "1px",
  },

  // STATS
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

  // FEATURES
  featSection: {
    position: "relative",
    zIndex: 10,
    maxWidth: "1100px",
    margin: "0 auto",
    padding: "20px 24px 80px",
  },
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
  featGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill,minmax(240px,1fr))",
    gap: "18px",
  },
  featCard: {
    padding: "30px 26px",
    background: "rgba(10,22,37,0.7)",
    border: `1px solid ${goldDim}`,
    borderRadius: "18px",
    backdropFilter: "blur(12px)",
    animation: "fadeUp 0.5s both",
    transition: "border-color 0.3s",
  },
  featIcon: { fontSize: "34px", marginBottom: "14px" },
  featTitle: {
    fontFamily: "'Bebas Neue',sans-serif",
    fontSize: "21px",
    letterSpacing: "1px",
    marginBottom: "10px",
  },
  featDesc: {
    fontSize: "14px",
    lineHeight: 1.7,
    color: "rgba(232,220,200,0.5)",
  },

  // BOTTOM CTA
  bottomCta: {
    position: "relative",
    zIndex: 10,
    padding: "20px 24px 100px",
    display: "flex",
    justifyContent: "center",
  },
  ctaBox: {
    position: "relative",
    maxWidth: "680px",
    width: "100%",
    padding: "56px 44px",
    background: "rgba(10,22,37,0.75)",
    border: `1px solid rgba(201,162,39,0.22)`,
    borderRadius: "24px",
    textAlign: "center",
    backdropFilter: "blur(20px)",
    overflow: "hidden",
  },
  ctaBoxGlow: {
    position: "absolute",
    top: "-60%",
    left: "50%",
    transform: "translateX(-50%)",
    width: "500px",
    height: "500px",
    borderRadius: "50%",
    background:
      "radial-gradient(circle,rgba(201,162,39,0.07)0%,transparent 70%)",
    pointerEvents: "none",
  },
  ctaBoxTitle: {
    fontFamily: "'Bebas Neue',sans-serif",
    fontSize: "clamp(26px,5vw,44px)",
    letterSpacing: "2px",
    marginBottom: "10px",
  },
  ctaBoxSub: {
    fontSize: "15px",
    color: "rgba(232,220,200,0.45)",
    marginBottom: "30px",
  },
  ctaLarge: {
    padding: "15px 42px",
    background: `linear-gradient(135deg,${gold},#9e7b16)`,
    border: "none",
    borderRadius: "13px",
    color: "#04090f",
    fontSize: "15px",
    fontWeight: "700",
    boxShadow: "0 10px 28px rgba(201,162,39,0.28)",
    transition: "all 0.25s",
  },

  // PREDICT
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

  // STEP BAR
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

  // FORM BODY
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

  // RESULT
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

  // FOOTER
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
};
