import React, { useState, useRef, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Modal,
  FlatList,
  Animated,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from "react-native";
import { colors } from "../theme";
import { autofillCar } from "../api";
import { fieldLabels } from "../data";

const WELCOME_TEXT =
  "👋 Bonjour ! Je suis votre assistant IA automobile.\n\nDécrivez-moi la voiture que vous cherchez et je remplirai le formulaire pour vous.\n\nExemples :\n• \"Peugeot 308 diesel 2019\"\n• \"Golf 7 automatique 80 000 km\"\n• \"je cherche une Clio 4 essence manuelle\"";

// ─── Chat message component ──────────────────────────────────────────────────
function ChatMessage({ msg, onApply }) {
  const fade = useRef(new Animated.Value(0)).current;
  const slide = useRef(new Animated.Value(20)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fade, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.timing(slide, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const isBot = msg.role === "bot";

  return (
    <Animated.View
      style={[
        cs.msgRow,
        isBot ? cs.msgRowBot : cs.msgRowUser,
        { opacity: fade, transform: [{ translateY: slide }] },
      ]}
    >
      {isBot && <Text style={cs.avatar}>🤖</Text>}
      <View style={[cs.bubble, isBot ? cs.bubbleBot : cs.bubbleUser]}>
        <Text style={[cs.msgText, isBot ? cs.msgTextBot : cs.msgTextUser]}>
          {msg.text}
        </Text>

        {/* Show autofill summary */}
        {msg.autofillData && (
          <View style={cs.autofillPreview}>
            {Object.entries(msg.autofillData)
              .filter(([k]) => fieldLabels[k] && msg.autofillData[k] != null)
              .map(([k, v]) => (
                <View key={k} style={cs.previewRow}>
                  <Text style={cs.previewLabel}>{fieldLabels[k]}</Text>
                  <Text style={cs.previewValue}>{String(v)}</Text>
                </View>
              ))}
            <TouchableOpacity
              style={cs.applyBtn}
              onPress={() => onApply(msg.autofillData)}
              activeOpacity={0.7}
            >
              <Text style={cs.applyText}>✅ Appliquer au formulaire</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
      {!isBot && <Text style={cs.avatar}>👤</Text>}
    </Animated.View>
  );
}

// ─── Main ChatBot Component ─────────────────────────────────────────────────
export default function ChatBot({ visible, onClose, onAutofill }) {
  const [messages, setMessages] = useState([
    { id: "welcome", role: "bot", text: WELCOME_TEXT },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const flatListRef = useRef(null);

  const addMessage = (msg) => {
    setMessages((prev) => [
      ...prev,
      { ...msg, id: String(Date.now()) + Math.random() },
    ]);
  };

  const scrollToEnd = () => {
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 100);
  };

  // Build chat history for LLM context
  const buildHistory = () =>
    messages
      .filter((m) => m.id !== "welcome")
      .map((m) => ({ role: m.role === "bot" ? "bot" : "user", text: m.text }));

  const handleSend = async () => {
    const query = input.trim();
    if (!query || loading) return;

    addMessage({ role: "user", text: query });
    setInput("");
    setLoading(true);
    scrollToEnd();

    try {
      const history = buildHistory();
      const data = await autofillCar(query, history);

      if (data.matched && !data.parse_error) {
        const hasFields = Object.keys(data).some(
          (k) => fieldLabels[k] && data[k] != null
        );
        addMessage({
          role: "bot",
          text: data.message || "🎯 Voici les caractéristiques identifiées :",
          autofillData: hasFields ? data : undefined,
        });
      } else if (data.parse_error) {
        addMessage({
          role: "bot",
          text: data.message || "Je n'ai pas pu structurer ma réponse. Réessayez avec plus de détails.",
        });
      } else {
        addMessage({
          role: "bot",
          text: data.message || "❌ Je n'ai pas pu identifier cette voiture. Essayez avec plus de détails.",
        });
      }
    } catch (e) {
      addMessage({
        role: "bot",
        text: `⚠️ ${e.message || "Impossible de contacter le serveur."}`,
      });
    } finally {
      setLoading(false);
      scrollToEnd();
    }
  };

  const handleApply = (data) => {
    onAutofill(data);
    addMessage({
      role: "bot",
      text: "✅ Formulaire rempli !\n\nVous pouvez fermer le chat et ajuster les valeurs, ou me demander de modifier un champ.",
    });
    scrollToEnd();
  };

  const handleReset = () => {
    setMessages([{ id: "welcome", role: "bot", text: WELCOME_TEXT }]);
  };

  return (
    <Modal visible={visible} transparent animationType="slide">
      <KeyboardAvoidingView
        style={cs.overlay}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <View style={cs.container}>
          {/* Header */}
          <View style={cs.header}>
            <View style={cs.headerLeft}>
              <Text style={cs.headerEmoji}>🤖</Text>
              <View>
                <Text style={cs.headerTitle}>AutoBot IA</Text>
                <Text style={cs.headerSub}>Propulsé par Gemini</Text>
              </View>
            </View>
            <View style={cs.headerRight}>
              <TouchableOpacity onPress={handleReset} style={cs.headerBtn}>
                <Text style={cs.headerBtnText}>🔄</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={onClose} style={cs.headerBtn}>
                <Text style={cs.headerBtnText}>✕</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Messages */}
          <FlatList
            ref={flatListRef}
            data={messages}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <ChatMessage msg={item} onApply={handleApply} />
            )}
            style={cs.messageList}
            contentContainerStyle={cs.messageContent}
            onContentSizeChange={scrollToEnd}
          />

          {/* Loading indicator */}
          {loading && (
            <View style={cs.typingRow}>
              <Text style={cs.avatar}>🤖</Text>
              <View style={cs.typingBubble}>
                <ActivityIndicator size="small" color={colors.gold} />
                <Text style={cs.typingText}>L'IA réfléchit…</Text>
              </View>
            </View>
          )}

          {/* Input */}
          <View style={cs.inputRow}>
            <TextInput
              style={cs.input}
              placeholder="Décrivez votre voiture…"
              placeholderTextColor={colors.textDimmer}
              value={input}
              onChangeText={setInput}
              onSubmitEditing={handleSend}
              returnKeyType="send"
              editable={!loading}
            />
            <TouchableOpacity
              style={[
                cs.sendBtn,
                (!input.trim() || loading) && cs.sendBtnDisabled,
              ]}
              onPress={handleSend}
              disabled={!input.trim() || loading}
              activeOpacity={0.7}
            >
              <Text style={cs.sendIcon}>➤</Text>
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

// ─── Styles ──────────────────────────────────────────────────────────────────
const cs = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "flex-end",
  },
  container: {
    backgroundColor: "#04090f",
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    height: "85%",
    borderWidth: 1,
    borderColor: colors.cardBorder,
    overflow: "hidden",
  },

  // Header
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 18,
    paddingVertical: 14,
    backgroundColor: "rgba(201,162,39,0.08)",
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  headerLeft: { flexDirection: "row", alignItems: "center", gap: 10 },
  headerEmoji: { fontSize: 28 },
  headerTitle: {
    fontSize: 17,
    fontWeight: "700",
    color: colors.text,
  },
  headerSub: {
    fontSize: 11,
    color: colors.textDim,
  },
  headerRight: { flexDirection: "row", gap: 6 },
  headerBtn: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: "rgba(255,255,255,0.06)",
    alignItems: "center",
    justifyContent: "center",
  },
  headerBtnText: { fontSize: 16, color: colors.textDim },

  // Messages
  messageList: { flex: 1 },
  messageContent: { paddingHorizontal: 14, paddingVertical: 10 },

  msgRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: 12,
    gap: 8,
  },
  msgRowBot: { justifyContent: "flex-start" },
  msgRowUser: { justifyContent: "flex-end" },
  avatar: { fontSize: 20, marginTop: 4 },

  bubble: {
    maxWidth: "80%",
    borderRadius: 16,
    padding: 12,
  },
  bubbleBot: {
    backgroundColor: "rgba(201,162,39,0.1)",
    borderWidth: 1,
    borderColor: "rgba(201,162,39,0.2)",
    borderTopLeftRadius: 4,
  },
  bubbleUser: {
    backgroundColor: colors.gold,
    borderTopRightRadius: 4,
  },
  msgText: {
    fontSize: 14,
    lineHeight: 20,
  },
  msgTextBot: { color: colors.text },
  msgTextUser: { color: colors.bg, fontWeight: "500" },

  // Autofill preview
  autofillPreview: {
    marginTop: 10,
    backgroundColor: "rgba(0,0,0,0.2)",
    borderRadius: 12,
    padding: 10,
  },
  previewRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 4,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(255,255,255,0.05)",
  },
  previewLabel: {
    fontSize: 11,
    color: colors.textDim,
    flex: 1,
  },
  previewValue: {
    fontSize: 12,
    color: colors.gold,
    fontWeight: "600",
    textAlign: "right",
    flex: 1,
  },
  applyBtn: {
    marginTop: 10,
    backgroundColor: colors.gold,
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: "center",
  },
  applyText: {
    color: colors.bg,
    fontWeight: "700",
    fontSize: 13,
  },

  // Typing indicator
  typingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 14,
    paddingBottom: 8,
  },
  typingBubble: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    backgroundColor: "rgba(201,162,39,0.1)",
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  typingText: {
    fontSize: 12,
    color: colors.textDim,
    fontStyle: "italic",
  },

  // Input row
  inputRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
    backgroundColor: "rgba(8,18,32,0.95)",
    gap: 8,
  },
  input: {
    flex: 1,
    backgroundColor: "rgba(255,255,255,0.06)",
    borderWidth: 1,
    borderColor: colors.inputBorder,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 14,
    color: colors.text,
  },
  sendBtn: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: colors.gold,
    alignItems: "center",
    justifyContent: "center",
  },
  sendBtnDisabled: {
    opacity: 0.4,
  },
  sendIcon: {
    fontSize: 18,
    color: colors.bg,
    fontWeight: "700",
  },
});
