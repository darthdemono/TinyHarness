"""hackbase chat | run PROMPT | skills | serve | bench"""
import argparse
import sys

from . import bench
from . import skills as skills_mod
from .agent import Agent
from .client import Client, image_b64
from .tools import folder_tools
from .web import make_server


def main(argv=None):
    p = argparse.ArgumentParser(prog="hackbase")
    p.add_argument("-m", "--model")
    p.add_argument("--backend", choices=["ollama", "openai"])
    p.add_argument("--url")
    p.add_argument("--skills", default="skills", help="folder of skill directories")
    p.add_argument("-s", "--system", default="")
    p.add_argument("--text-tools", action="store_true", help="tool calls as JSON text, for models without native tools")
    p.add_argument("--docs", help="folder the agent may list, read and search")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("prompt")
    r.add_argument("-i", "--image", action="append", default=[])
    b = sub.add_parser("bench")
    b.add_argument("--models", required=True, help="comma separated model names")
    b.add_argument("prompts", nargs="+")
    sub.add_parser("chat")
    sub.add_parser("skills")
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=8080)
    a = p.parse_args(argv)

    if a.cmd == "bench":
        rows = bench.run(a.models.split(","), a.prompts, backend=a.backend, base_url=a.url)
        print(bench.table(rows))
        return 0
    found = skills_mod.load(a.skills)
    if a.cmd == "skills":
        print(skills_mod.catalog(found) or "no skills in " + a.skills)
        return 0
    agent = Agent(Client(a.model, a.backend, a.url), system=a.system, skills=found, native_tools=not a.text_tools)
    if a.docs:
        agent.add_tools(folder_tools(a.docs))
    if a.cmd == "run":
        print(agent.run(a.prompt, images=[image_b64(i) for i in a.image] or None))
    elif a.cmd == "chat":
        try:
            while True:
                print(agent.run(input("> ")))
        except (EOFError, KeyboardInterrupt):
            print()
    else:
        srv = make_server(agent, port=a.port)
        print("http://127.0.0.1:%d" % a.port)
        srv.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
