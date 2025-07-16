# CRITICAL: Git Merge Task - Careful Execution Required

## Task Overview
You need to execute a complex git merge operation that integrates a verbose output feature branch with substantial improvements from the main branch. This is **high-risk work** requiring careful conflict resolution.

## Essential Context
- **Working Directory**: `/Users/athundt/source/pyuvstarter-reduce-verbose-output-v1` (WORKTREE - not main repo)
- **Current State**: `feature/reduce-verbose-output-v1` branch at commit `375dbe99`
- **Backup**: Complete worktree backed up at `/tmp/worktree-backup-backup-before-merge-20250716-025816`
- **Main Repo**: `/Users/athundt/source/pyuvstarter` (DO NOT work here)

## CRITICAL INSTRUCTIONS

### 1. READ THE PLAN FIRST
**MANDATORY**: Before doing ANYTHING, read the complete merge plan:
```
/Users/athundt/source/pyuvstarter-reduce-verbose-output-v1/merge.md
```

This 765-line document contains:
- 59 checkboxes with step-by-step instructions
- Comprehensive safety procedures
- Rollback strategies for when things go wrong
- Git permissions setup/cleanup
- Testing procedures

### 2. EXPECT CONFLICTS
- Both branches modified `pyuvstarter.py` extensively (3640 lines each)
- Core functions like `_log_action()` have been changed differently
- Main branch has Python conflict resolution improvements
- Feature branch has verbose/clean output modes with tqdm progress

### 3. SAFETY FIRST
- ✅ Full backup already created
- ⚠️ Use rollback procedures if you get stuck
- ⚠️ Test thoroughly at each phase
- ⚠️ Don't force anything - conflicts are expected

### 4. GIT PERMISSIONS
The plan includes setting up temporary git permissions in `.claude/settings.json`. Follow Phase 0 exactly to enable git operations safely.

### 5. SUCCESS CRITERIA
- Verbose mode (`--verbose`) shows detailed output with main's improvements
- Clean mode (default) shows progress bars with conflict resolution
- All tests pass
- Demo scripts work with integrated functionality

## EXECUTION APPROACH
1. **Start with Phase 0** - Git permissions setup
2. **Follow every checkbox** - Don't skip steps
3. **Test frequently** - After major changes
4. **Use rollback if needed** - Better safe than sorry
5. **Clean up** - Phase 6 removes temporary permissions

## IMPORTANT NOTES
- This is methodical work, not a race
- Conflicts in `_log_action()` and CLI interface are expected
- Be prepared for 2-4 hours of careful work
- Success is not guaranteed on first attempt
- Rollback and retry is completely acceptable

## START HERE
```bash
cd /Users/athundt/source/pyuvstarter-reduce-verbose-output-v1
cat merge.md  # Read the full plan
```

**Do not begin execution until you understand the complete merge.md plan.**