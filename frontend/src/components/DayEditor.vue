<template>
  <section style="display:grid; gap:18px;">
    <h2>День: {{ localDay.date }}</h2>

    <fieldset style="border:1px solid #ddd; padding:12px; border-radius:10px;">
      <legend>Раз в сутки</legend>

      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
        <div>
          <label>Осадки (мм)</label><br />
          <input type="number" step="0.1" v-model.number="localDay.precip_mm" />
        </div>

        <div>
          <label>Облачность</label><br />
          <select v-model="localDay.cloudiness">
            <option disabled value="">— выбрать —</option>
            <option value="ясная">ясная</option>
            <option value="переменная">переменная</option>
            <option value="сплошная">сплошная</option>
          </select>
        </div>

        <div>
          <label>Ветер: скорость (м/с)</label><br />
          <input type="number" step="0.1" min="0" v-model.number="windSpeed" />
        </div>

        <div>
          <label>Ветер: направление</label><br />
          <select v-model="windDir">
            <option value="С">С</option>
            <option value="СВ">СВ</option>
            <option value="В">В</option>
            <option value="ЮВ">ЮВ</option>
            <option value="Ю">Ю</option>
            <option value="ЮЗ">ЮЗ</option>
            <option value="З">З</option>
            <option value="СЗ">СЗ</option>
          </select>
        </div>
      </div>
    </fieldset>

    <fieldset style="border:1px solid #ddd; padding:12px; border-radius:10px;">
      <legend>Температура и влажность (фиксировано: 07:00 / 13:00 / 20:00)</legend>

      <table style="width:100%; border-collapse: collapse;">
        <thead>
          <tr>
            <th align="left">Время</th>
            <th align="left">Темп (°C)</th>
            <th align="left">RH (%)</th>
            <th align="left">Очистить</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in FIXED_TIMES" :key="t">
            <td style="padding:6px 0; white-space:nowrap;"><strong>{{ t }}</strong></td>

            <td>
              <input
                type="number"
                step="0.1"
                :value="airMap[t].temp_c ?? ''"
                @input="setTemp(t, ($event.target as HTMLInputElement).value)"
                placeholder="—"
              />
            </td>

            <td>
              <input
                type="number"
                min="0"
                max="100"
                :value="airMap[t].rh_pct ?? ''"
                @input="setRh(t, ($event.target as HTMLInputElement).value)"
                placeholder="—"
              />
            </td>

            <td>
              <button @click="clearPoint(t)">Очистить</button>
            </td>
          </tr>
        </tbody>
      </table>

      <p style="margin-top:10px; opacity:.75;">
        Пустые значения сохраняются как “нет измерения”.
      </p>
    </fieldset>

    <div>
      <label>Заметки</label><br />
      <textarea v-model="localDay.notes" rows="3" style="width:100%;"></textarea>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { ObservationDay } from "../api";

const props = defineProps<{ day: ObservationDay }>();
const emit = defineEmits<{ (e: "update:day", v: ObservationDay): void }>();

const localDay = props.day;

// фиксированные времена
const FIXED_TIMES = ["07:00", "13:00", "20:00"] as const;

type FixedTime = (typeof FIXED_TIMES)[number];

function normalizeAir(day: ObservationDay) {
  // строим карту по фиксированным временам, подтягивая существующие данные
  const map: Record<FixedTime, { time: FixedTime; temp_c: number | null; rh_pct: number | null }> = {
    "07:00": { time: "07:00", temp_c: null, rh_pct: null },
    "13:00": { time: "13:00", temp_c: null, rh_pct: null },
    "20:00": { time: "20:00", temp_c: null, rh_pct: null }
  };

  for (const p of day.air ?? []) {
    if ((FIXED_TIMES as readonly string[]).includes(p.time)) {
      const t = p.time as FixedTime;
      map[t].temp_c = (p as any).temp_c ?? null;
      map[t].rh_pct = (p as any).rh_pct ?? null;
    }
  }
  return map;
}

const airMap = computed(() => normalizeAir(localDay));

function commit(map: ReturnType<typeof normalizeAir>) {
  // сохраняем ровно 3 точки, фиксированные времена
  localDay.air = FIXED_TIMES.map((t) => ({
    time: t,
    temp_c: map[t].temp_c ?? null,
    rh_pct: map[t].rh_pct ?? null
  })) as any;

  emit("update:day", localDay);
}

function setTemp(t: FixedTime, raw: string) {
  const map = normalizeAir(localDay);
  map[t].temp_c = raw === "" ? null : Number(raw);
  commit(map);
}

function setRh(t: FixedTime, raw: string) {
  const map = normalizeAir(localDay);
  map[t].rh_pct = raw === "" ? null : Number(raw);
  commit(map);
}

function clearPoint(t: FixedTime) {
  const map = normalizeAir(localDay);
  map[t].temp_c = null;
  map[t].rh_pct = null;
  commit(map);
}

const windSpeed = computed({
  get: () => localDay.wind?.speed_mps ?? 0,
  set: (v: number) => {
    localDay.wind = { speed_mps: v, dir: localDay.wind?.dir ?? "С" };
    emit("update:day", localDay);
  }
});

const windDir = computed({
  get: () => localDay.wind?.dir ?? "С",
  set: (v: any) => {
    localDay.wind = { speed_mps: localDay.wind?.speed_mps ?? 0, dir: v };
    emit("update:day", localDay);
  }
});
</script>
