import fs from 'fs'
import path from 'path'

/**
 * Extract changelog entries from the backend CHANGELOG.md file
 * and convert them to a structured format for the frontend
 */
function extractChangelog() {
  const changelogPath = path.resolve('../backend/CHANGELOG.md')
  
  if (!fs.existsSync(changelogPath)) {
    console.warn('Backend CHANGELOG.md not found, skipping changelog extraction')
    return { releases: [] }
  }

  const content = fs.readFileSync(changelogPath, 'utf-8')
  const lines = content.split('\n')
  
  const releases = []
  let currentRelease = null
  let currentSection = null
  let inCodeBlock = false

  for (const line of lines) {
    // Toggle code block state
    if (line.startsWith('```')) {
      inCodeBlock = !inCodeBlock
      continue
    }

    // Skip lines inside code blocks
    if (inCodeBlock) continue

    // Match release headers: ## [version] - date
    const releaseMatch = line.match(/^## \[([^\]]+)\] - (.+)$/)
    if (releaseMatch) {
      // Save previous release if exists
      if (currentRelease) {
        releases.push(currentRelease)
      }
      
      currentRelease = {
        version: releaseMatch[1],
        date: releaseMatch[2],
        sections: {}
      }
      currentSection = null
      continue
    }

    // Match section headers: ### Features, ### Bug Fixes, etc.
    const sectionMatch = line.match(/^### (.+)$/)
    if (sectionMatch && currentRelease) {
      currentSection = sectionMatch[1]
      currentRelease.sections[currentSection] = []
      continue
    }

    // Match list items: - item or * item
    const itemMatch = line.match(/^[-*] (.+)$/)
    if (itemMatch && currentRelease && currentSection) {
      currentRelease.sections[currentSection].push(itemMatch[1])
      continue
    }
  }

  // Add the last release
  if (currentRelease) {
    releases.push(currentRelease)
  }

  return { releases }
}

/**
 * Get the latest release version from the changelog
 */
function getLatestVersion(changelog) {
  return changelog.releases.length > 0 ? changelog.releases[0].version : '1.0.0'
}

export { extractChangelog, getLatestVersion }
