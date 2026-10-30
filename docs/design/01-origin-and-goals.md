# Origin and goals

## The event

Hacktoberfest Hack Day Budapest, Saturday 31 October 2026, 12:00 to 19:00, Puzl CowOrKing (Lajos u. 126-130),
organised with MLH. Hacktoberfest 2026 changed format: pull requests no longer count; participants build a
new project with open-source or open-weight AI doing real work. The stated theme is "AI belongs to everyone".

Rules as published on the event's challenge page (read 2026-10-30):

- Solo or a team of up to four.
- The project must be in a public GitHub or GitLab repository under an open-source licence before the
  deadline, or consist of meaningful pull requests to existing open-source projects made during the event.
- Every team gives a two-minute live demo of working code to be prize-eligible. No slide-only pitches.
  The page says 17:30; the schedule elsewhere says 17:15. Unresolved, check on the day.
- Five prize categories: Best Open-Source AI Project (agent skill, open-weight model or model harness),
  Best Use of Gemma 4 (multimodal, focused tools, rapid prototyping), Best Halloween Costume,
  Hardware Wizard (Arduino Uno Q kits), Open-Source Contributor Raffle (cloud-native tool or open-source PRs).
- The organisers reported on 2026-10-30 that physical merchandise is stuck in customs; prizes are mailed.

The theme's argument for open models (MLH's wording): access, pricing and policy can change overnight outside
an individual's control; open AI offers transparency and resilience. The design leans on this: everything
must work offline, locally and without any single vendor.

## The goal

The problem statement is revealed on the day. The aim was therefore a very wide base so that a team can
write the project-specific part in minutes and spend its time on the pitch. Consequences:

- Breadth over depth: many small reusable pieces (tools, skills, presets, flows) rather than one big feature.
- Zero install friction: no third-party Python packages, one command to fetch the engine, one to run.
- Must run on whatever laptop a teammate brings: Linux, macOS, Windows, x64 and arm64, with or without a GPU.
- Speed and efficiency: the engine is llama.cpp (quantised models on CPU or Vulkan GPU), not Python inference.
- Open by construction: Apache 2.0, public repository, open-weight models, no hosted dependency required.

## Non-goals

- Training or fine-tuning models.
- A polished product UI. The web page exists to demo; it has no authentication and binds to localhost.
- Competing with full agent frameworks. The loop is intentionally about 150 lines.
