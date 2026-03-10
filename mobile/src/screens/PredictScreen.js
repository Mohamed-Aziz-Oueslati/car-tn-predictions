import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Modal,
  FlatList,
  Dimensions,
} from "react-native";
import { colors } from "../theme";
import { fetchOptions, predictPrice } from "../api";
import {
  DEFAULT_OPTIONS,
  selectFields,
  initialForm,
  steps,
  fieldLabels,
  numericFields,
} from "../data";
import ChatBot from "../components/ChatBot";

const { width } = Dimensions.get("window");

function PickerModal({ visible, title, options, onSelect, onClose }) {
  const [search, setSearch] = useState("");
  const filtered = options.filter((o) =>
    String(o).toLowerCase().includes(search.toLowerCase())
  );
  return (
    <Modal visible={visible} transparent animationType="slide">
      <View style={pk.overlay}>
        <View style={pk.sheet}>
          <View style={pk.header}>
            <Text style={pk.title}>{title}</Text>
            <TouchableOpacity onPress={onClose}>
              <Text style={pk.close}>✕</Text>
            </TouchableOpacity>
          </View>
          {options.length > 8 && (
            <TextInput
              style={pk.search}
              placeholder="Rechercher..."
              placeholderTextColor={colors.textDimmer}
              value={search}
              onChangeText={setSearch}
            />
          )}
          <FlatList
            data={filtered}
            keyExtractor={(item) => String(item)}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={pk.item}
                onPress={() => {
                  onSelect(String(item));
                  onClose();
                  setSearch("");
                }}
              >
                <Text style={pk.itemText}>{String(item)}</Text>
              </TouchableOpacity>
            )}
            ListEmptyComponent={
              <Text style={pk.empty}>Aucun résultat</Text>
            }
            style={{ maxHeight: 350 }}
          />
        </View>
      </View>
    </Modal>
  );
}

const pk = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.6)",
    justifyContent: "flex-end",
  },
  sheet: {
    backgroundColor: "#0a1625",
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    maxHeight: "70%",
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 14,
  },
  title: {
    fontSize: 16,
    fontWeight: "700",
    color: colors.text,
  },
  close: {
    fontSize: 20,
    color: colors.textDim,
    padding: 4,
  },
  search: {
    backgroundColor: colors.inputBg,
    borderWidth: 1,
    borderColor: colors.inputBorder,
    borderRadius: 10,
    padding: 10,
    fontSize: 14,
    color: colors.text,
    marginBottom: 10,
  },
  item: {
    paddingVertical: 13,
    paddingHorizontal: 8,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  itemText: { fontSize: 15, color: colors.text },
  empty: {
    color: colors.textDim,
    textAlign: "center",
    paddingVertical: 20,
    fontSize: 14,
  },
});

