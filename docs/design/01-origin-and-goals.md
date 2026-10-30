# Origin and goals

## Where it came from

TinyHarness was written ahead of a one-day open-model hackathon whose problem statement is revealed on the day. Everything about that event
(rules, prizes, problem-statement ideas, the demo outline and risks) is kept outside this repository, because TinyHarness is a general library
and the event project is a separate repository that depends on it (see D18).

## The goal

The problem is unknown in advance. The aim was therefore a very wide base so that a team can
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
