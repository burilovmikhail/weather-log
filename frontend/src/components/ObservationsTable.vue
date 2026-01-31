<template>
  <section style="margin-top:24px;">
    <div style="display:flex; gap:12px; align-items:end; flex-wrap:wrap;">
      <div>
        <label>От</label><br />
        <input type="date" v-model="from" />
      </div>
      <div>
        <label>До</label><br />
        <input type="date" v-model="to" />
      </div>
      <button @click="reload">Показать</button>
      <span v-if="status" style="opacity:.8">{{ status }}</span>
    </div>

    <div style="overflow:auto; margin-top:12px; border:1px solid #ddd; border-radius:10px;">
      <table style="width:100%; border-collapse:collapse; min-width:900px;">
        <thead>
          <tr style="background:#f7f7f7;">
            <th style="text-align:left; padding:10px; border-bottom:1px solid #ddd;">Дата</th>
            <th style="text-align:left; padding:10px; border-bottom:1px solid #ddd;">Облачность</th>
            <th style="text-align:left; padding:10px; border-bottom:1px solid #ddd;">Осадки (мм)</th>
            <th style="text-align:left; padding:10px; border-bottom:1px solid #ddd;">Ветер</th>

            <th style="text-align:left; padding:10px; border-bottom:1px solid #ddd;">07:00</th>
            <th style="text-align:left; padding:10px; border-bottom:1px solid #ddd;">13:00</th>
            <th style="text-align:left; padding:10px; border-bottom:1px solid #ddd;">20:00</th>

            <th style="text-align:left; padding:10px; border-bottom:1px solid #ddd;">
            Средняя T
            </th>            

            <th style="text-align:left; padding:10px; border-bottom:1px solid #ddd;">Заметки</th>
            <th style="text-align:left; padding:10px; border-bottom:1px solid #ddd;"></th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="d in rows" :key="d.date">
            <td style="padding:10px; border-bottom:1px solid #eee; white-space:nowrap;">
              {{ d.date }}
            </td>

            <td style="padding:10px; border-bottom:1px solid #eee; white-space:nowrap;">
              <span :title="d.cloudiness ?? ''" style="font-size:18px; margin-right:6px;">
                {{ cloudIcon(d) }}
              </span>
              <span style="opacity:.85">{{ d.cloudiness ?? "—" }}</span>
            </td>

            <td style="padding:10px; border-bottom:1px solid #eee;">
              {{ formatNum(d.precip_mm) }}
            </td>

            <td style="padding:10px; border-bottom:1px solid #eee; white-space:nowrap;">
              <span v-if="d.wind">
                {{ formatNum(d.wind.speed_mps) }} м/с, {{ d.wind.dir }}
              </span>
              <span v-else>—</span>
            </td>

            <td style="padding:10px; border-bottom:1px solid #eee;">
              {{ airCell(d, "07:00") }}
            </td>
            <td style="padding:10px; border-bottom:1px solid #eee;">
              {{ airCell(d, "13:00") }}
            </td>
            <td style="padding:10px; border-bottom:1px solid #eee;">
              {{ airCell(d, "20:00") }}
            </td>

            <td style="padding:10px; border-bottom:1px solid #eee; white-space:nowrap;">
            {{ avgTemp(d) }}
            </td>            

            <td style="padding:10px; border-bottom:1px solid #eee; max-width:280px;">
              <span v-if="d.notes">{{ d.notes }}</span><span v-else>—</span>
            </td>

            <td style="padding:10px; border-bottom:1px solid #eee; white-space:nowrap;">
              <button @click="$emit('open', d.date)">Открыть</button>
            </td>
          </tr>

          <tr v-if="rows.length === 0">
            <td colspan="9" style="padding:14px; opacity:.7;">Нет данных за выбранный период.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { listDays, type ObservationDay } from "../api";

defineEmits<{ (e: "open", date: string): void }>();
defineExpose({ reload });

const today = new Date().toISOString().slice(0, 10);
const from = ref(today.slice(0, 8) + "01"); // первое число месяца
const to = ref(today);
const rows = ref<ObservationDay[]>([]);
const status = ref("");

async function reload() {
  status.value = "Загрузка...";
  try {
    rows.value = await listDays(from.value, to.value);
    status.value = `Готово: ${rows.value.length}`;
  } catch (e: any) {
    status.value = "Ошибка: " + e.message;
  }
}


function cloudIcon(d: ObservationDay) {
  // "дождик" при осадках — обычно ожидаемое поведение
  if ((d.precip_mm ?? 0) > 0) return "🌧️";
  if (d.cloudiness === "ясная") return "☀️";
  if (d.cloudiness === "переменная") return "⛅";
  if (d.cloudiness === "сплошная") return "☁️";
  return "—";
}

function airCell(d: ObservationDay, time: string) {
  const p = d.air?.find((x) => x.time === time);
  if (!p) return "—";
  return `${formatNum(p.temp_c)}°C / ${formatNum(p.rh_pct)}%`;
}

function formatNum(v: any) {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return Number(v).toString();
}

function avgTemp(d: ObservationDay): string {
  if (!d.air || d.air.length === 0) return "—";

  const vals = d.air
    .map(p => p.temp_c)
    .filter(v => typeof v === "number") as number[];

  if (vals.length === 0) return "—";

  const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
  return avg.toFixed(1) + "°C";
}


// можно автозагружать при старте
reload();
</script>
