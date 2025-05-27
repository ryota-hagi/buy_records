# Branch Strategy Guide

## Overview

This document outlines the branching strategy for the Buy Records project. We follow a modified Git Flow approach optimized for continuous deployment.

## Main Branches

### `main` (Production)
- **Purpose**: Production-ready code
- **Protection**: Protected branch with required reviews
- **Deployment**: Auto-deploys to production via Vercel
- **Merge Requirements**:
  - Pull request with at least 1 approval
  - All CI/CD checks must pass
  - No merge conflicts

### `develop` (Staging)
- **Purpose**: Integration branch for features
- **Protection**: Protected branch
- **Deployment**: Auto-deploys to staging environment
- **Merge Requirements**:
  - Pull request preferred
  - All tests must pass

## Supporting Branches

### Feature Branches (`feature/*`)
- **Naming**: `feature/description-of-feature`
- **Created from**: `develop`
- **Merged to**: `develop`
- **Lifecycle**: Deleted after merge
- **Examples**:
  - `feature/add-mercari-integration`
  - `feature/improve-search-performance`
  - `feature/update-ui-components`

### Bugfix Branches (`bugfix/*`)
- **Naming**: `bugfix/description-of-bug`
- **Created from**: `develop`
- **Merged to**: `develop`
- **Lifecycle**: Deleted after merge
- **Examples**:
  - `bugfix/fix-ebay-api-timeout`
  - `bugfix/correct-currency-conversion`

### Hotfix Branches (`hotfix/*`)
- **Naming**: `hotfix/description-of-fix`
- **Created from**: `main`
- **Merged to**: `main` AND `develop`
- **Lifecycle**: Deleted after merge
- **Purpose**: Critical production fixes
- **Examples**:
  - `hotfix/fix-critical-search-error`
  - `hotfix/security-patch`

### Release Branches (`release/*`)
- **Naming**: `release/version-number`
- **Created from**: `develop`
- **Merged to**: `main` AND `develop`
- **Lifecycle**: Deleted after merge
- **Purpose**: Prepare for production release
- **Examples**:
  - `release/1.2.0`
  - `release/2.0.0-beta`

## Workflow Examples

### Feature Development
```bash
# Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/add-yahoo-shopping-api

# Work on feature
git add .
git commit -m "feat: implement Yahoo Shopping API integration"

# Push and create PR
git push origin feature/add-yahoo-shopping-api
# Create PR from feature/add-yahoo-shopping-api to develop
```

### Hotfix Process
```bash
# Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/fix-api-key-exposure

# Fix the issue
git add .
git commit -m "fix: remove exposed API key from client code"

# Push and create PRs
git push origin hotfix/fix-api-key-exposure
# Create PR from hotfix/fix-api-key-exposure to main
# After merge to main, create PR to develop
```

### Release Process
```bash
# Create release branch
git checkout develop
git pull origin develop
git checkout -b release/1.5.0

# Bump version, update changelog
npm version minor
git add .
git commit -m "chore: bump version to 1.5.0"

# Push and create PRs
git push origin release/1.5.0
# Create PR from release/1.5.0 to main
# After merge to main, create PR back to develop
```

## Commit Message Convention

Follow the Conventional Commits specification:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc)
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `test:` Test additions or modifications
- `chore:` Build process or auxiliary tool changes
- `ci:` CI/CD changes

Examples:
```
feat: add JAN code search functionality
fix: resolve timeout issue in Mercari scraper
docs: update API documentation for eBay integration
refactor: simplify unified search engine logic
```

## Best Practices

1. **Keep branches up to date**: Regularly merge or rebase from the parent branch
2. **Small, focused commits**: Make commits atomic and focused on a single change
3. **Descriptive branch names**: Use clear, descriptive names that explain the purpose
4. **Clean up branches**: Delete branches after merging
5. **Test before merging**: Ensure all tests pass before creating a PR
6. **Review thoroughly**: Take code reviews seriously, they improve code quality
7. **Document changes**: Update relevant documentation with your changes

## Merge Strategies

- **Feature to Develop**: Squash and merge (clean history)
- **Develop to Main**: Create a merge commit (preserve history)
- **Hotfix to Main**: Create a merge commit
- **Release to Main**: Create a merge commit

## Emergency Procedures

In case of critical production issues:

1. Create hotfix branch from `main`
2. Implement minimal fix
3. Test thoroughly
4. Create PR to `main` with "URGENT" label
5. Get expedited review
6. Merge to `main`
7. Immediately create PR to merge back to `develop`

## Questions?

If you have questions about the branching strategy, please consult with the team lead or open a discussion in the project repository.