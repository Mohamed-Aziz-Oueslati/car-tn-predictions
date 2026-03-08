// ─── Form Data Constants ─────────────────────────────────────────────────────
export const DEFAULT_OPTIONS = {
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

export const selectFields = [
  "Marque",
  "Energie",
  "Boite_vitesse",
  "Transmission",
  "Carrosserie",
  "Gouvernorat",
  "Couleur_exterieure",
  "Couleur_interieure",
  "Sellerie",
];

export const initialForm = {
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

export const steps = [
  {
    id: 1,
    title: "Identité",
    icon: "🚗",
    fields: ["Marque", "Carrosserie", "Energie", "Boite_vitesse", "Transmission"],
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

export const fieldLabels = {
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

export const numericFields = [
  "Kilometrage",
  "Puissance_fiscale",
  "Puissance_ch",
  "Proprietaires",
  "Nombre_places",
  "Nombre_portes",
  "Cylindree",
  "age_voiture",
];
