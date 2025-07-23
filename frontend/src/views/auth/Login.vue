<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="elevation-12">
          <v-toolbar color="primary" dark flat>
            <v-toolbar-title>Vogelring Login</v-toolbar-title>
          </v-toolbar>
          <v-card-text>
            <v-form @submit.prevent="handleLogin" ref="form">
              <v-text-field
                v-model="username"
                label="Benutzername oder E-Mail"
                name="username"
                prepend-icon="mdi-account"
                type="text"
                :rules="[rules.required]"
                required
              />

              <v-text-field
                v-model="password"
                label="Passwort"
                name="password"
                prepend-icon="mdi-lock"
                :type="showPassword ? 'text' : 'password'"
                :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                @click:append="showPassword = !showPassword"
                :rules="[rules.required]"
                required
              />

              <v-alert
                v-if="authStore.error"
                type="error"
                dismissible
                @input="authStore.clearError"
                class="mb-4"
              >
                {{ authStore.error }}
              </v-alert>
            </v-form>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn
              color="primary"
              :loading="authStore.loading"
              @click="handleLogin"
              :disabled="!isFormValid"
            >
              Anmelden
            </v-btn>
          </v-card-actions>
          <v-divider />
          <v-card-text class="text-center">
            <p class="mb-2">
              Noch kein Konto?
              <router-link to="/auth/register" class="text-decoration-none">
                Registrieren
              </router-link>
            </p>
            <p>
              <router-link to="/auth/forgot-password" class="text-decoration-none">
                Passwort vergessen?
              </router-link>
            </p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const form = ref();
const username = ref("");
const password = ref("");
const showPassword = ref(false);

const rules = {
  required: (value: string) => !!value || "Dieses Feld ist erforderlich",
};

const isFormValid = computed(() => {
  return username.value && password.value;
});

const handleLogin = async () => {
  if (!form.value.validate()) {
    return;
  }

  try {
    await authStore.signIn(username.value, password.value);
    // Redirect to main app after successful login
    router.push("/");
  } catch (error) {
    console.error("Login failed:", error);
    // Error is already handled in the store and displayed in the template
  }
};
</script>

<style scoped>
.fill-height {
  min-height: 100vh;
}
</style> 