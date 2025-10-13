# TT-Top Git Workflow & Upstream Sync Guide

This guide covers maintaining your TT-Top fork while staying synchronized with the upstream TT-SMI repository.

## Current Repository Setup

Your repository is properly configured with:
- **`origin`**: `git@github.com:tenstorrent/tt-smi.git` (upstream TT-SMI)
- **`fork`**: `git@github.com:tsingletaryTT/tt-smi.git` (your fork)
- **Current branch**: `tt-top` (TT-Top development branch)

## Branching Strategy

### 🌳 **Branch Structure**

```
main                    # Synced with upstream TT-SMI main
├── tt-top             # Primary TT-Top development (current)
├── tt-top-stable      # Stable TT-Top releases
├── upstream-sync      # Temporary branch for merging upstream changes
└── feature/xyz        # Feature branches off tt-top
```

### 📋 **Branch Purposes**

- **`main`**: Mirror of upstream TT-SMI for tracking changes
- **`tt-top`**: Primary development branch with all TT-Top features
- **`tt-top-stable`**: Stable releases ready for production
- **`upstream-sync`**: Temporary branch for integrating upstream changes

## Sync Workflow

### 🔄 **Regular Sync Process (Weekly/Monthly)**

```bash
# 1. Fetch latest changes from upstream
git fetch origin

# 2. Update local main to match upstream
git checkout main
git reset --hard origin/main

# 3. Create temporary sync branch
git checkout -b upstream-sync-$(date +%Y%m%d)

# 4. Merge main into sync branch
git merge main

# 5. Check for conflicts and resolve
git status
# (Resolve any conflicts that arise)

# 6. Switch to tt-top branch
git checkout tt-top

# 7. Merge sync branch into tt-top
git merge upstream-sync-$(date +%Y%m%d)

# 8. Clean up sync branch
git branch -d upstream-sync-$(date +%Y%m%d)

# 9. Push updated tt-top to your fork
git push fork tt-top
```

### ⚡ **Quick Sync Commands**

```bash
# Create alias for common sync operation
git config alias.sync-upstream '!f() {
    git fetch origin &&
    git checkout main &&
    git reset --hard origin/main &&
    git checkout tt-top &&
    echo "Ready to merge upstream changes. Run: git merge main";
}; f'

# Usage
git sync-upstream
git merge main  # Review and resolve conflicts if needed
```

## Handling Conflicts

### 🔧 **Common Conflict Scenarios**

#### **1. Backend Changes in TT-SMI**
If upstream changes affect `tt_smi/tt_smi_backend.py`:

```bash
# TT-Top uses copied backend in tt_top/tt_smi_backend.py
# After merging upstream, update TT-Top copy:
cp tt_smi/tt_smi_backend.py tt_top/tt_smi_backend.py

# Review changes and test TT-Top functionality
git add tt_top/tt_smi_backend.py
git commit -m "Sync backend changes from upstream TT-SMI"
```

#### **2. Constants Changes**
If upstream changes affect `tt_smi/constants.py`:

```bash
# Selectively merge relevant constants
# Keep TT-Top specific changes in tt_top/constants.py
# Review upstream changes:
git diff main..HEAD tt_smi/constants.py

# Apply relevant changes to tt_top/constants.py manually
# Avoid overwriting TT-Top customizations
```

#### **3. Core Dependencies**
If upstream changes dependencies in `pyproject.toml`:

```bash
# Review upstream dependency changes
git diff main..HEAD pyproject.toml

# Update TT-Top dependencies if needed
# Keep TT-Top specific entries (name="tt-top", etc.)
```

### 🛠️ **Conflict Resolution Strategy**

```bash
# When conflicts occur during merge:
git status  # See conflicted files

# For each conflicted file:
# 1. Open in editor
# 2. Look for conflict markers: <<<<<<< ======= >>>>>>>
# 3. Choose appropriate resolution:

# Strategy A: Keep upstream changes (for shared code)
git checkout --theirs <file>

# Strategy B: Keep TT-Top changes (for customized code)
git checkout --ours <file>

# Strategy C: Manual merge (most common)
# Edit file to combine changes appropriately

# Mark as resolved
git add <file>

# Complete the merge
git commit
```

## File-Specific Sync Guidelines

### 📁 **Files to Sync from Upstream**

| File | Action | Reason |
|------|--------|--------|
| `tt_smi/tt_smi_backend.py` | Copy to `tt_top/` | Hardware interface updates |
| `tt_smi/log.py` | Copy to `tt_top/` | Logging improvements |
| `tt_smi/constants.py` | Selective merge | Hardware constants only |
| Hardware data files | Full sync | Device specifications |
| Bug fixes in shared code | Merge | Stability improvements |

### 🚫 **Files to Keep TT-Top Specific**

| File | Action | Reason |
|------|--------|--------|
| `setup.py` | Keep TT-Top version | Different project metadata |
| `pyproject.toml` | Keep TT-Top version | Different entry points |
| `README.md` | Keep TT-Top version | Different documentation |
| `tt_top/` directory | Keep all changes | TT-Top specific code |
| `tests_tt_top/` | Keep all changes | TT-Top specific tests |

