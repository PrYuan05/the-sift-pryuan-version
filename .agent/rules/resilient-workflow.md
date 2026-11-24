---
trigger: always_on
description: Resilient workflow guidelines to survive Antigravity server restarts, protect long-running Minecraft client sessions, and keep tablet Artifact previews under the 2 MB proxy limit.
---

# Resilient Workflow Rules (The Sift Workspace)

Follow these practices so background server restarts never break multi-step work or lose progress:

1. **Checkpoint Multi-Step Work to Disk**
   - For multi-step pipelines (texture generation, worldgen sync, batch verification, screenshot capture), write reusable scripts under `tools/` and persist intermediate outputs/files to disk before moving to the next step.
   - Avoid fragile inline shell quoting for complex Python scripts; prefer writing a clean `.py` script and running it so it can be re-run cleanly after any interruption.

2. **Keep the Minecraft Client Outside Agent Daemon Processes**
   - Before launching `.\gradlew.bat runClient`, always check `desktop_list_windows` to see if the user already has a Minecraft client open (e.g., launched from IntelliJ IDEA or a standalone terminal).
   - Prefer interacting with an externally launched Minecraft window so an Antigravity server restart will never kill the live game session.
   - If the agent must launch `runClient`, prefer detaching it cleanly or reminding the user to launch from IntelliJ IDEA for long testing sessions.

3. **Graceful Recovery After Server Restarts**
   - When a `<SYSTEM_MESSAGE>` reports that background tasks were stopped due to a server restart, immediately verify actual disk outputs and live windows before retrying—never assume a prior step finished or failed from memory alone, and resume directly from the next incomplete step.

4. **Tablet / Remote Proxy-Safe Visual Artifacts (< 2 MB Limit)**
   - When creating user-facing Markdown Artifacts containing screenshots or 3D previews, resize/compress images to crisp JPEGs (`width <= 1280px`, `quality = 82..85`, ~70–150 KB each) and split large galleries so each Artifact stays comfortably under the 2 MB (`2,097,152 bytes`) upstream proxy limit.
   - Copy screenshots out of temporary capture folders into the artifact directory immediately so auto-pruning does not delete earlier captures.
