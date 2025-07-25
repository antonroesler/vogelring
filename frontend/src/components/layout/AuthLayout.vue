<template>
  <v-container class="fill-height auth-container" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <div class="auth-card-wrapper">
          <v-card class="auth-card">
            <slot />
          </v-card>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
// No props or logic needed - pure layout component
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  background: #ffffff !important;
  position: relative;
  overflow: hidden;
}

.auth-container::before {
  content: '';
  position: fixed;
  top: 65%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 110%;
  height: 110%;
  background: url('/blackheadedgull.png') no-repeat center center;
  background-size: contain;
  opacity: 0.7;
  z-index: 0;
  pointer-events: none;
  background-attachment: fixed;
}

.auth-card-wrapper {
  position: relative;
  z-index: 1;
}

.auth-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px !important;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1), 0 8px 16px rgba(0, 0, 0, 0.1) !important;
  overflow: hidden;
  transition: all 0.3s ease;
}

.auth-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.15), 0 12px 24px rgba(0, 0, 0, 0.1) !important;
}

:deep(.auth-header) {
  text-align: center;
  padding: 48px 32px 24px;
  background: linear-gradient(135deg, rgba(0, 67, 108, 0.05) 0%, rgba(34, 128, 150, 0.05) 100%);
}

:deep(.auth-logo) {
  margin-bottom: 24px;
}

:deep(.logo-icon) {
  color: #00436C;
  filter: drop-shadow(0 2px 4px rgba(0, 67, 108, 0.2));
}

:deep(.auth-title) {
  font-size: 2rem;
  font-weight: 600;
  color: #00436C;
  margin-bottom: 8px;
  letter-spacing: -0.025em;
}

:deep(.auth-subtitle) {
  color: #228096;
  font-size: 1rem;
  margin: 0;
  opacity: 0.8;
}

:deep(.auth-form) {
  padding: 32px !important;
}

:deep(.auth-input) {
  margin-bottom: 16px;
}

:deep(.auth-input .v-field) {
  border-radius: 12px;
  transition: all 0.3s ease;
}

:deep(.auth-input .v-field:hover) {
  box-shadow: 0 4px 12px rgba(0, 67, 108, 0.1);
}

:deep(.auth-input .v-field--focused) {
  box-shadow: 0 4px 16px rgba(0, 67, 108, 0.2);
}

:deep(.auth-alert) {
  border-radius: 12px;
}

:deep(.auth-actions) {
  padding: 0 32px 32px !important;
}

:deep(.auth-submit-btn) {
  border-radius: 12px !important;
  height: 48px !important;
  font-weight: 600 !important;
  text-transform: none !important;
  letter-spacing: 0.025em !important;
  background: linear-gradient(135deg, #00436C 0%, #228096 100%) !important;
  box-shadow: 0 4px 16px rgba(0, 67, 108, 0.3) !important;
  transition: all 0.3s ease !important;
}

:deep(.auth-submit-btn:hover) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0, 67, 108, 0.4) !important;
}

:deep(.auth-submit-btn:active) {
  transform: translateY(0);
}

:deep(.auth-divider) {
  margin: 0 32px;
  opacity: 0.2;
}

:deep(.auth-footer) {
  padding: 24px 32px 32px !important;
  text-align: center;
}

:deep(.auth-link) {
  color: #00436C;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.2s ease;
  position: relative;
}

:deep(.auth-link::after) {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 2px;
  background: linear-gradient(135deg, #00436C 0%, #228096 100%);
  transition: width 0.3s ease;
}

:deep(.auth-link:hover::after) {
  width: 100%;
}

:deep(.auth-link:hover) {
  color: #228096;
}

/* Responsive adjustments */
@media (max-width: 600px) {
  :deep(.auth-header) {
    padding: 32px 24px 16px;
  }
  
  :deep(.auth-form) {
    padding: 24px !important;
  }
  
  :deep(.auth-actions) {
    padding: 0 24px 24px !important;
  }
  
  :deep(.auth-footer) {
    padding: 16px 24px 24px !important;
  }
  
  :deep(.auth-title) {
    font-size: 1.75rem;
  }
}
</style> 