## Release Management

### 🏷️ **Tagging Strategy**

```bash
# Tag stable TT-Top releases
git checkout tt-top-stable
git tag -a v1.0.0 -m "TT-Top v1.0.0 - Initial standalone release"
git push fork --tags

# Tag sync points for tracking
git tag -a sync-$(date +%Y%m%d) -m "Sync with upstream TT-SMI $(git rev-parse origin/main)"
```

### 📦 **Release Workflow**

```bash
# 1. Ensure tt-top is stable and tested
git checkout tt-top
./cleanup_tttop.sh  # Clean project structure
python3 validate_tttop.py  # Validate structure
cd tests_tt_top && python3 run_tests.py full  # Run full test suite

# 2. Create stable release branch
git checkout -b tt-top-stable
git push fork tt-top-stable

# 3. Tag the release
git tag -a v1.0.0 -m "TT-Top v1.0.0 - Initial standalone release"
git push fork --tags
```

## Monitoring Upstream Changes

### 👀 **Track Important Changes**

```bash
# Set up GitHub CLI for monitoring (optional)
gh repo view tenstorrent/tt-smi --web

# Check for new releases
gh release list --repo tenstorrent/tt-smi

# Monitor specific files for changes
git log --oneline origin/main -- tt_smi/tt_smi_backend.py
git log --oneline origin/main -- tt_smi/constants.py
```

### 📧 **Notification Setup**

1. **GitHub Watch**: Enable notifications for the upstream repository
2. **Release Notifications**: Watch for new TT-SMI releases
3. **RSS/Atom Feeds**: Subscribe to commit feeds for specific files

## Automation Scripts

### 🤖 **Automated Sync Check Script**

```bash
#!/bin/bash
# check_upstream.sh - Check for upstream changes

echo "Checking upstream TT-SMI for changes..."
git fetch origin

BEHIND_COUNT=$(git rev-list --count tt-top..origin/main)
if [ $BEHIND_COUNT -gt 0 ]; then
    echo "⚠️  Upstream has $BEHIND_COUNT new commits"
    echo "Recent changes:"
    git log --oneline tt-top..origin/main | head -5
    echo ""
    echo "Consider running sync workflow"
else
    echo "✅ TT-Top is up to date with upstream"
fi
```

### 🔄 **Smart Sync Script**

```bash
#!/bin/bash
# smart_sync.sh - Intelligent upstream sync

# Backup current work
git stash push -m "Pre-sync backup $(date)"

# Fetch and analyze changes
git fetch origin
CHANGES=$(git log --oneline tt-top..origin/main -- tt_smi/ | wc -l)

if [ $CHANGES -eq 0 ]; then
    echo "✅ No relevant upstream changes"
    git stash pop
    exit 0
fi

echo "📥 Found $CHANGES upstream changes affecting shared code"
echo "Proceeding with sync..."

# Run sync workflow
git sync-upstream
echo "🔍 Review changes and run: git merge main"
```

## Best Practices

### ✅ **Recommended Practices**

1. **Regular Syncing**: Sync weekly to avoid large conflict sets
2. **Test After Sync**: Always run TT-Top test suite after upstream merges
3. **Selective Integration**: Don't merge upstream UI changes that conflict with TT-Top
4. **Documentation**: Document any custom merge decisions for future reference
5. **Backup Branches**: Create backup branches before major syncs

### ⚠️ **Avoid These Pitfalls**

1. **Force Pushing**: Never force push to shared branches
2. **Direct Main Edits**: Don't commit directly to main branch
3. **Ignoring Conflicts**: Always resolve conflicts thoughtfully
4. **Skipping Tests**: Always test after merging upstream changes
5. **Large Sync Gaps**: Don't let sync gaps grow too large (>1 month)

## Emergency Procedures

### 🚨 **If Sync Goes Wrong**

```bash
# Emergency reset to last known good state
git reflog  # Find previous good commit
git reset --hard HEAD@{n}  # where n is the good state

# Or restore from backup branch
git checkout tt-top-backup  # if you created one
git branch -D tt-top
git checkout -b tt-top
```

### 🔧 **Recovery Commands**

```bash
# Abort current merge
git merge --abort

# Reset to clean state
git clean -fd
git reset --hard

# Start over with fresh sync
git fetch origin
git checkout tt-top
```

---

## Quick Reference

### 📚 **Common Commands**
```bash
# Check sync status
git fetch origin && git log --oneline tt-top..origin/main

# Quick upstream check
git log --graph --oneline --all | head -20

# View changes in specific files
git diff origin/main -- tt_smi/tt_smi_backend.py

# Sync backend file only
cp tt_smi/tt_smi_backend.py tt_top/tt_smi_backend.py

# Test TT-Top after sync
python3 validate_tttop.py && cd tests_tt_top && python3 run_tests.py
```

This workflow ensures you maintain the benefits of the upstream TT-SMI improvements while preserving TT-Top's standalone functionality and customizations.