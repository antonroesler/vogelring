<template>
  <v-container class="legal-page">
    <div class="back-button-container">
      <v-btn
        variant="text"
        color="primary"
        @click="$router.back()"
        class="back-btn"
      >
        <v-icon icon="mdi-arrow-left" class="me-2"></v-icon>
        Zurück
      </v-btn>
    </div>
    <v-row justify="center">
      <v-col cols="12" md="8">
        <v-card class="legal-card">
          <v-card-title class="legal-title">
            <v-icon icon="mdi-shield-account" class="me-2"></v-icon>
            Datenschutzerklärung
          </v-card-title>
          <v-card-text class="legal-content">
            <section class="mb-6">
              <h3>1. Datenschutz auf einen Blick</h3>
              <h4>Allgemeine Hinweise</h4>
              <p>
                Die folgenden Hinweise geben einen einfachen Überblick darüber, was mit Ihren personenbezogenen Daten 
                passiert, wenn Sie diese Website besuchen. Personenbezogene Daten sind alle Daten, mit denen Sie 
                persönlich identifiziert werden können.
              </p>
              
              <h4>Datenerfassung auf dieser Website</h4>
              <p><strong>Wer ist verantwortlich für die Datenerfassung auf dieser Website?</strong></p>
              <p>
                Die Datenverarbeitung auf dieser Website erfolgt durch den Websitebetreiber. Dessen Kontaktdaten 
                können Sie dem Impressum dieser Website entnehmen.
              </p>
              
              <p><strong>Wie erfassen wir Ihre Daten?</strong></p>
              <p>
                Ihre Daten werden zum einen dadurch erhoben, dass Sie uns diese mitteilen. Hierbei kann es sich z.B. 
                um Daten handeln, die Sie in ein Kontaktformular eingeben oder bei der Registrierung angeben.
              </p>
            </section>

            <section class="mb-6">
              <h3>2. Hosting und Content Delivery Networks (CDN)</h3>
              <h4>AWS (Amazon Web Services)</h4>
              <p>
                Wir hosten die Inhalte unserer Website bei Amazon Web Services (AWS). Anbieter ist die Amazon Web 
                Services EMEA SARL, 38 Avenue John F. Kennedy, 1855 Luxemburg (nachfolgend AWS).
              </p>
              <p>
                Wenn Sie unsere Website besuchen, werden Ihre personenbezogenen Daten auf den Servern von AWS verarbeitet. 
                Hierbei können auch personenbezogene Daten an das Mutterunternehmen von AWS in die USA übermittelt werden. 
                Die Datenübertragung in die USA wird auf die EU-Standardvertragsklauseln gestützt.
              </p>
            </section>

            <section class="mb-6">
              <h3>3. Allgemeine Hinweise und Pflichtinformationen</h3>
              <h4>Datenschutz</h4>
              <p>
                Die Betreiber dieser Seiten nehmen den Schutz Ihrer persönlichen Daten sehr ernst. Wir behandeln Ihre 
                personenbezogenen Daten vertraulich und entsprechend der gesetzlichen Datenschutzbestimmungen sowie 
                dieser Datenschutzerklärung.
              </p>
              
              <h4>Hinweis zur verantwortlichen Stelle</h4>
              <div class="contact-info">
                <p><strong>Die verantwortliche Stelle für die Datenverarbeitung auf dieser Website ist:</strong></p>
                <p>Anton Rösler</p>
                <p>Rossäckerstr. 43</p>
                <p>74189 Weinsberg</p>
                <p>E-Mail: anton@antonroesler.com</p>
              </div>
            </section>

            <section class="mb-6">
              <h3>4. Datenerfassung auf dieser Website</h3>
              <h4>Cookies</h4>
              <p>
                Unsere Internetseiten verwenden so genannte „Cookies". Cookies sind kleine Textdateien und richten auf 
                Ihrem Endgerät keinen Schaden an. Sie werden entweder vorübergehend für die Dauer einer Sitzung 
                (Session-Cookies) oder dauerhaft (permanente Cookies) auf Ihrem Endgerät gespeichert.
              </p>
              
              <h4>Server-Log-Dateien</h4>
              <p>
                Der Provider der Seiten erhebt und speichert automatisch Informationen in so genannten Server-Log-Dateien, 
                die Ihr Browser automatisch an uns übermittelt. Dies sind:
              </p>
              <ul>
                <li>Browsertyp und Browserversion</li>
                <li>verwendetes Betriebssystem</li>
                <li>Referrer URL</li>
                <li>Hostname des zugreifenden Rechners</li>
                <li>Uhrzeit der Serveranfrage</li>
                <li>IP-Adresse</li>
              </ul>
            </section>

            <section class="mb-6">
              <h3>5. Registrierung auf dieser Website</h3>
              <p>
                Sie können sich auf dieser Website registrieren, um zusätzliche Funktionen zu nutzen. Die dazu 
                eingegebenen Daten verwenden wir nur zum Zwecke der Nutzung des jeweiligen Angebotes oder Dienstes, 
                für den Sie sich registriert haben.
              </p>
              <p>
                Die bei der Registrierung abgefragten Pflichtangaben müssen vollständig angegeben werden. Anderenfalls 
                werden wir die Registrierung ablehnen. Für wichtige Änderungen etwa beim Angebotsumfang oder bei 
                technisch notwendigen Änderungen nutzen wir die bei der Registrierung angegebene E-Mail-Adresse.
              </p>
            </section>

            <section class="mb-6">
              <h3>6. Ihre Rechte</h3>
              <p>Sie haben folgende Rechte:</p>
              <ul>
                <li>Recht auf Auskunft über Ihre bei uns gespeicherten personenbezogenen Daten</li>
                <li>Recht auf Berichtigung unrichtiger oder unvollständiger Daten</li>
                <li>Recht auf Löschung Ihrer bei uns gespeicherten Daten</li>
                <li>Recht auf Einschränkung der Datenverarbeitung</li>
                <li>Recht auf Datenübertragbarkeit</li>
                <li>Widerspruchsrecht gegen die Verarbeitung Ihrer Daten</li>
                <li>Recht auf Beschwerde bei einer Aufsichtsbehörde</li>
              </ul>
            </section>

            <section>
              <h3>7. SSL- bzw. TLS-Verschlüsselung</h3>
              <p>
                Diese Seite nutzt aus Sicherheitsgründen und zum Schutz der Übertragung vertraulicher Inhalte eine 
                SSL- bzw. TLS-Verschlüsselung. Eine verschlüsselte Verbindung erkennen Sie daran, dass die Adresszeile 
                des Browsers von „http://" auf „https://" wechselt und an dem Schloss-Symbol in Ihrer Browserzeile.
              </p>
            </section>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
