# TT-Top GitHub Migration Guide

This guide covers the migration of the TT-SMI project to a standalone TT-Top repository on GitHub.

## 🎯 Recommended Strategy: Clean Fork Approach

Create a new `tt-top` repository while preserving the original `tt-smi` project. This provides the cleanest user experience while maintaining both projects.

## 📋 Pre-Migration Checklist

### 1. **Complete Local Cleanup**
```bash
# Run the cleanup script
./cleanup_tttop.sh

# Validate the project structure
python3 validate_tttop.py

# Run tests to ensure everything works
cd tests_tt_top && python3 run_tests.py full
```

### 2. **Update All Documentation**
```bash
# Update URLs in documentation
find . -name "*.md" -exec sed -i.bak 's/github.com\/tenstorrent\/tt-smi/github.com\/tenstorrent\/tt-top/g' {} \;

# Update project references
find . -name "*.md" -exec sed -i.bak 's/TT-SMI project/TT-Top project/g' {} \;

# Clean up backup files
find . -name "*.bak" -delete
```

### 3. **Verify Package Configuration**
```bash
# Ensure setup.py and pyproject.toml have correct URLs
grep -n "github.com" setup.py pyproject.toml
grep -n "tt-top" setup.py pyproject.toml
```

## 🚀 GitHub Migration Steps

### Step 1: Create New TT-Top Repository

**Option A: Using GitHub CLI**
```bash
gh repo create tenstorrent/tt-top \
  --public \
  --description "Real-time hardware monitoring for Tenstorrent silicon with advanced telemetry visualization" \
  --homepage "https://docs.tenstorrent.com/tt-top" \
  --add-readme=false
```

**Option B: Using GitHub Web Interface**
1. Go to https://github.com/new
2. Repository name: `tt-top`
3. Description: `Real-time hardware monitoring for Tenstorrent silicon with advanced telemetry visualization`
4. Public repository
5. Don't initialize with README (we have our own)

### Step 2: Configure Repository Settings

**Add Topics and Labels:**
```bash
# Add repository topics
gh repo edit tenstorrent/tt-top --add-topic tenstorrent
gh repo edit tenstorrent/tt-top --add-topic hardware-monitoring
gh repo edit tenstorrent/tt-top --add-topic real-time
gh repo edit tenstorrent/tt-top --add-topic telemetry
gh repo edit tenstorrent/tt-top --add-topic terminal-ui
gh repo edit tenstorrent/tt-top --add-topic python

# Set repository settings
gh repo edit tenstorrent/tt-top --enable-issues=true
gh repo edit tenstorrent/tt-top --enable-projects=true
gh repo edit tenstorrent/tt-top --enable-wiki=false
```

**Create Initial Labels:**
```bash
gh label create "enhancement" --description "New feature or improvement" --color "84b6eb"
gh label create "bug" --description "Something isn't working" --color "d73a4a"
gh label create "documentation" --description "Improvements or additions to documentation" --color "0075ca"
gh label create "hardware" --description "Hardware-specific issues" --color "8b5cf6"
gh label create "performance" --description "Performance related" --color "fbbf24"
gh label create "testing" --description "Testing related" --color "10b981"
```

### Step 3: Push TT-Top Code

```bash
# Add the new repository as a remote
git remote add tt-top-origin https://github.com/tenstorrent/tt-top.git

# Create a clean branch for TT-Top
git checkout -b tt-top-main

# Push to new repository
git push tt-top-origin tt-top-main:main

# Set up tracking
git branch --set-upstream-to=tt-top-origin/main tt-top-main
```

### Step 4: Create Initial Release

```bash
# Create and push a version tag
git tag -a v1.0.0 -m "TT-Top v1.0.0 - Initial standalone release

Features:
- Real-time hardware telemetry monitoring
- Memory hierarchy visualization
- ML workload detection and analysis
- Hardware event logging
- Cross-architecture support (Grayskull, Wormhole, Blackhole)
- Professional terminal interface with cyberpunk aesthetics"

git push tt-top-origin v1.0.0

# Create GitHub release
gh release create v1.0.0 \
  --repo tenstorrent/tt-top \
  --title "TT-Top v1.0.0 - Initial Release" \
  --notes "First standalone release of TT-Top hardware monitoring tool. See README.md for installation and usage instructions."
```

