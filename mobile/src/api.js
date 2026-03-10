const API_URL = "http://192.168.0.3:8000";

export { API_URL };

export async function loginUser(email, password) {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Erreur serveur");
  return data;
}

export async function registerUser({ full_name, email, password, telephone }) {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ full_name, email, password, telephone }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Erreur serveur");
  return data;
}

export async function fetchOptions() {
  const res = await fetch(`${API_URL}/options`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Erreur serveur");
  return data;
}

export async function predictPrice(payload) {
  const res = await fetch(`${API_URL}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Erreur serveur");
  return data;
}

export async function autofillCar(query, history = []) {
  const res = await fetch(`${API_URL}/autofill`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, history }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Erreur serveur");
  return data;
}

export async function checkHealth() {
  const res = await fetch(`${API_URL}/health`);
  return res.ok ? "online" : "offline";
}
