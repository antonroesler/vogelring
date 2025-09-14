# Contributing to Vogelring

Thank you for your interest in contributing to Vogelring!

## Commit Message Convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/) to automatically generate releases and changelogs.

### Commit Message Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes that affect the build system or external dependencies
- **ci**: Changes to our CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files
- **revert**: Reverts a previous commit

### Scopes

For backend changes, use the `backend` scope:
- `feat(backend): add new bird species endpoint`
- `fix(backend): resolve database connection issue`

### Examples

```
feat(backend): add bird migration tracking
fix(backend): resolve authentication token validation
docs: update API documentation
chore(backend): update dependencies
```

### Breaking Changes

To indicate a breaking change, add `!` after the type/scope:
```
feat(backend)!: change API response format
```

Or include `BREAKING CHANGE:` in the footer:
```
feat(backend): add new authentication system

BREAKING CHANGE: API now requires authentication headers
```

## Release Process

Releases are automated using [Release Please](https://github.com/googleapis/release-please):

1. When you merge a PR with conventional commits to `main`, Release Please will:
   - Create or update a release PR with the new version and changelog
   - The version bump follows semantic versioning based on commit types

2. When you merge the release PR, Release Please will:
   - Create a GitHub release
   - Tag the release
   - Update the version in `pyproject.toml`

## Development Setup

1. Clone the repository
2. Navigate to the backend directory: `cd backend`
3. Install dependencies: `uv sync`
4. Run tests: `uv run pytest`
5. Start the development server: `uv run uvicorn src.main:app --reload`
