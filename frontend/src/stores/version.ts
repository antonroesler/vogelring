import { defineStore } from 'pinia'

interface ChangelogRelease {
  version: string
  date: string
  sections: Record<string, string[]>
}

interface VersionInfo {
  version: string
  buildTime: string
  backendVersion?: string
}

interface VersionState {
  currentVersion: string
  lastSeenVersion: string | null
  changelogData: { releases: ChangelogRelease[] }
  showChangelogDialog: boolean
  changelogDisabled: boolean
  initialized: boolean
  buildTime: string | null
}

const STORAGE_KEYS = {
  LAST_SEEN_VERSION: 'vogelring_last_seen_version',
  CHANGELOG_DISABLED: 'vogelring_changelog_disabled'
}

export const useVersionStore = defineStore('version', {
  state: (): VersionState => ({
    currentVersion: __BACKEND_VERSION__ || '1.0.0',
    lastSeenVersion: null,
    changelogData: { releases: [] },
    showChangelogDialog: false,
    changelogDisabled: false,
    initialized: false,
    buildTime: null
  }),

  getters: {
    hasNewVersion: (state) => {
      if (!state.lastSeenVersion || !state.currentVersion) return false
      return state.lastSeenVersion !== state.currentVersion
    },

    shouldShowChangelog(state) {
      const hasNewVersion = state.lastSeenVersion && state.currentVersion 
        ? state.lastSeenVersion !== state.currentVersion 
        : false
      return hasNewVersion && !state.changelogDisabled && state.changelogData.releases.length > 0
    },

    latestRelease: (state) => {
      return state.changelogData.releases.length > 0 ? state.changelogData.releases[0] : null
    }
  },

  actions: {
    async initialize() {
      if (this.initialized) return

      // Load persisted data
      this.loadPersistedData()

      // Load changelog data
      await this.loadChangelogData()

      // Load version info to get build time and check for updates
      await this.loadVersionInfo()

      // Check if we should show the changelog
      if (this.shouldShowChangelog) {
        // Small delay to ensure the app is fully loaded
        setTimeout(() => {
          this.showChangelogDialog = true
        }, 1000)
      }

      this.initialized = true
    },

    loadPersistedData() {
      try {
        const lastSeenVersion = localStorage.getItem(STORAGE_KEYS.LAST_SEEN_VERSION)
        const changelogDisabled = localStorage.getItem(STORAGE_KEYS.CHANGELOG_DISABLED)

        this.lastSeenVersion = lastSeenVersion
        this.changelogDisabled = changelogDisabled === 'true'
      } catch (error) {
        console.warn('Error loading version data from localStorage:', error)
      }
    },

    async loadChangelogData() {
      try {
        const response = await fetch('/changelog.json?t=' + Date.now())
        if (response.ok) {
          this.changelogData = await response.json()
          
          // Update current version to latest from changelog if available
          if (this.changelogData.releases.length > 0) {
            this.currentVersion = this.changelogData.releases[0].version
          }
        }
      } catch (error) {
        console.warn('Error loading changelog data:', error)
      }
    },

    async loadVersionInfo() {
      try {
        const response = await fetch('/version.json?t=' + Date.now())
        if (response.ok) {
          const versionInfo: VersionInfo = await response.json()
          
          // Store the current build time
          const currentBuildTime = this.buildTime
          this.buildTime = versionInfo.buildTime
          
          // If we have a previous build time and it's different, reload the page
          if (currentBuildTime && currentBuildTime !== versionInfo.buildTime) {
            console.log('New version detected (build time changed), reloading page...')
            window.location.reload()
          }
        }
      } catch (error) {
        console.warn('Error loading version info:', error)
      }
    },

    markVersionAsSeen(dontShowAgain = false) {
      try {
        localStorage.setItem(STORAGE_KEYS.LAST_SEEN_VERSION, this.currentVersion)
        this.lastSeenVersion = this.currentVersion

        if (dontShowAgain) {
          localStorage.setItem(STORAGE_KEYS.CHANGELOG_DISABLED, 'true')
          this.changelogDisabled = true
        }

        this.showChangelogDialog = false
      } catch (error) {
        console.warn('Error saving version data to localStorage:', error)
      }
    },

    dismissChangelog() {
      this.showChangelogDialog = false
    },

    enableChangelog() {
      try {
        localStorage.removeItem(STORAGE_KEYS.CHANGELOG_DISABLED)
        this.changelogDisabled = false
      } catch (error) {
        console.warn('Error enabling changelog:', error)
      }
    },

    // Manual method to show changelog (e.g., from a menu)
    showChangelog() {
      this.showChangelogDialog = true
    },

    // Get version info for display
    getVersionInfo(): { app: string; backend: string; hasUpdate: boolean } {
      const hasNewVersion = this.lastSeenVersion && this.currentVersion 
        ? this.lastSeenVersion !== this.currentVersion 
        : false
      return {
        app: __APP_VERSION__ || '1.0.0',
        backend: this.currentVersion,
        hasUpdate: hasNewVersion
      }
    }
  }
})
