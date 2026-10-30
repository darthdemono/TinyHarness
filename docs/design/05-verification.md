# Verification: what was measured, and what was not

## Machine used for measurements

Intel i5-6600K (4 cores), 16 GB RAM, NVIDIA RTX 2060 6 GB, Linux (Fedora-based), llama.cpp build b12015, Python 3.14.

## Measured

| Claim | Result | How |
|---|---|---|
| Engine download and checksum | Worked; build reports `version: 0.8.0-dev (build 12015)` | `llamacpp.install()` then `llama-server --version` |
| Gemma 3 270M, CPU | Answered a one-word prompt in about 33 s including download | `--local ggml-org/gemma-3-270m-it-GGUF run ...` |
| Gemma 4 E2B Q4_0, image | Described a generated red sign "STOP 30" correctly (CPU, 94 s total, mostly load) | `run -i image.png ...` |
| Gemma 4 E2B Q4_0, tool call | Used `search_docs` and answered correctly from the file (CPU and GPU) | `--docs DIR` |
| Same, calculator tool | Answered 391 for 17 x 23 using the tool | `--extras --offline` |
| GPU speed | 57 to 84 generated tokens per second with Vulkan, about 3 on CPU | llama-server timing lines in the log |
| Offline start from cache | Worked | `--offline` |
| Web UI streaming | Tokens arrived as newline-delimited JSON from a real model | `curl -N` against `serve` |
| Unit tests | 122 pass; 100 percent line and branch coverage | `pytest --cov` |
| Platform matrix | 18 of 18 CI jobs green on first run | GitHub Actions run 41117895975 |
| Vault key delivery | Real vault entry reached a local server as a 56-character bearer token; value never printed | `--unv Groq` against a fake server |

First-run model download (about 3.4 GB with the image projector) took roughly six minutes on the development connection.
A cold start with the model cached takes about 50 seconds, mostly loading.

## Not verified

- Any machine other than the one above (macOS, Windows and arm64 only ran the unit tests and the engine download job).
- The Gemma 4 E4B model on a 6 GB GPU.
- Audio input (not attempted; support for it in the chosen model is unchecked).
- The web page in a real browser (only the streaming endpoint was exercised).
- Hosted endpoints such as Groq (the key delivery was tested, no request to the service was made).
- Behaviour of the CUDA or ROCm builds, and the Arduino boards from the hardware category.
- The `/releases` asset naming for future llama.cpp builds; the CI engine job will fail if names change.
