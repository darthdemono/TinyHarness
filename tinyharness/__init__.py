"""@file __init__.py
@brief TinyHarness: a small, fast toolkit for building open-weight AI projects in a day.

Pure standard library. The package is deliberately flat; read the modules in
this order to understand the design:

1. client.py: one chat interface over Ollama and OpenAI-style servers.
2. agent.py: the tool-calling loop on top of a client.
3. tools.py, extras.py, skills.py: things an agent can use.
4. structured.py, flows.py, presets.py: reusable multi-call behaviours.
5. llamacpp.py, hw.py: the local engine (llama.cpp) and the hardware probe.
6. web.py, cli.py: the two front ends.
7. bench.py, redteam.py: measurement and attack tools.
"""

__version__ = "0.1.0"
