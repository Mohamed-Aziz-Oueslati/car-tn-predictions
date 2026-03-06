import { useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ─── DATA ────────────────────────────────────────────────────────────────────
export const MARQUES = [
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
];
export const ENERGIES = ["Essence", "Diesel", "Hybride", "Électrique", "GPL"];
export const BOITES = ["Manuelle", "Automatique", "Semi-automatique"];
export const TRANSMISSIONS = [
  "Traction avant",
  "Propulsion",
  "4x4",
  "Intégrale",
];
export const CARROSSERIES = [
  "Berline",
  "SUV",
  "Citadine",
  "Break",
  "Coupé",
  "Cabriolet",
  "Monospace",
  "Pick-up",
];
export const GOUVERNORATS = [
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
export const COULEURS_EXT = [
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
export const COULEURS_INT = [
  "Noir",
  "Beige",
  "Gris",
  "Crème",
  "Marron",
  "Rouge",
];
export const SELLERIES = ["Tissu", "Cuir", "Semi-cuir", "Alcantara"];

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

// ─── PREDICT PAGE ─────────────────────────────────────────────────────────────
export default function PredictCar() {
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

  // ── RESULT SCREEN ──
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

  // ── FORM ──
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

// ─── STYLES ───────────────────────────────────────────────────────────────────
const s = {
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
  secTag: {
    fontSize: "11px",
    letterSpacing: "3px",
    textTransform: "uppercase",
    color: gold,
    opacity: 0.8,
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
};
