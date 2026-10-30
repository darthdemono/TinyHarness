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

## Rules found in the organisers' handbook (read 2026-10-30)

Sources: the public host handbook (github.com/MLH/hacktoberfest-handbook), the MLH standard hackathon rules (github.com/MLH/mlh-policies),
and Google's page on Gemma through the Gemini API. They shape what may be built and how it is judged.

- **Submission** goes through OrganizerHQ Challenges during the event: public repository link, project name, description, technologies used,
  optional demo URL, and every challenge the project enters must be ticked. The host sets when submissions open and close; they close before demos.
- **Best Open-Source AI Project**: one winning team (DEV Badge each, possibly a swag bag). Requirements: open-source or open-weight AI is an important part;
  public GitHub repository with an open-source licence; an agent skill must follow the Agent Skills standard; a model-harness entry needs an original
  implementation or meaningful changes to an existing open-source harness. "Small language model" means 10 billion parameters or fewer. The README should
  name the model and link its licence or terms. Strong entries show substantial technical work by the team, easy-to-verify source, licence, model and
  dependencies, and a working demonstration.
- **Best Use of Gemma 4**: the judges are told to confirm the project uses a Gemma model **through the Gemini API**, with the model named in the README and the
  integration visible in code or the demo. Hosted Gemma 4 models listed by Google: `gemma-4-31b-it` and `gemma-4-26b-a4b-it`. A purely local Gemma run does not
  obviously satisfy this wording.
- **Standard rules** (default unless the host states otherwise): all work on a project happens during the event; an earlier idea is allowed; libraries, frameworks
  and open-source code may be used; but "working on a project before the event and open-sourcing it for the sole purpose of using the code during the event is
  against the spirit of the rules and is not allowed". Teams must stop at the deadline (small fixes allowed). Code must stay public after the event.
  Teams must be honest and transparent about the AI code tools they used, including in the submission.
- **Judging criteria** in the standard rules: technology, design, completion, learning (weighed equally); demos are judged on what was built, not on pitch quality.

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
