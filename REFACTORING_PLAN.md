# Systematic Refactoring Plan

## 🎯 Objective
Clean up the codebase systematically, removing ~60-70% of unused/legacy code while preserving all functionality.

## 📋 Phase-by-Phase Cleanup Plan

### Phase 1: Safe Archive Removals ✅
**Risk Level: LOW** - These are clearly isolated legacy directories

1. **Remove `archive/` directory** - Complete legacy system
2. **Remove `frontend/archive/` directory** - Old React implementation  
3. **Remove `backend/` directory** - Empty/duplicate backend

**Dependencies to check:** None (isolated directories)

### Phase 2: Duplicate File Removals ✅
**Risk Level: LOW-MEDIUM** - Check for any references first

1. **Remove `app/src/main.py`** - Conflicts with `app/main.py`
2. **Remove `app/config.yaml`** - Duplicate of `app/config/config.yaml`
3. **Remove old Docker configs** - `docker-compose.yml`, `docker-compose.dev.yml`
4. **Remove old README files** - `README` (keep `README.md`)

**Dependencies to check:** 
- Search for imports of `app/src/main.py`
- Check if any scripts reference old config files
- Verify Docker configs aren't used in deployment

### Phase 3: Script Analysis & Cleanup ⚠️
**Risk Level: MEDIUM** - Need to verify each script isn't imported/called

Scripts to investigate in `app/scripts/`:
- `clean_transcript.py`
- `create_spinoff_transcript.py` 
- `fetch_youtube_transcript.py`
- `generate_audio.py`
- `generate_test_transcript.py`
- `list_transcripts.py`
- `process_large_transcript.py`
- `process_transcript.py`
- `search_transcripts.py`
- `test_kokoro.py`
- `test_voice_options.py`

**Keep:** `youtube_to_audio.py` (main pipeline)

**Dependencies to check:**
- Search entire codebase for imports of each script
- Check if any are called from `app/main.py` or other active code
- Verify they're not referenced in documentation or startup scripts

### Phase 4: Frontend Cleanup ✅
**Risk Level: LOW** - Unused frontend files

1. **Remove `frontend/src/App.css`** - Not imported anywhere
2. **Remove `frontend/memory-bank/`** - Old project notes
3. **Remove `frontend/docs/`** - Old documentation
4. **Check `frontend/src/context/`** - May be unused with new structure
5. **Check `frontend/src/assets/`** - If empty or unused

### Phase 5: Configuration Consolidation ⚠️
**Risk Level: MEDIUM** - Critical for app functionality

1. **Verify single config source** - `app/config/config.yaml`
2. **Remove `app/nixpacks.toml`** if not used for deployment
3. **Check `app/package-lock.json`** - Why is this in backend?

### Phase 6: Final Structure Verification ✅
**Risk Level: LOW** - Final cleanup

1. **Update startup scripts** if needed
2. **Update documentation references**
3. **Test application functionality**
4. **Update .gitignore** if needed

## 🔍 Dependency Checking Strategy

Before removing any file, I will:

1. **Search for imports:**
   ```bash
   grep -r "from filename" .
   grep -r "import filename" .
   ```

2. **Search for direct references:**
   ```bash
   grep -r "filename" . --exclude-dir=node_modules --exclude-dir=.git
   ```

3. **Check startup scripts and configs:**
   - `startup.sh`
   - `Makefile`
   - `package.json` files
   - Docker configs

4. **Verify functionality:**
   - Test application startup
   - Test main user flows
   - Check for broken imports

## 📊 Progress Tracking

- [ ] Phase 1: Archive Removals
- [ ] Phase 2: Duplicate Files  
- [ ] Phase 3: Script Analysis
- [ ] Phase 4: Frontend Cleanup
- [ ] Phase 5: Configuration
- [ ] Phase 6: Final Verification

## 🚨 Safety Measures

1. **Work on `refactored` branch** ✅
2. **Commit after each phase** for easy rollback
3. **Test application after each major change**
4. **Keep detailed log of what was removed**
5. **Verify no broken imports before proceeding**

## 🎯 Expected Outcome

**Before:** ~500+ files with lots of duplication and legacy code
**After:** Clean, maintainable structure with ~60-70% fewer files

**Final Structure:**
```
prellus/
├── docs/                    # Comprehensive documentation
├── app/                     # Clean backend
│   ├── main.py             # Single entry point
│   ├── scripts/
│   │   └── youtube_to_audio.py  # Main pipeline
│   ├── src/transcript_pipeline/ # Core modules
│   ├── config/config.yaml  # Single config
│   └── data/               # File storage
├── frontend/               # Clean React app
│   └── src/                # Modern structure
├── startup.sh              # Simple startup
├── Makefile                # Process management
└── README.md               # Single README
```

Let's begin with Phase 1!
