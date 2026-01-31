<template>
  <section style="border:1px solid #ddd; border-radius:12px; padding:14px; max-width:420px;">
    <h2 style="margin:0 0 10px 0;">Вход</h2>

    <div style="display:grid; gap:10px;">
      <div>
        <label>Логин</label><br />
        <input v-model="u" autocomplete="username" />
      </div>

      <div>
        <label>Пароль</label><br />
        <input v-model="p" type="password" autocomplete="current-password" />
      </div>

      <div style="display:flex; gap:10px; align-items:center;">
        <button @click="doLogin">Войти</button>
        <span v-if="err" style="color:#b00;">{{ err }}</span>
      </div>

      <p style="margin:0; opacity:.7; font-size:13px;">
        Для прототипа используем Basic Auth. Лучше включать HTTPS, если доступ не только локальный.
      </p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { login } from "../api";

const emit = defineEmits<{ (e: "logged-in"): void }>();

const u = ref("");
const p = ref("");
const err = ref("");

async function doLogin() {
  err.value = "";
  try {
    await login(u.value, p.value);
    emit("logged-in");
  } catch (e: any) {
    err.value = e.message === "UNAUTHORIZED" ? "Неверный логин/пароль" : ("Ошибка: " + e.message);
  }
}
</script>
