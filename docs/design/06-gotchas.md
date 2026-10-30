# Gotchas

Things that already cost time. Check here before debugging.

## Engine and models
- **`/releases/latest` is useless for llama.cpp.** It returns a stub release; use the releases list (see D3).
- **llama-server `-np` defaults to auto**, which allocates several slots and multiplies KV-cache memory. We pass `-np 1`.
- **Sizes**: a 3 to 5 GB model download over venue Wi-Fi is not realistic. Run once at home; use `--offline` after.
- **System temp can be a small RAM disk.** `/tmp` was full on the development machine and broke an archive download with
  "No space left on device". Downloads and unpacking therefore go to `~/.tinyharness`, never the system temp folder.
- **GPU needs the Vulkan build**: `--gpu` switches variant; the plain build silently uses the CPU.
- **First prompt is slow**: warm-up and prompt processing on the first request (about 4 tokens per second measured), then
  fast (hundreds of tokens per second for the prompt). Do a throwaway request before a live demo.
- **Gemma 4 downloads a separate projector file** for images (`mmproj`); `-hf` fetches it automatically. Text-only models have none.

## Protocol details
- **OpenAI-style servers reject tool-call history without `type: function`** (HTTP 500, "Missing tool call type"). The client
  adds it (`Client._wire`). If you build messages yourself, go through `Client`.
- **Tool arguments** arrive as a dict from Ollama and as JSON text from OpenAI-style servers; the agent handles both.
- **Streaming** is newline-delimited JSON for Ollama and `data:`-prefixed server-sent events for OpenAI style; blank lines and
  comment lines are ignored.

## Command line
- **Global flags go before the subcommand**: `tinyharness --local --gpu run "..."`, not `tinyharness run --gpu ...`.
- **`--skills` default**: `./skills` if that folder exists, otherwise the bundled skills. Tests pass `--skills` explicitly.
- **`--unv` re-executes the process** with `python -m tinyharness.cli`; that is why `python -m tinyharness.cli` must keep working.

## Tests and tooling
- **Doxygen**: `PYTHON_DOCSTRING = NO` is correct (see D16). With YES, `@param` prints literally.
- **Tool descriptions come from docstrings** (first paragraph only). Putting Doxygen tags in the first paragraph leaks them to the model.
- **Coverage gate is 100 percent** on Linux; if a platform-specific line cannot be reached on Linux, patch `os.name` or the
  relevant call in the test rather than excluding the line.
- **Tests that start servers** bind port 0 and shut down; do not hard-code ports.
- **Shell pitfall**: `pkill -f tinyharness` also kills the shell running the command if its text matches. Match the binary name or use the PID.
- **pytest `-q` with the coverage plugin** prints the table only when `--cov` is given; the config sets the source and the threshold.

## Repository and process
- **Local working files are ignored** (see `.gitignore`); do not commit editor, notes or tool folders.
- **Commit messages**: one plain sentence, no trailers (see 08).
- **Main is the published branch**; the first publish pushed the existing history as `main`. Later work goes through branches and pull requests.
