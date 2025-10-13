# Personal Repository Rename: tsingletaryTT/tt-smi → tsingletaryTT/tt-top

Guide for renaming your personal fork to establish TT-Top as a standalone project.

## 🎯 **Strategy: Rename Personal Fork**

This approach renames your existing `tsingletaryTT/tt-smi` repository to `tsingletaryTT/tt-top`, preserving all development history while establishing the new identity.

## 📋 **Pre-Rename Checklist**

### 1. **Complete Local Cleanup**
```bash
# Ensure you're on the tt-top branch
git checkout tt-top

# Run cleanup to finalize project structure
./cleanup_tttop.sh

# Validate the project
python3 validate_tttop.py

# Run tests
cd tests_tt_top && python3 run_tests.py full
```

### 2. **Update All References**
```bash
# Update documentation to reflect new repository name
find . -name "*.md" -exec sed -i.bak 's/tsingletaryTT\/tt-smi/tsingletaryTT\/tt-top/g' {} \;
find . -name "*.md" -exec sed -i.bak 's/github.com\/tenstorrent\/tt-smi/github.com\/tenstorrent\/tt-smi/g' {} \;

# Update project files
sed -i.bak 's/"Bug Reports" = "https:\/\/github.com\/tenstorrent\/tt-top\/issues"/"Bug Reports" = "https:\/\/github.com\/tsingletaryTT\/tt-top\/issues"/g' pyproject.toml
sed -i.bak 's/"Source" = "https:\/\/github.com\/tenstorrent\/tt-top"/"Source" = "https:\/\/github.com\/tsingletaryTT\/tt-top"/g' pyproject.toml

# Clean backup files
find . -name "*.bak" -delete
```

## 🚀 **GitHub Rename Process**

### **Option A: Using GitHub Web Interface**

1. **Go to Repository Settings**
   - Navigate to https://github.com/tsingletaryTT/tt-smi
   - Click on "Settings" tab
   - Scroll down to "Repository name" section

2. **Rename Repository**
   - Change name from `tt-smi` to `tt-top`
   - Update description: `Real-time hardware monitoring for Tenstorrent silicon with advanced telemetry visualization`
   - Click "Rename"

3. **Update Topics**
   - Go to main repository page
   - Click gear icon next to "About"
   - Add topics: `tenstorrent`, `hardware-monitoring`, `real-time`, `telemetry`, `terminal-ui`, `python`

### **Option B: Using GitHub CLI**

```bash
# Rename repository
gh repo rename tsingletaryTT/tt-smi tsingletaryTT/tt-top

# Update description and settings
gh repo edit tsingletaryTT/tt-top \
  --description "Real-time hardware monitoring for Tenstorrent silicon with advanced telemetry visualization" \
  --homepage "https://github.com/tsingletaryTT/tt-top" \
  --add-topic tenstorrent \
  --add-topic hardware-monitoring \
  --add-topic real-time \
  --add-topic telemetry \
  --add-topic terminal-ui \
  --add-topic python
```

## 🔧 **Update Local Git Configuration**

```bash
# Update remote URLs to reflect new repository name
git remote set-url fork https://github.com/tsingletaryTT/tt-top.git

# Verify remote configuration
git remote -v
# Should show:
# fork    https://github.com/tsingletaryTT/tt-top.git (fetch)
# fork    https://github.com/tsingletaryTT/tt-top.git (push)
# origin  git@github.com:tenstorrent/tt-smi.git (fetch)
# origin  git@github.com:tenstorrent/tt-smi.git (push)

# Update upstream sync scripts to use new fork URL
sed -i.bak 's/tsingletaryTT\/tt-smi/tsingletaryTT\/tt-top/g' sync_upstream.sh
sed -i.bak 's/tsingletaryTT\/tt-smi/tsingletaryTT\/tt-top/g' GIT_WORKFLOW.md
rm *.bak
```

## 📝 **Update Project Documentation**

### **Update README.md**
```bash
# Update installation instructions
sed -i.bak 's/git clone.*tt-smi/git clone https:\/\/github.com\/tsingletaryTT\/tt-top.git/g' README.md

# Update issue links
sed -i.bak 's/tenstorrent\/tt-top\/issues/tsingletaryTT\/tt-top\/issues/g' README.md

# Clean backup
rm README.md.bak
```

### **Update Installation Guide**
```bash
# Update clone instructions in INSTALL_TTTOP.md
sed -i.bak 's/git clone.*tt-smi/git clone https:\/\/github.com\/tsingletaryTT\/tt-top.git/g' INSTALL_TTTOP.md
rm INSTALL_TTTOP.bak
```

## 🏷️ **Create Initial Release**

