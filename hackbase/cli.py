"""hackbase chat | run | skills | serve | bench | extract | digest | ask"""
import argparse
import json
import os
import sys

from . import bench, flows
from . import skills as skills_mod
from .agent import Agent
from .client import Client, image_b64
from .presets import PRESETS
from .presets import get as preset
from .structured import ask_json, to_csv
from .tools import folder_tools
from .web import make_server


def main(argv=None):
    p = argparse.ArgumentParser(prog="hackbase")
    p.add_argument("-m", "--model")
    p.add_argument("--backend", choices=["ollama", "openai"])
    p.add_argument("--url")
    p.add_argument("--skills", default="skills", help="folder of skill directories")
    p.add_argument("-s", "--system", default="")
    p.add_argument("--preset", choices=sorted(PRESETS), help="role prompt, see hackbase.presets")
    p.add_argument("--lang", default="English", help="language the preset answers in")
    p.add_argument("--session", help="JSON file: conversation is loaded from it and saved back after each turn")
    p.add_argument("--text-tools", action="store_true", help="tool calls as JSON text, for models without native tools")
    p.add_argument("--docs", help="folder the agent may list, read and search")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("prompt")
    r.add_argument("-i", "--image", action="append", default=[])
    b = sub.add_parser("bench")
    b.add_argument("--models", required=True, help="comma separated model names")
    b.add_argument("prompts", nargs="+")
    e = sub.add_parser("extract", help="image or text to validated JSON or CSV")
    e.add_argument("--fields", required=True, help="name:type pairs, e.g. item:str,price:float")
    e.add_argument("--many", action="store_true", help="expect a list of rows")
    e.add_argument("--csv", action="store_true")
    e.add_argument("-i", "--image", action="append", default=[])
    e.add_argument("prompt", nargs="?", default="Extract the data.")
    d = sub.add_parser("digest", help="map-reduce summary of a long text file")
    d.add_argument("file")
    d.add_argument("--instruction", default="Summarise the key points as short bullets.")
    q = sub.add_parser("ask", help="answer only from a folder, with citations")
    q.add_argument("folder")
    q.add_argument("question")
    sub.add_parser("chat")
    k = sub.add_parser("skills")
    k.add_argument("--validate", action="store_true", help="check folders against the Agent Skills spec")
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=8080)
    a = p.parse_args(argv)

    if a.cmd == "bench":
        rows = bench.run(a.models.split(","), a.prompts, backend=a.backend, base_url=a.url)
        print(bench.table(rows))
        return 0
    found = skills_mod.load(a.skills)
    if a.cmd == "skills" and a.validate:
        problems = skills_mod.validate(a.skills)
        print("\n".join(problems) or "all skills valid")
        return 1 if problems else 0
    if a.cmd == "skills":
        print(skills_mod.catalog(found) or "no skills in " + a.skills)
        return 0
    client = Client(a.model, a.backend, a.url)
    system = (preset(a.preset, a.lang) + "\n" if a.preset else "") + a.system
    if a.cmd == "extract":
        schema = dict(x.split(":", 1) for x in a.fields.split(","))
        got = ask_json(client, a.prompt, schema, images=[image_b64(i) for i in a.image] or None, system=system, many=a.many)
        print(to_csv(got if a.many else [got], schema) if a.csv else json.dumps(got, ensure_ascii=False, indent=2), end="" if a.csv else "\n")
        return 0
    if a.cmd == "digest":
        with open(a.file, encoding="utf-8") as f:
            print(flows.digest(client, f.read(), a.instruction))
        return 0
    if a.cmd == "ask":
        ans, srcs = flows.grounded(client, a.question, a.folder, system=system)
        print(ans + ("\n\nSources: " + ", ".join(srcs) if srcs else ""))
        return 0
    agent = Agent(client, system=system, skills=found, native_tools=not a.text_tools)
    if a.session and os.path.exists(a.session):
        agent.load(a.session)
    if a.docs:
        agent.add_tools(folder_tools(a.docs))
    if a.cmd == "run":
        print(agent.run(a.prompt, images=[image_b64(i) for i in a.image] or None))
        if a.session:
            agent.save(a.session)
    elif a.cmd == "chat":
        try:
            while True:
                print(agent.run(input("> ")))
                if a.session:
                    agent.save(a.session)
        except (EOFError, KeyboardInterrupt):
            print()
    else:
        srv = make_server(agent, port=a.port)
        print("http://127.0.0.1:%d" % a.port)
        srv.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
