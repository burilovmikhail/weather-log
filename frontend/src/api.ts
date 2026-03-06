export type AirPoint = { time: string; temp_c: number | null; rh_pct: number | null };

export type WindDir = "С" | "СВ" | "В" | "ЮВ" | "Ю" | "ЮЗ" | "З" | "СЗ";
export type Cloudiness = "ясная" | "переменная" | "сплошная";

export type Wind = {
  speed_mps: number;
  dir: WindDir;
};

export type ObservationDay = {
  date: string;
  precip_mm?: number | null;
  cloudiness?: Cloudiness | null;
  wind?: Wind | null;
  air: AirPoint[];
  notes?: string | null;
};


const TOKEN_KEY = "meteo_token";

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function authHeader(): Record<string, string> {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

async function apiFetch(input: RequestInfo, init: RequestInit = {}) {
  const headers = {
    ...(init.headers || {}),
    ...authHeader(),
  } as Record<string, string>;

  const r = await fetch(input, { ...init, headers });

  if (r.status === 401) throw new Error("UNAUTHORIZED");
  if (!r.ok) throw new Error(await r.text());
  return r;
}

export async function login(username: string, password: string): Promise<void> {
  const r = await fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (r.status === 401) throw new Error("UNAUTHORIZED");
  if (!r.ok) throw new Error(await r.text());
  const data = await r.json();
  setToken(data.access_token);
}

export async function getDay(date: string): Promise<ObservationDay | null> {
  const r = await fetch(`/api/observations/${date}`, {
    headers: {
      ...authHeader(),
    },
  });

  if (r.status === 401) throw new Error("UNAUTHORIZED");
  if (r.status === 404) return null;

  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function putDay(day: ObservationDay): Promise<ObservationDay> {
  const r = await apiFetch(`/api/observations/${day.date}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(day)
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export type SyncResponse = {
  synced: string[];
  skipped: string[];
  errors: Record<string, string>;
};

export async function syncDays(): Promise<SyncResponse> {
  const r = await apiFetch("/api/sync", { method: "POST" });
  return r.json();
}

export async function listDays(from?: string, to?: string): Promise<ObservationDay[]> {
  const params = new URLSearchParams();
  if (from) params.set("from", from);
  if (to) params.set("to", to);

  const url = `/api/observations${params.toString() ? "?" + params.toString() : ""}`;
  const r = await apiFetch(url);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}