export default function PredictScreen({ navigation }) {
  const [form, setForm] = useState(initialForm);
  const [step, setStep] = useState(0);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [options, setOptions] = useState(DEFAULT_OPTIONS);
  const [ranges, setRanges] = useState({});
  const [pickerField, setPickerField] = useState(null);
  const [chatVisible, setChatVisible] = useState(false);

  const handleAutofill = (data) => {
    const newForm = { ...form };
    const fieldMap = {
      Marque: "Marque",
      Energie: "Energie",
      Boite_vitesse: "Boite_vitesse",
      Transmission: "Transmission",
      Carrosserie: "Carrosserie",
      Gouvernorat: "Gouvernorat",
      Couleur_exterieure: "Couleur_exterieure",
      Couleur_interieure: "Couleur_interieure",
      Sellerie: "Sellerie",
      Puissance_fiscale: "Puissance_fiscale",
      Puissance_ch: "Puissance_ch",
      Nombre_places: "Nombre_places",
      Nombre_portes: "Nombre_portes",
      Cylindree: "Cylindree",
      Kilometrage: "Kilometrage",
      age_voiture: "age_voiture",
    };
    Object.entries(fieldMap).forEach(([apiKey, formKey]) => {
      if (data[apiKey] != null && data[apiKey] !== "") {
        const val = String(data[apiKey]);
        if (selectFields.includes(formKey) && options[formKey]) {
          const match = options[formKey].find((o) => String(o).toLowerCase() === val.toLowerCase());
          newForm[formKey] = match || val;
        } else {
          newForm[formKey] = val;
        }
      }
    });
    setForm(newForm);
    setResult(null);
    setError(null);
    setStep(0);
  };

  useEffect(() => {
    fetchOptions()
      .then((data) => {
        if (data.options) setOptions((prev) => ({ ...prev, ...data.options }));
        if (data.numeric_ranges) setRanges(data.numeric_ranges);
      })
      .catch(() => {});
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
    cur.fields
      .filter((f) => numericFields.includes(f))
      .every((f) => !rangeError(f));

  const handleChange = (k, v) => {
    setForm((p) => ({ ...p, [k]: v }));
    setError(null);
  };

  const handleNext = () => {
    if (!isValid()) {
      setError("Veuillez remplir tous les champs correctement.");
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
      setError("Veuillez remplir tous les champs correctement.");
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
      const data = await predictPrice(payload);
      setResult(data);
    } catch (e) {
      setError(e.message || "Impossible de contacter l'API.");
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    const price =
      typeof result.predicted_price === "number"
        ? result.predicted_price.toLocaleString("fr-TN", {
            maximumFractionDigits: 0,
          })
        : "—";
    return (
      <ScrollView style={st.container} contentContainerStyle={st.resultContent}>
        <View style={st.resultCard}>
          <Text style={st.resultEmoji}>🏆</Text>
          <Text style={st.resultLabel}>Prix estimé pour votre véhicule</Text>
          <Text style={st.resultPrice}>
            {price}
            <Text style={st.resultCurrency}> TND</Text>
          </Text>

          <View style={st.tagRow}>
            <View style={st.tag}>
              <Text style={st.tagText}>📍 {form.Marque}</Text>
            </View>
            <View style={st.tag}>
              <Text style={st.tagText}>📅 {form.age_voiture} ans</Text>
            </View>
            <View style={st.tag}>
              <Text style={st.tagText}>
                🛣️ {Number(form.Kilometrage).toLocaleString()} km
              </Text>
            </View>
            <View style={st.tag}>
              <Text style={st.tagText}>⚡ {form.Energie}</Text>
            </View>
            <View style={st.tag}>
              <Text style={st.tagText}>⚙️ {form.Boite_vitesse}</Text>
            </View>
            <View style={st.tag}>
              <Text style={st.tagText}>🏎️ {form.Carrosserie}</Text>
            </View>
          </View>

          <TouchableOpacity
            style={st.resetBtn}
            onPress={handleReset}
            activeOpacity={0.7}
          >
            <Text style={st.resetText}>↩ Nouvelle estimation</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  }

  return (
    <View style={st.wrapper}>
    <ScrollView
      style={st.container}
      contentContainerStyle={st.formContent}
      keyboardShouldPersistTaps="handled"
    >
      {}
      <View style={st.header}>
        <Text style={st.headerTag}>Formulaire de prédiction</Text>
        <Text style={st.headerTitle}>Renseignez votre véhicule</Text>
        <Text style={st.headerSub}>
          Complétez les 4 étapes pour obtenir votre estimation
        </Text>
      </View>

      {}
      <View style={st.stepBar}>
        {steps.map((s, i) => (
          <React.Fragment key={s.id}>
            <TouchableOpacity
              onPress={() => i < step && setStep(i)}
              activeOpacity={i < step ? 0.6 : 1}
            >
              <View
                style={[
                  st.stepCircle,
                  i < step
                    ? st.stepDone
                    : i === step
                    ? st.stepActive
                    : st.stepPending,
                ]}
              >
                <Text
                  style={[
                    st.stepIcon,
                    i < step && { color: colors.gold },
                    i === step && { color: colors.bg },
                  ]}
                >
                  {i < step ? "✓" : s.icon}
                </Text>
              </View>
            </TouchableOpacity>
            {i < steps.length - 1 && (
              <View
                style={[
                  st.stepLine,
                  { backgroundColor: i < step ? colors.gold : colors.cardBorder },
                ]}
              />
            )}
          </React.Fragment>
        ))}
      </View>
      <Text style={st.stepLabel}>
        {cur.icon} {cur.title} — Étape {step + 1}/{steps.length}
      </Text>

      {}
      <View style={st.fieldsWrap}>
        {cur.fields.map((field) => {
          if (selectFields.includes(field)) {
            return (
              <View key={field} style={st.fieldGroup}>
                <Text style={st.label}>{fieldLabels[field]}</Text>
                <TouchableOpacity
                  style={st.selectBtn}
                  onPress={() => setPickerField(field)}
                  activeOpacity={0.7}
                >
                  <Text
                    style={[
                      st.selectText,
                      !form[field] && { color: colors.textDimmer },
                    ]}
                  >
                    {form[field] || "— Sélectionner —"}
                  </Text>
                  <Text style={st.selectArrow}>▾</Text>
                </TouchableOpacity>
              </View>
            );
          }

          const r = ranges[field];
          const rErr = rangeError(field);
          return (
            <View key={field} style={st.fieldGroup}>
              <Text style={st.label}>
                {fieldLabels[field]}
                {r && (
                  <Text style={st.rangeHint}>
                    {" "}
                    ({r.min} – {r.max})
                  </Text>
                )}
              </Text>
              <TextInput
                style={[st.input, rErr && { borderColor: colors.error }]}
                keyboardType="numeric"
                placeholder={r ? `${r.min} – ${r.max}` : "0"}
                placeholderTextColor={colors.textDimmer}
                value={form[field]}
                onChangeText={(v) => handleChange(field, v)}
              />
              {rErr && <Text style={st.fieldErr}>{rErr}</Text>}
            </View>
          );
        })}
      </View>

      {}
      {error && (
        <View style={st.errorBox}>
          <Text style={st.errorText}>⚠ {error}</Text>
        </View>
      )}

      {}
      <View style={st.btnRow}>
        {step > 0 && (
          <TouchableOpacity
            style={st.backBtn}
            onPress={handleBack}
            activeOpacity={0.7}
          >
            <Text style={st.backText}>← Retour</Text>
          </TouchableOpacity>
        )}
        {step < steps.length - 1 ? (
          <TouchableOpacity
            style={st.nextBtn}
            onPress={handleNext}
            activeOpacity={0.8}
          >
            <Text style={st.nextText}>Suivant →</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={[st.submitBtn, loading && { opacity: 0.7 }]}
            onPress={handleSubmit}
            disabled={loading}
            activeOpacity={0.8}
          >
            {loading ? (
              <ActivityIndicator color={colors.bg} />
            ) : (
              <Text style={st.submitText}>🔮 Prédire le prix</Text>
            )}
          </TouchableOpacity>
        )}
      </View>

      {}
      <PickerModal
        visible={!!pickerField}
        title={pickerField ? fieldLabels[pickerField] : ""}
        options={pickerField ? options[pickerField] || [] : []}
        onSelect={(v) => handleChange(pickerField, v)}
        onClose={() => setPickerField(null)}
      />
    </ScrollView>

    {}
    <TouchableOpacity
      style={st.chatFab}
      onPress={() => setChatVisible(true)}
      activeOpacity={0.8}
    >
      <Text style={st.chatFabIcon}>🤖</Text>
    </TouchableOpacity>

    {}
    <ChatBot
      visible={chatVisible}
      onClose={() => setChatVisible(false)}
      onAutofill={handleAutofill}
    />
    </View>
  );
}

const st = StyleSheet.create({
  wrapper: { flex: 1, backgroundColor: colors.bg },
  container: { flex: 1, backgroundColor: colors.bg },
  formContent: { padding: 20, paddingBottom: 40 },
  resultContent: {
    flexGrow: 1,
    justifyContent: "center",
    padding: 20,
  },

  header: { alignItems: "center", marginBottom: 24 },
  headerTag: {
    fontSize: 10,
    letterSpacing: 3,
    textTransform: "uppercase",
    color: colors.gold,
    opacity: 0.8,
    marginBottom: 6,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: "800",
    color: colors.text,
    letterSpacing: 1,
    marginBottom: 6,
  },
  headerSub: { fontSize: 13, color: colors.textDim },

  stepBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 8,
  },
  stepCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  stepActive: {
    backgroundColor: colors.gold,
    shadowColor: colors.gold,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.4,
    shadowRadius: 12,
    elevation: 6,
  },
  stepDone: {
    backgroundColor: colors.goldDim,
    borderWidth: 1,
    borderColor: colors.gold,
  },
  stepPending: {
    backgroundColor: "rgba(255,255,255,0.03)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.07)",
  },
  stepIcon: { fontSize: 16, color: colors.textDimmer },
  stepLine: { width: 30, height: 1, marginHorizontal: 4 },
  stepLabel: {
    textAlign: "center",
    fontSize: 14,
    fontWeight: "600",
    color: colors.text,
    marginBottom: 20,
  },

  fieldsWrap: { gap: 14 },
  fieldGroup: { marginBottom: 2 },
  label: {
    fontSize: 10,
    fontWeight: "600",
    letterSpacing: 1.5,
    textTransform: "uppercase",
    color: colors.gold,
    opacity: 0.72,
    marginBottom: 6,
  },
  rangeHint: { fontSize: 9, opacity: 0.55, fontWeight: "400" },
  input: {
    backgroundColor: colors.inputBg,
    borderWidth: 1,
    borderColor: colors.inputBorder,
    borderRadius: 10,
    padding: 12,
    fontSize: 14,
    color: colors.text,
  },
  fieldErr: {
    fontSize: 11,
    color: colors.errorText,
    marginTop: 3,
  },
  selectBtn: {
    backgroundColor: colors.inputBg,
    borderWidth: 1,
    borderColor: colors.inputBorder,
    borderRadius: 10,
    padding: 12,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  selectText: { fontSize: 14, color: colors.text },
  selectArrow: { fontSize: 12, color: colors.gold },

  errorBox: {
    backgroundColor: colors.errorBg,
    borderWidth: 1,
    borderColor: colors.errorBorder,
    borderRadius: 10,
    padding: 12,
    marginTop: 14,
  },
  errorText: { color: colors.errorText, fontSize: 13 },

  btnRow: {
    flexDirection: "row",
    justifyContent: "flex-end",
    gap: 10,
    marginTop: 20,
  },
  backBtn: {
    borderWidth: 1,
    borderColor: "rgba(201,162,39,0.25)",
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 22,
  },
  backText: { color: colors.gold, fontSize: 14 },
  nextBtn: {
    backgroundColor: colors.gold,
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 28,
    shadowColor: colors.gold,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.3,
    shadowRadius: 14,
    elevation: 6,
  },
  nextText: { color: colors.bg, fontSize: 14, fontWeight: "700" },
  submitBtn: {
    backgroundColor: colors.gold,
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 30,
    shadowColor: colors.gold,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.35,
    shadowRadius: 18,
    elevation: 8,
  },
  submitText: { color: colors.bg, fontSize: 15, fontWeight: "700" },

  resultCard: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 24,
    padding: 32,
    alignItems: "center",
  },
  resultEmoji: { fontSize: 48, marginBottom: 14 },
  resultLabel: {
    fontSize: 10,
    letterSpacing: 4,
    textTransform: "uppercase",
    color: colors.gold,
    opacity: 0.75,
    marginBottom: 14,
    textAlign: "center",
  },
  resultPrice: {
    fontSize: 52,
    fontWeight: "900",
    color: colors.text,
    textAlign: "center",
    marginBottom: 8,
  },
  resultCurrency: {
    fontSize: 22,
    color: colors.gold,
    fontWeight: "700",
  },
  tagRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "center",
    gap: 8,
    marginVertical: 20,
    padding: 14,
    backgroundColor: "rgba(255,255,255,0.025)",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  tag: {
    backgroundColor: colors.goldDim,
    borderRadius: 18,
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  tagText: { fontSize: 12, color: colors.gold },
  resetBtn: {
    borderWidth: 1,
    borderColor: "rgba(201,162,39,0.32)",
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 24,
  },
  resetText: { color: colors.gold, fontSize: 14 },

  chatFab: {
    position: "absolute",
    bottom: 30,
    right: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.gold,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: colors.gold,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.4,
    shadowRadius: 14,
    elevation: 8,
    zIndex: 100,
  },
  chatFabIcon: { fontSize: 26 },
});