### Step 5: Set Up Repository Protection

```bash
# Protect main branch
gh api repos/tenstorrent/tt-top/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":[]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field restrictions=null
```

## 📁 Original TT-SMI Repository Handling

### Option 1: Archive TT-SMI (Recommended)
```bash
# Add deprecation notice to TT-SMI README
echo "
## ⚠️ Project Status: Archived

This repository has been archived. TT-SMI live monitoring functionality has been moved to a standalone project:

**🚀 [TT-Top - Real-time Hardware Monitor](https://github.com/tenstorrent/tt-top)**

- **For live monitoring**: Use [TT-Top](https://github.com/tenstorrent/tt-top)
- **For static telemetry**: This repository remains available for reference

See the [TT-Top installation guide](https://github.com/tenstorrent/tt-top/blob/main/README.md) for migration instructions.
" >> README.md

# Archive the repository
gh repo archive tenstorrent/tt-smi
```

### Option 2: Keep Both Active
```bash
# Update TT-SMI README to reference TT-Top
echo "
## Related Projects

**🚀 [TT-Top](https://github.com/tenstorrent/tt-top)** - Standalone real-time hardware monitor forked from TT-SMI

TT-Top provides an enhanced live monitoring experience with:
- Advanced memory hierarchy visualization
- ML workload detection
- Hardware event logging
- Performance optimizations

For real-time monitoring, we recommend using TT-Top.
" >> README.md
```

## 🔄 Migration Validation

### Test New Repository
```bash
# Clone and test the new repository
git clone https://github.com/tenstorrent/tt-top.git /tmp/tt-top-test
cd /tmp/tt-top-test

# Validate project structure
python3 validate_tttop.py

# Run tests
cd tests_tt_top && python3 run_tests.py quick

# Test installation
pip install -e . --user
tt-top --help
```

### Update Documentation Links
```bash
# Update any external documentation
# - Internal wikis
# - User guides
# - API documentation
# - Issue trackers
```

## 📢 Communication Plan

### 1. **Announcement Issues**
Create issues in both repositories announcing the transition:

**TT-SMI Repository:**
```markdown
# TT-SMI Live Monitor Moved to Standalone TT-Top Project

The TT-SMI live monitoring functionality has been extracted into a dedicated project for better maintainability and enhanced features.

## 🚀 New Project: TT-Top
- Repository: https://github.com/tenstorrent/tt-top
- Enhanced features and performance
- Dedicated to real-time hardware monitoring

## Migration Path
1. For live monitoring: Switch to TT-Top
2. For static telemetry: Continue using TT-SMI
3. See migration guide: [link]

This change improves both projects by allowing focused development.
```

**TT-Top Repository:**
```markdown
# Welcome to TT-Top! 🎉

TT-Top is a standalone real-time hardware monitoring tool for Tenstorrent silicon, forked from TT-SMI to provide enhanced monitoring capabilities.

## What's New in TT-Top
- Advanced memory hierarchy visualization
- ML workload detection and analysis
- Hardware event logging
- Performance optimizations
- Clean, focused interface

## Getting Started
See our [installation guide](README.md) and [examples](examples/) to get started.

Questions? Open an issue or check our [documentation](INSTALL_TTTOP.md).
```

### 2. **Update External References**
- Documentation websites
- Blog posts and tutorials
- Internal tools and scripts
- CI/CD pipelines

## 🔍 Post-Migration Checklist

- [ ] New repository created and configured
- [ ] Code pushed and tested
- [ ] Initial release created (v1.0.0)
- [ ] Repository settings configured (topics, labels, protection)
- [ ] Original repository handled (archived or updated)
- [ ] Documentation updated with new URLs
- [ ] Migration announcement posted
- [ ] External references updated
- [ ] Team notified of new repository

## 📞 Support

For migration questions or issues:
1. Check the [TT-Top documentation](README.md)
2. Open an issue in the [TT-Top repository](https://github.com/tenstorrent/tt-top/issues)
3. Contact the development team

---

**Migration Timeline Estimate:** 2-4 hours for complete migration
**Recommended Migration Window:** During low-activity period to minimize disruption