// No script needed for this static page
</script>

<style scoped>
.legal-page {
  padding: 32px 16px;
  min-height: calc(100vh - 200px);
}

.legal-card {
  border-radius: 16px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
  border: 1px solid rgba(0, 67, 108, 0.1);
}

.legal-title {
  background: linear-gradient(135deg, rgba(0, 67, 108, 0.05) 0%, rgba(34, 128, 150, 0.05) 100%);
  color: #00436C;
  font-size: 1.5rem;
  font-weight: 600;
  padding: 24px 32px;
}

.legal-content {
  padding: 32px !important;
  line-height: 1.7;
}

.legal-content h3 {
  color: #00436C;
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 16px;
  border-bottom: 2px solid #DED5CA;
  padding-bottom: 8px;
}

.legal-content h4 {
  color: #228096;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 20px 0 12px 0;
}

.legal-content p {
  margin-bottom: 16px;
  color: rgba(0, 0, 0, 0.87);
}

.legal-content ul {
  margin-bottom: 16px;
  padding-left: 24px;
}

.legal-content li {
  margin-bottom: 8px;
  color: rgba(0, 0, 0, 0.87);
}

.contact-info {
  background: rgba(0, 67, 108, 0.02);
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid #228096;
}

.contact-info p {
  margin-bottom: 8px;
}

.contact-info p:last-child {
  margin-bottom: 0;
}

.contact-info a {
  color: #228096;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.contact-info a:hover {
  color: #00436C;
  text-decoration: underline;
}

.back-button-container {
  margin-bottom: 16px;
}

.back-btn {
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
}

.back-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 67, 108, 0.2);
}

/* Responsive adjustments */
@media (max-width: 600px) {
  .legal-title {
    padding: 16px 20px;
    font-size: 1.3rem;
  }
  
  .legal-content {
    padding: 20px !important;
  }
  
  .legal-content h3 {
    font-size: 1.1rem;
  }
  
  .legal-content h4 {
    font-size: 1rem;
  }
}
</style>