```bash
# Commit all documentation updates
git add -A
git commit -m "Update repository references for tt-top rename

- Updated all documentation links
- Updated project configuration URLs
- Finalized TT-Top standalone project structure"

# Create version tag for initial release
git tag -a v1.0.0 -m "TT-Top v1.0.0 - Initial standalone release

Features:
✨ Real-time hardware telemetry monitoring (100ms refresh)
🧠 Intelligent ML workload detection and analysis
💾 Memory hierarchy visualization (DDR → L2 → L1)
📊 Hardware event logging with real-time streaming
🎨 Professional terminal interface with hardware-responsive colors
🏗️  Cross-architecture support (Grayskull, Wormhole, Blackhole)
🔧 Comprehensive test suite and validation tools

Forked from TT-SMI and redesigned as focused hardware monitoring tool."

# Push everything to renamed repository
git push fork tt-top
git push fork --tags

# Create GitHub release
gh release create v1.0.0 \
  --repo tsingletaryTT/tt-top \
  --title "TT-Top v1.0.0 - Initial Standalone Release" \
  --notes-file - << 'EOF'
# 🎉 TT-Top v1.0.0 - Initial Release

First standalone release of **TT-Top**, a real-time hardware monitoring tool for Tenstorrent silicon.

## ✨ **Key Features**

- **Real-time Monitoring**: 100ms refresh rate with hardware-responsive visualizations
- **Memory Hierarchy**: DDR channel status, L2 cache, and L1 SRAM visualization
- **ML Workload Detection**: Automatic detection of PyTorch, TensorFlow, JAX, and HuggingFace workloads
- **Hardware Event Log**: Live streaming of power, thermal, and performance events
- **Cross-Architecture**: Support for Grayskull, Wormhole, and Blackhole devices
- **Professional UI**: Clean terminal interface with cyberpunk color palette

## 📦 **Installation**

```bash
# Clone repository
git clone https://github.com/tsingletaryTT/tt-top.git
cd tt-top

# Install dependencies
pip install textual rich psutil

# Install TT-Top
pip install -e .

# Launch
tt-top
```

## 📚 **Documentation**

- [Installation Guide](INSTALL_TTTOP.md)
- [Usage Examples](examples/basic_usage.py)
- [Git Workflow](GIT_WORKFLOW.md) (for upstream sync)

## 🔄 **Forked from TT-SMI**

TT-Top is forked from [TT-SMI](https://github.com/tenstorrent/tt-smi) and redesigned as a focused, standalone hardware monitoring tool. It maintains sync with upstream TT-SMI for backend improvements while providing enhanced visualization and analysis capabilities.

---

**Questions?** Open an issue or check the documentation!
EOF
```

## 🔄 **Update Sync Configuration**

Your upstream sync setup remains mostly the same, but update the documentation:

```bash
# Update GIT_WORKFLOW.md with new fork URL
sed -i.bak 's/tsingletaryTT\/tt-smi/tsingletaryTT\/tt-top/g' GIT_WORKFLOW.md
rm GIT_WORKFLOW.md.bak

# Test sync functionality still works
./check_upstream.sh
```

## 📢 **Optional: Update TT-SMI Fork Description**

Since GitHub will automatically redirect `tsingletaryTT/tt-smi` to `tsingletaryTT/tt-top`, you might want to:

1. **Update your GitHub profile** to mention TT-Top
2. **Pin the TT-Top repository** for visibility
3. **Add repository description** that clearly identifies it as TT-Top

## ✅ **Post-Rename Validation**

```bash
# Test repository access
git remote get-url fork
# Should return: https://github.com/tsingletaryTT/tt-top.git

# Test clone from new URL
git clone https://github.com/tsingletaryTT/tt-top.git /tmp/tt-top-test
cd /tmp/tt-top-test
python3 validate_tttop.py

# Test installation
pip install -e . --user
tt-top --help
```

## 🎯 **Benefits of This Approach**

### ✅ **Advantages**
- **Preserves History**: All development history and commits preserved
- **Automatic Redirects**: Old URLs automatically redirect to new repository
- **Maintains Stars/Forks**: Keeps existing repository metrics
- **Simple Process**: Single rename operation
- **Clean Identity**: Repository now clearly represents TT-Top project

### ✅ **SEO Benefits**
- GitHub automatically handles URL redirects
- Search engines will index new repository name
- Existing bookmarks continue to work
- Commit history shows evolution to TT-Top

## 🚀 **Next Steps After Rename**

1. **Test Everything**: Ensure all links and references work
2. **Update Bookmarks**: Update your personal bookmarks
3. **Notify Collaborators**: Let any collaborators know about the rename
4. **Continue Development**: Keep building TT-Top features
5. **Future Migration**: When ready, can transfer to `tenstorrent/tt-top`

---

## **Execution Summary**

**Time Required**: ~30 minutes
**Complexity**: Low
**Risk**: Minimal (GitHub handles redirects automatically)
**Result**: Clean `tsingletaryTT/tt-top` repository with preserved history

This gives you a proper standalone TT-Top identity while maintaining the option to transfer to the main Tenstorrent organization later!