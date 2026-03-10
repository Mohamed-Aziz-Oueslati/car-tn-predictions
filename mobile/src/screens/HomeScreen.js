import React from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Image,
  Dimensions,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { colors } from "../theme";

const { width } = Dimensions.get("window");

const stats = [
  { value: "50K+", label: "Véhicules analysés" },
  { value: "94%", label: "Précision du modèle" },
  { value: "24", label: "Gouvernorats" },
  { value: "2s", label: "Temps de réponse" },
];

const vehicules = [
  {
    marque: "Toyota",
    modele: "Corolla",
    prix: "22 500",
    annee: "2022",
    km: "30 000",
    energie: "Hybride",
    image:
      "https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=60",
  },
  {
    marque: "Volkswagen",
    modele: "Golf",
    prix: "18 900",
    annee: "2021",
    km: "45 000",
    energie: "Essence",
    image:
      "https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=60",
  },
  {
    marque: "Peugeot",
    modele: "3008",
    prix: "26 300",
    annee: "2023",
    km: "12 000",
    energie: "Diesel",
    image:
      "https://images.unsplash.com/photo-1555215695-3004980ad54e?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=60",
  },
  {
    marque: "Renault",
    modele: "Clio",
    prix: "14 200",
    annee: "2020",
    km: "58 000",
    energie: "Essence",
    image:
      "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=60",
  },
];

export default function HomeScreen({ navigation }) {
  return (
    <ScrollView style={st.container} contentContainerStyle={st.content}>
      {}
      <LinearGradient
        colors={["#081422", colors.bg]}
        style={st.hero}
      >
        <View style={st.heroBadge}>
          <Text style={st.heroBadgeText}>
            🏆 Meilleur outil d'estimation en Tunisie
          </Text>
        </View>

        <Text style={st.heroTitle}>
          Découvrez la Vraie{"\n"}
          <Text style={st.heroGold}>Valeur de Votre</Text>
          {"\n"}Voiture d'Occasion
        </Text>

        <Text style={st.heroDesc}>
          Notre intelligence artificielle analyse{" "}
          <Text style={{ fontWeight: "700", color: colors.text }}>
            17 critères
          </Text>{" "}
          de votre véhicule pour une estimation précise basée sur le marché
          tunisien.
        </Text>

        <TouchableOpacity
          style={st.ctaBtn}
          activeOpacity={0.8}
          onPress={() => navigation.navigate("Predict")}
        >
          <Text style={st.ctaText}>🚗 Estimer ma voiture →</Text>
        </TouchableOpacity>

        <Text style={st.ctaNote}>Gratuit · Instantané · Sans inscription</Text>
      </LinearGradient>

      {}
      <View style={st.statsGrid}>
        {stats.map((s, i) => (
          <View key={i} style={st.statCard}>
            <Text style={st.statValue}>{s.value}</Text>
            <Text style={st.statLabel}>{s.label}</Text>
          </View>
        ))}
      </View>

      {}
      <View style={st.section}>
        <Text style={st.sectionTag}>Nos véhicules en vedette</Text>
        <Text style={st.sectionTitle}>
          Sélection de voitures d'occasion
        </Text>
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={st.showcaseScroll}
      >
        {vehicules.map((v, i) => (
          <View key={i} style={st.showcaseCard}>
            <Image source={{ uri: v.image }} style={st.showcaseImg} />
            <LinearGradient
              colors={["transparent", "rgba(0,0,0,0.85)"]}
              style={st.showcaseOverlay}
            />
            <View style={st.showcaseContent}>
              <Text style={st.showcaseName}>
                {v.marque} {v.modele}
              </Text>
              <Text style={st.showcasePrice}>{v.prix} TND</Text>
              <Text style={st.showcaseSpecs}>
                {v.annee} · {v.km} km · {v.energie}
              </Text>
              <TouchableOpacity
                style={st.showcaseBtn}
                onPress={() => navigation.navigate("Predict")}
              >
                <Text style={st.showcaseBtnText}>Estimer ce modèle</Text>
              </TouchableOpacity>
            </View>
          </View>
        ))}
      </ScrollView>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const cardWidth = width * 0.7;

const st = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { paddingBottom: 20 },

  hero: { padding: 24, paddingTop: 50, alignItems: "center" },
  heroBadge: {
    backgroundColor: colors.goldDim,
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    marginBottom: 20,
  },
  heroBadgeText: {
    fontSize: 11,
    color: colors.gold,
    letterSpacing: 0.5,
  },
  heroTitle: {
    fontSize: 32,
    fontWeight: "800",
    color: colors.text,
    textAlign: "center",
    lineHeight: 40,
    marginBottom: 16,
  },
  heroGold: { color: colors.gold },
  heroDesc: {
    fontSize: 14,
    color: colors.textDim,
    textAlign: "center",
    lineHeight: 22,
    marginBottom: 28,
    paddingHorizontal: 8,
  },
  ctaBtn: {
    backgroundColor: colors.gold,
    paddingVertical: 14,
    paddingHorizontal: 28,
    borderRadius: 14,
    shadowColor: colors.gold,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.35,
    shadowRadius: 20,
    elevation: 10,
    marginBottom: 10,
  },
  ctaText: {
    color: colors.bg,
    fontSize: 15,
    fontWeight: "700",
  },
  ctaNote: {
    fontSize: 11,
    color: colors.textDimmer,
    letterSpacing: 1,
  },

  statsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    paddingHorizontal: 16,
    marginTop: 24,
    gap: 10,
  },
  statCard: {
    width: (width - 42) / 2,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 14,
    paddingVertical: 18,
    alignItems: "center",
  },
  statValue: {
    fontSize: 28,
    fontWeight: "800",
    color: colors.gold,
  },
  statLabel: {
    fontSize: 11,
    color: colors.textDim,
    letterSpacing: 0.5,
    marginTop: 4,
  },

  section: { paddingHorizontal: 24, marginTop: 32, marginBottom: 16 },
  sectionTag: {
    fontSize: 10,
    letterSpacing: 3,
    textTransform: "uppercase",
    color: colors.gold,
    opacity: 0.8,
    marginBottom: 6,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: "700",
    color: colors.text,
    lineHeight: 28,
  },

  showcaseScroll: { paddingLeft: 20, paddingRight: 8 },
  showcaseCard: {
    width: cardWidth,
    height: cardWidth * 1.15,
    borderRadius: 18,
    overflow: "hidden",
    marginRight: 14,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  showcaseImg: {
    width: "100%",
    height: "100%",
    position: "absolute",
  },
  showcaseOverlay: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    height: "70%",
  },
  showcaseContent: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    padding: 16,
  },
  showcaseName: {
    fontSize: 18,
    fontWeight: "700",
    color: colors.text,
    marginBottom: 4,
  },
  showcasePrice: {
    fontSize: 22,
    fontWeight: "800",
    color: colors.gold,
    marginBottom: 4,
  },
  showcaseSpecs: {
    fontSize: 12,
    color: colors.textDim,
    marginBottom: 10,
  },
  showcaseBtn: {
    borderWidth: 1,
    borderColor: colors.gold,
    borderRadius: 8,
    paddingVertical: 8,
    alignItems: "center",
  },
  showcaseBtnText: {
    color: colors.gold,
    fontSize: 12,
    fontWeight: "600",
  },
});
