---
name: project-status-reporter
description: Gather and report the current status of The Sift (pysift) Minecraft mod project, including build health, texture pipeline verification, git status, and roadmap progress.
---

# Project Status Reporter (`project-status-reporter`)

Use this skill when the user asks for a project status report on **The Sift (`pysift`)**.

## Checklist

1. **Code Health**
   - Check Java compilation (`.\gradlew.bat compileJava compileClientJava`).
   - Run `python -I tools/texture_pipeline/verify.py .` and report exit status, `errors`, and any notable warnings.

2. **Version Control**
   - Check `git status --short` and `git log -n 3 --oneline`.
   - Count untracked/new, modified, and deleted files, grouped by subsystem.

3. **System Progress**
   - Cross-check `MODDING_ROADMAP_AND_SPECS.md` against actual code in `src/main/java/pryuan05/pysift/` and `src/client/java/pryuan05/pysift/` (blocks, building sets, dimension/biomes, soul willow, spirit liquid & soul deprivation, portal ritual & renderer, 24 mobs + AI goals, creative tabs).

4. **Pending Items**
   - Highlight what still needs in-game verification, git commits, or design decisions.
