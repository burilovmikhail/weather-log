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

export async function getDay(date: string): Promise<ObservationDay | null> {
  const r = await fetch(`/api/observations/${date}`);
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function putDay(day: ObservationDay): Promise<ObservationDay> {
  const r = await fetch(`/api/observations/${day.date}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(day)
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function listDays(from?: string, to?: string): Promise<ObservationDay[]> {
  const params = new URLSearchParams();
  if (from) params.set("from", from);
  if (to) params.set("to", to);

  const url = `/api/observations${params.toString() ? "?" + params.toString() : ""}`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}