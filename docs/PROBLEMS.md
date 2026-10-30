# Problem statements

Theme: **AI belongs to everyone**. Build something new with open-source or open-weight AI doing real work.
Prize tracks: Best Use of Gemma 4 (multimodal, focused tools, rapid prototyping) and Best Open-Source AI Project
(agent skill, open-weight model, model harness). Each statement lists the tinyharness command that gets it running; the rest is prompt and polish.

| # | Problem statement | Track fit | Start with |
|---|---|---|---|
| 1 | Plain-language explainer for official letters (visa, residence permit, bank, university) that runs fully offline so private documents never leave the laptop. | Focused AI Tools | `python examples/letter_explainer.py letter.txt ./rules`, or `tinyharness --docs ./rules --preset plain chat` |
| 2 | Photo to action: point a camera at a bus stop sign, medicine box or menu in a foreign language and get a spoken-style answer in your own language. | Multimodal Experience | `tinyharness --preset translator --lang English serve`, upload the photo |
| 3 | Agent skill pack that teaches any assistant a local community's workflow (student union, food bank, repair cafe) as a standard SKILL.md folder. | Open-Source AI, agent skill | write `skills/<name>/SKILL.md`, check with `tinyharness skills --validate` |
| 4 | Study buddy that turns lecture slides or notes into quizzes with worked, step by step answers, local model only. | Focused AI Tools | `tinyharness --docs ./notes --preset quiz run "Quiz me on chapter 2"`, cited with `tinyharness ask ./notes "..."` |
| 5 | Accessibility describer: image to alt text and short audio-friendly description for blind or low-vision users, running on a cheap laptop. | Multimodal Experience | `tinyharness --preset describer run -i photo.jpg "Describe this"` or `examples/alt_text.py` |
| 6 | Tiny model harness: a clean tool-calling loop that works with any open-weight model, including ones with no native tool support. | Open-Source AI, model harness | `tinyharness --text-tools ...` or the `tinyharness.agent.Agent` class |
| 7 | Offline first-aid and emergency guide in plain language, with a retrieval step over a small trusted text folder. | Focused AI Tools | `tinyharness --preset firstaid ask ./sources "How do I treat a burn?"` |
| 8 | Repo helper for new open-source contributors: reads a repository and writes a good-first-issue map and setup guide. | Rapid Prototyping | `tinyharness --docs ./repo run "Use the repo-onboarding skill"` |
| 9 | Open-weight model comparison bench: same prompts, several local models, side by side latency and answers in a web page. | Open-Source AI, open-weight model | `tinyharness bench --models a,b "prompt"` |
| 10 | Language practice partner that corrects short messages and explains each mistake, tuned for low-resource languages. | Focused AI Tools | `tinyharness --preset coach --lang Hungarian --session me.json chat` |
| 11 | Receipt and invoice reader: photo to a clean table you own, with no cloud upload. | Multimodal Experience | `tinyharness extract --fields item:str,qty:int,price:float --many --csv -i receipt.jpg` |
| 12 | Community notice board summariser: long group-chat exports to a short weekly digest per language. | Rapid Prototyping | `tinyharness digest chat_export.txt --instruction "Weekly digest, one bullet per topic"` |
| 13 | Prompt-injection tester: a skill that attacks your own agent with known tricks and reports which ones worked. | Open-Source AI, agent skill | `tinyharness redteam` (exit code 1 if any attack leaked) |
| 14 | Kids' science tutor that answers from a fixed local textbook and refuses to guess outside it. | Focused AI Tools | `tinyharness ask ./textbook "Why is the sky blue?"` (refuses outside the book) |
| 15 | Hardware assistant: a sensor or camera on a board feeds readings to a local model that explains what is happening in plain words. Runs on a small ARM board; whether a given board can run the model is unchecked. | Hardware Wizard | `tinyharness doctor` then `--local` with the smallest model; use `extract` to turn readings into JSON |
| 16 | Deployable tool: package any of the above as a container with the engine inside, so a community can run it with one command. | Open-Source Contributor Raffle | write a small Dockerfile around `pip install .` and `tinyharness --local serve`; the CLI runs headless |

These are ideas generated from the published themes, not organiser requirements. Pick one in the first
fifteen minutes; every statement above runs with the commands shown, and no extra code is needed to get a first demo.
