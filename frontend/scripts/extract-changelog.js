import fs from 'fs'
import path from 'path'

/**
 * Extract changelog entries from the root CHANGELOG.md file
 * and convert them to a structured format for the frontend.
 * 
 * Supports both formats:
 * - Old format: ## [1.0.0] - 2025-09-14
 * - Release-please format: ## [1.1.0](https://github.com/user/repo/compare/v1.0.0...v1.1.0) (2025-09-14)
 */
function extractChangelog() {
  const changelogPath = path.resolve('../CHANGELOG.md')
  
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

    // Match release headers: 
    // Format 1: ## [version] - date (old format)
    // Format 2: ## [version](link) (date) (release-please format)
    const releaseMatch = line.match(/^## \[([^\]]+)\](?:\([^)]+\))?\s*(?:-\s*(.+)|\((.+)\))$/)
    if (releaseMatch) {
      // Save previous release if exists
      if (currentRelease) {
        releases.push(currentRelease)
      }
      
      // Extract version and date - date can be in position 2 or 3 depending on format
      const version = releaseMatch[1]
      const date = releaseMatch[2] || releaseMatch[3] || 'Unknown date'
      
      currentRelease = {
        version: version,
        date: date,
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
      // Clean up the item text by removing commit references
      let cleanItem = itemMatch[1]
      
      // Remove the entire commit reference pattern: (#123) ([a1b2c3d](https://github.com/...))
      // This handles cases like: "feature (#23) ([abc123](https://github.com/...))"
      cleanItem = cleanItem.replace(/\s*\(#\d+\)\s*\(\[[a-f0-9]{7,40}\]\([^)]+\)\)$/i, '')
      
      // Remove just commit links: ([a1b2c3d](https://github.com/...))
      cleanItem = cleanItem.replace(/\s*\(\[[a-f0-9]{7,40}\]\([^)]+\)\)$/i, '')
      
      // Remove standalone commit hashes in parentheses: ([a1b2c3d])
      cleanItem = cleanItem.replace(/\s*\([a-f0-9]{7,40}\)$/i, '')
      
      // Remove issue/PR references anywhere in the text: (#123) or ([#123](link))
      cleanItem = cleanItem.replace(/\s*\(#\d+\)/gi, '')
      cleanItem = cleanItem.replace(/\s*\(\[#\d+\]\([^)]+\)\)/gi, '')
      
      // Remove any remaining GitHub links: [text](https://github.com/...)
      cleanItem = cleanItem.replace(/\s*\[[^\]]+\]\(https:\/\/github\.com[^)]+\)/gi, '')
      
      // Remove trailing whitespace
      cleanItem = cleanItem.trim()
      
      // Only add non-empty items
      if (cleanItem) {
        currentRelease.sections[currentSection].push(cleanItem)
      }
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
