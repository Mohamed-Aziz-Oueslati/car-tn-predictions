import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { colors } from "../theme";
import { loginUser, registerUser } from "../api";

export default function AuthScreen({ navigation }) {
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
  const [success, setSuccess] = useState(null);
  const [showPass, setShowPass] = useState(false);
  const [showConf, setShowConf] = useState(false);

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
      if (mode === "register") {
        await registerUser({
          full_name: `${form.prenom} ${form.nom}`,
          email: form.email,
          password: form.password,
          telephone: form.telephone || null,
        });
        switchMode("login");
        setTimeout(
          () => setSuccess("✅ Compte créé avec succès ! Connectez-vous."),
          50
        );
      } else {
        const data = await loginUser(form.email, form.password);
        await AsyncStorage.setItem("ap_token", data.access_token);
        await AsyncStorage.setItem("ap_user", JSON.stringify(data.user));
        navigation.reset({ index: 0, routes: [{ name: "Main" }] });
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={st.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView
        contentContainerStyle={st.scroll}
        keyboardShouldPersistTaps="handled"
      >
        {/* Logo */}
        <View style={st.logoRow}>
          <Text style={st.logoMark}>◈</Text>
          <Text style={st.logoText}>
            AutoPredict <Text style={st.logoGold}>TN</Text>
          </Text>
        </View>

        {/* Badge */}
        <Text style={st.badge}>
          {mode === "login" ? "🔑 Espace membre" : "🚀 Créer un compte"}
        </Text>

        {/* Tabs */}
        <View style={st.tabs}>
          <TouchableOpacity
            onPress={() => switchMode("login")}
            style={[st.tab, mode === "login" && st.tabActive]}
          >
            <Text
              style={[st.tabText, mode === "login" && st.tabTextActive]}
            >
              Connexion
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            onPress={() => switchMode("register")}
            style={[st.tab, mode === "register" && st.tabActive]}
          >
            <Text
              style={[st.tabText, mode === "register" && st.tabTextActive]}
            >
              Inscription
            </Text>
          </TouchableOpacity>
        </View>

        <Text style={st.subtitle}>
          {mode === "login"
            ? "Bienvenue ! Connectez-vous pour continuer."
            : "Créez votre compte gratuit en quelques secondes."}
        </Text>

        {/* Register-only fields */}
        {mode === "register" && (
          <View style={st.row}>
            <View style={st.halfField}>
              <Text style={st.label}>Nom</Text>
              <TextInput
                style={st.input}
                placeholder="Ben Ali"
                placeholderTextColor={colors.textDimmer}
                value={form.nom}
                onChangeText={(v) => change("nom", v)}
              />
            </View>
            <View style={st.halfField}>
              <Text style={st.label}>Prénom</Text>
              <TextInput
                style={st.input}
                placeholder="Ahmed"
                placeholderTextColor={colors.textDimmer}
                value={form.prenom}
                onChangeText={(v) => change("prenom", v)}
              />
            </View>
          </View>
        )}

        {/* Email */}
        <View style={st.field}>
          <Text style={st.label}>Adresse e-mail</Text>
          <TextInput
            style={st.input}
            placeholder="email@exemple.com"
            placeholderTextColor={colors.textDimmer}
            keyboardType="email-address"
            autoCapitalize="none"
            value={form.email}
            onChangeText={(v) => change("email", v)}
          />
        </View>

        {/* Phone (register only) */}
        {mode === "register" && (
          <View style={st.field}>
            <Text style={st.label}>
              Téléphone <Text style={st.optional}>(optionnel)</Text>
            </Text>
            <TextInput
              style={st.input}
              placeholder="+216 XX XXX XXX"
              placeholderTextColor={colors.textDimmer}
              keyboardType="phone-pad"
              value={form.telephone}
              onChangeText={(v) => change("telephone", v)}
            />
          </View>
        )}

        {/* Password */}
        <View style={st.field}>
          <Text style={st.label}>Mot de passe</Text>
          <View style={st.passWrap}>
            <TextInput
              style={[st.input, { flex: 1, marginBottom: 0 }]}
              placeholder="••••••••"
              placeholderTextColor={colors.textDimmer}
              secureTextEntry={!showPass}
              value={form.password}
              onChangeText={(v) => change("password", v)}
            />
            <TouchableOpacity
              onPress={() => setShowPass((p) => !p)}
              style={st.eyeBtn}
            >
              <Text style={st.eyeText}>{showPass ? "🙈" : "👁"}</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Confirm (register only) */}
        {mode === "register" && (
          <View style={st.field}>
            <Text style={st.label}>Confirmer le mot de passe</Text>
            <View style={st.passWrap}>
              <TextInput
                style={[st.input, { flex: 1, marginBottom: 0 }]}
                placeholder="••••••••"
                placeholderTextColor={colors.textDimmer}
                secureTextEntry={!showConf}
                value={form.confirm}
                onChangeText={(v) => change("confirm", v)}
              />
              <TouchableOpacity
                onPress={() => setShowConf((p) => !p)}
                style={st.eyeBtn}
              >
                <Text style={st.eyeText}>{showConf ? "🙈" : "👁"}</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Messages */}
        {success && (
          <View style={st.successBox}>
            <Text style={st.successText}>{success}</Text>
          </View>
        )}
        {error && (
          <View style={st.errorBox}>
            <Text style={st.errorText}>⚠ {error}</Text>
          </View>
        )}

        {/* Submit */}
        <TouchableOpacity
          onPress={submit}
          disabled={loading}
          style={[st.submitBtn, loading && { opacity: 0.7 }]}
          activeOpacity={0.8}
        >
          {loading ? (
            <ActivityIndicator color={colors.bg} />
          ) : (
            <Text style={st.submitText}>
              {mode === "login" ? "🔑 Se connecter" : "🚀 Créer mon compte"}
            </Text>
          )}
        </TouchableOpacity>

        {/* Switch mode */}
        <TouchableOpacity
          onPress={() => switchMode(mode === "login" ? "register" : "login")}
          style={st.switchBtn}
        >
          <Text style={st.switchText}>
            {mode === "login"
              ? "Pas encore de compte ? "
              : "Déjà inscrit ? "}
            <Text style={st.switchLink}>
              {mode === "login" ? "S'inscrire" : "Se connecter"}
            </Text>
          </Text>
        </TouchableOpacity>

        <Text style={st.footer}>
          🇹🇳 Marché automobile tunisien · Gratuit · Sécurisé
        </Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const st = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  scroll: {
    flexGrow: 1,
    justifyContent: "center",
    padding: 24,
  },
  logoRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 20,
    gap: 8,
  },
  logoMark: { fontSize: 24, color: colors.gold },
  logoText: {
    fontSize: 24,
    fontWeight: "700",
    letterSpacing: 2,
    color: colors.text,
  },
  logoGold: { color: colors.gold },
  badge: {
    textAlign: "center",
    fontSize: 14,
    color: colors.gold,
    marginBottom: 16,
    letterSpacing: 1,
  },
  tabs: {
    flexDirection: "row",
    backgroundColor: colors.goldDimmer,
    borderRadius: 12,
    marginBottom: 16,
    padding: 3,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: "center",
  },
  tabActive: {
    backgroundColor: colors.gold,
  },
  tabText: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.textDim,
  },
  tabTextActive: {
    color: colors.bg,
  },
  subtitle: {
    fontSize: 13,
    color: colors.textDim,
    textAlign: "center",
    marginBottom: 20,
  },
  row: {
    flexDirection: "row",
    gap: 12,
    marginBottom: 4,
  },
  halfField: {
    flex: 1,
  },
  field: {
    marginBottom: 14,
  },
  label: {
    fontSize: 11,
    fontWeight: "600",
    letterSpacing: 1,
    textTransform: "uppercase",
    color: colors.gold,
    marginBottom: 6,
    opacity: 0.8,
  },
  optional: {
    fontSize: 9,
    opacity: 0.5,
    textTransform: "none",
  },
  input: {
    backgroundColor: colors.inputBg,
    borderWidth: 1,
    borderColor: colors.inputBorder,
    borderRadius: 10,
    padding: 12,
    fontSize: 14,
    color: colors.text,
    marginBottom: 4,
  },
  passWrap: {
    flexDirection: "row",
    alignItems: "center",
    gap: 0,
  },
  eyeBtn: {
    position: "absolute",
    right: 10,
    padding: 6,
  },
  eyeText: { fontSize: 18 },
  successBox: {
    backgroundColor: colors.successBg,
    borderWidth: 1,
    borderColor: colors.successBorder,
    borderRadius: 10,
    padding: 12,
    marginBottom: 14,
  },
  successText: { color: colors.success, fontSize: 13 },
  errorBox: {
    backgroundColor: colors.errorBg,
    borderWidth: 1,
    borderColor: colors.errorBorder,
    borderRadius: 10,
    padding: 12,
    marginBottom: 14,
  },
  errorText: { color: colors.errorText, fontSize: 13 },
  submitBtn: {
    backgroundColor: colors.gold,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    marginBottom: 16,
    shadowColor: colors.gold,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  submitText: {
    color: colors.bg,
    fontSize: 15,
    fontWeight: "700",
  },
  switchBtn: {
    alignItems: "center",
    marginBottom: 20,
  },
  switchText: { color: colors.textDim, fontSize: 13 },
  switchLink: {
    color: colors.gold,
    fontWeight: "600",
    textDecorationLine: "underline",
  },
  footer: {
    textAlign: "center",
    fontSize: 10,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: colors.textDimmer,
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
    paddingTop: 16,
  },
});
