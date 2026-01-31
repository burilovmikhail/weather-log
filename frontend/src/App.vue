<template>
  <main style="max-width: 900px; margin: 40px auto; font-family: system-ui;">
    <h1>Meteo Log</h1>
    
    <LoginBox v-if="needAuth" @logged-in="onLoggedIn" />

    <template v-else>
      <section style="display:flex; gap:12px; align-items:end; margin:16px 0;">
        <div>
          <label>Дата</label><br />
          <input type="date" v-model="date" />
        </div>
        <button @click="load">Загрузить</button>
        <button @click="save" :disabled="!day">Сохранить</button>
        <span v-if="status" style="opacity:.8">{{ status }}</span>
      </section>

      <DayEditor v-if="day" v-model:day="day" />
      <p v-else style="opacity:.7">Выбери дату и нажми «Загрузить».</p>

      <ObservationsTable ref="tableRef" @unauthorized="needAuth = true" @open="openFromTable" />
    </template>
  </main>
</template>

<script setup lang="ts">
import { ref } from "vue";
import DayEditor from "./components/DayEditor.vue";
import ObservationsTable from "./components/ObservationsTable.vue";
import LoginBox from "./components/LoginBox.vue";
import { clearToken } from "./api";
import { getDay, putDay, type ObservationDay } from "./api";

const tableRef = ref<InstanceType<typeof ObservationsTable> | null>(null);

const needAuth = ref(!localStorage.getItem("meteo_token"));
const date = ref(new Date().toISOString().slice(0, 10));
const day = ref<ObservationDay | null>(null);
const status = ref("");

async function onLoggedIn() {
  needAuth.value = false;
  status.value = "";
  await tableRef.value?.reload();
}

function logout() {
  clearToken();
  needAuth.value = true;
  day.value = null;
}

async function load() {
  status.value = "Загрузка...";
  try {
    const existing = await getDay(date.value);
    day.value = existing ?? { date: date.value, air: [] };
    status.value = existing ? "Ок" : "Новый день";
  } catch (e: any) {
    if (e.message === "UNAUTHORIZED") {
      needAuth.value = true;
      status.value = "Нужна авторизация";
      return;
    }
    status.value = "Ошибка: " + e.message;
  }
}

async function save() {
  if (!day.value) return;
  status.value = "Сохранение...";
  try {
    day.value = await putDay(day.value);
    status.value = "Сохранено";

    day.value = null;               // закрыть редактор
    await tableRef.value?.reload(); // обновить таблицу    
  } catch (e: any) {
    if (e.message === "UNAUTHORIZED") {
      needAuth.value = true;
      status.value = "Нужна авторизация";
      return;
    }
    status.value = "Ошибка: " + e.message;
  }
}

async function openFromTable(d: string) {
  date.value = d;
  await load();
}
</script>
