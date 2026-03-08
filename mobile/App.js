import React, { useState, useEffect } from "react";
import { StatusBar } from "expo-status-bar";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import AsyncStorage from "@react-native-async-storage/async-storage";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { colors } from "./src/theme";
import { checkHealth } from "./src/api";

import AuthScreen from "./src/screens/AuthScreen";
import HomeScreen from "./src/screens/HomeScreen";
import PredictScreen from "./src/screens/PredictScreen";

const Stack = createNativeStackNavigator();

// ─── Header component for main screens ───────────────────────────────────────
function MainHeader({ navigation, user, apiStatus, onLogout }) {
  return (
    <View style={hdr.container}>
      <TouchableOpacity
        onPress={() => navigation.navigate("Home")}
        style={hdr.logoRow}
      >
        <Text style={hdr.logoMark}>◈</Text>
        <Text style={hdr.logoText}>
          AutoPredict <Text style={hdr.logoGold}>TN</Text>
        </Text>
      </TouchableOpacity>
      <View style={hdr.right}>
        <View style={hdr.statusPill}>
          <View
            style={[
              hdr.dot,
              {
                backgroundColor:
                  apiStatus === "online"
                    ? "#00ff88"
                    : apiStatus === "offline"
                    ? "#ff4455"
                    : "#ffaa00",
              },
            ]}
          />
          <Text style={hdr.statusText}>
            {apiStatus === "online"
              ? "API"
              : apiStatus === "offline"
              ? "Hors ligne"
              : "..."}
          </Text>
        </View>
        {user && (
          <TouchableOpacity onPress={onLogout} style={hdr.logoutBtn}>
            <Text style={hdr.logoutText}>⏻</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

const hdr = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: colors.bg,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
    paddingHorizontal: 16,
    paddingVertical: 12,
    paddingTop: 48,
  },
  logoRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  logoMark: { fontSize: 18, color: colors.gold },
  logoText: {
    fontSize: 18,
    fontWeight: "700",
    color: colors.text,
    letterSpacing: 1.5,
  },
  logoGold: { color: colors.gold },
  right: { flexDirection: "row", alignItems: "center", gap: 10 },
  statusPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    backgroundColor: "rgba(255,255,255,0.04)",
    borderRadius: 12,
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  dot: { width: 6, height: 6, borderRadius: 3 },
  statusText: { fontSize: 10, color: colors.textDim },
  logoutBtn: {
    backgroundColor: "rgba(255,68,85,0.08)",
    borderWidth: 1,
    borderColor: "rgba(255,68,85,0.2)",
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  logoutText: { fontSize: 14, color: "#ff6677" },
});

// ─── Tab-like bottom nav for main screens ────────────────────────────────────
function BottomNav({ current, onNavigate }) {
  const tabs = [
    { key: "Home", icon: "🏠", label: "Accueil" },
    { key: "Predict", icon: "🔮", label: "Prédiction" },
  ];
  return (
    <View style={bn.container}>
      {tabs.map((t) => (
        <TouchableOpacity
          key={t.key}
          style={[bn.tab, current === t.key && bn.tabActive]}
          onPress={() => onNavigate(t.key)}
          activeOpacity={0.7}
        >
          <Text style={bn.icon}>{t.icon}</Text>
          <Text style={[bn.label, current === t.key && bn.labelActive]}>
            {t.label}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

const bn = StyleSheet.create({
  container: {
    flexDirection: "row",
    backgroundColor: "rgba(8,18,32,0.97)",
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
    paddingBottom: 20,
    paddingTop: 10,
  },
  tab: {
    flex: 1,
    alignItems: "center",
    paddingVertical: 6,
  },
  tabActive: {},
  icon: { fontSize: 20, marginBottom: 2 },
  label: { fontSize: 10, color: colors.textDim, letterSpacing: 0.5 },
  labelActive: { color: colors.gold, fontWeight: "600" },
});

// ─── Main screen wrapper with tabs ───────────────────────────────────────────
function MainScreen({ navigation }) {
  const [currentTab, setCurrentTab] = useState("Home");
  const [user, setUser] = useState(null);
  const [apiStatus, setApiStatus] = useState(null);

  useEffect(() => {
    AsyncStorage.getItem("ap_user").then((u) => {
      if (u) setUser(JSON.parse(u));
    });
    checkHealth()
      .then(setApiStatus)
      .catch(() => setApiStatus("offline"));
  }, []);

  const handleLogout = async () => {
    await AsyncStorage.removeItem("ap_token");
    await AsyncStorage.removeItem("ap_user");
    navigation.reset({ index: 0, routes: [{ name: "Auth" }] });
  };

  return (
    <View style={{ flex: 1, backgroundColor: colors.bg }}>
      <MainHeader
        navigation={{ navigate: (k) => setCurrentTab(k) }}
        user={user}
        apiStatus={apiStatus}
        onLogout={handleLogout}
      />
      <View style={{ flex: 1 }}>
        {currentTab === "Home" && (
          <HomeScreen navigation={{ navigate: (k) => setCurrentTab(k) }} />
        )}
        {currentTab === "Predict" && (
          <PredictScreen navigation={{ navigate: (k) => setCurrentTab(k) }} />
        )}
      </View>
      <BottomNav current={currentTab} onNavigate={setCurrentTab} />
    </View>
  );
}

// ─── Root App ────────────────────────────────────────────────────────────────
export default function App() {
  const [initialRoute, setInitialRoute] = useState(null);

  useEffect(() => {
    AsyncStorage.getItem("ap_token").then((token) => {
      setInitialRoute(token ? "Main" : "Auth");
    });
  }, []);

  if (!initialRoute) {
    return (
      <View
        style={{
          flex: 1,
          backgroundColor: colors.bg,
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <ActivityIndicator color={colors.gold} size="large" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <Stack.Navigator
        initialRouteName={initialRoute}
        screenOptions={{ headerShown: false }}
      >
        <Stack.Screen name="Auth" component={AuthScreen} />
        <Stack.Screen name="Main" component={MainScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
