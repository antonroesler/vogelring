<template>
  <footer class="legal-footer">
    <v-container>
      <v-row>
        <v-col cols="12" md="8">
          <div class="footer-content">
            <div class="footer-brand">
              <v-icon icon="mdi-bird" size="24" class="me-2"></v-icon>
              <span class="footer-title">Vogelring</span>
            </div>
            <p class="footer-description">
              Comprehensive bird tracking and sighting management system for ornithologists and bird watchers.
            </p>
          </div>
        </v-col>
        <v-col cols="12" md="4">
          <div class="footer-links">
            <h4 class="footer-section-title">Rechtliche Hinweise</h4>
            <div class="legal-links">
              <router-link to="/impressum" class="footer-link">Impressum</router-link>
              <router-link to="/datenschutz" class="footer-link">Datenschutzerklärung</router-link>
              <router-link to="/agb" class="footer-link">AGB</router-link>
              <router-link to="/widerruf" class="footer-link">Widerrufsrecht</router-link>
            </div>
          </div>
        </v-col>
      </v-row>
      <v-divider class="footer-divider"></v-divider>
      <v-row>
        <v-col cols="12" class="text-center">
          <div class="footer-bottom">
            <p class="copyright">
              © {{ currentYear }} Vogelring. Alle Rechte vorbehalten.
            </p>
            <p class="contact-info">
              Kontakt: <a href="mailto:anton@antonroesler.com" class="footer-link">anton@antonroesler.com</a>
            </p>
          </div>
        </v-col>
      </v-row>
    </v-container>
  </footer>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const currentYear = computed(() => new Date().getFullYear());
</script>

<style scoped>
.legal-footer {
  background: linear-gradient(135deg, #00436C 0%, #228096 100%);
  background-color: #00436C; /* Fallback solid color */
  color: white;
  padding: 48px 0 24px;
  margin-top: auto;
  position: relative;
  z-index: 1000;
  /* Ensure footer completely blocks background */
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.3);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.footer-content {
  margin-bottom: 24px;
}

.footer-brand {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.footer-title {
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.025em;
}

.footer-description {
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.6;
  margin: 0;
  font-weight: 500;
}

.footer-section-title {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 16px;
  color: white;
}

.legal-links {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.footer-link {
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  transition: all 0.3s ease;
  font-weight: 600;
  position: relative;
}

.footer-link::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 2px;
  background: rgba(255, 255, 255, 0.8);
  transition: width 0.3s ease;
}

.footer-link:hover {
  color: white;
  transform: translateX(4px);
}

.footer-link:hover::after {
  width: 100%;
}

.footer-divider {
  margin: 32px 0 24px;
  opacity: 0.3;
}

.footer-bottom {
  color: rgba(255, 255, 255, 0.7);
}

.copyright {
  margin: 0 0 8px 0;
  font-size: 0.9rem;
  font-weight: 500;
}

.contact-info {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 500;
}

.contact-info .footer-link {
  color: rgba(255, 255, 255, 0.8);
  font-weight: 600;
}

/* Responsive adjustments */
@media (max-width: 960px) {
  .legal-footer {
    padding: 32px 0 16px;
  }
  
  .footer-content {
    text-align: center;
    margin-bottom: 32px;
  }
  
  .footer-links {
    text-align: center;
  }
  
  .legal-links {
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: center;
    gap: 16px;
  }
}

@media (max-width: 600px) {
  .legal-links {
    flex-direction: column;
    gap: 12px;
  }
  
  .footer-brand {
    justify-content: center;
  }
}
</style>