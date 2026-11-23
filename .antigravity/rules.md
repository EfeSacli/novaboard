# Antigravity Workspace Rules — Developer-Grade UI, Mechanical Audio & Telemetry

1. **Always adhere to `SYSTEM_DESIGN_RULES.md`** in the repository root.
2. **Visual Palette:** Use monochrome dark surfaces (`#09090b`, `#121214`, `#18181b`), `1px` crisp borders (`#27272a`), minimal border radius (`4px–6px`), and a single functional accent (`#10b981` emerald or `#f59e0b` amber). Never use gradients, neon glows, glassmorphism, or decorative emoji clutter.
3. **Typography:** Use monospaced fonts (`Consolas` / `JetBrains Mono` / `DejaVu Sans Mono`) for all numeric metrics, timers, counters, badges, diffs, latency readouts, and command logs.
4. **Audio Engine:** Use zero-latency synthesized mechanical switch/relay impulses (`150Hz–400Hz` short tactile clicks, dry mechanical thuds for confirmation, low-frequency pulses for errors) and expose an always-accessible `AUDIO: ON/OFF` toggle in the status bar.
5. **Engineering Components:** Include the Context & Latency Inspector status bar, monospaced micro-log stream (`> Action...`), and line-numbered `+`/`-` Diff viewer for data mutations.
