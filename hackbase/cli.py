"""hackbase chat | run PROMPT | skills | serve"""
import argparse
import sys

from . import skills as skills_mod
from .agent import Agent
from .client import Client, image_b64
from .web import make_server


def main(argv=None):
    p = argparse.ArgumentParser(prog="hackbase")
    p.add_argument("-m", "--model")
    p.add_argument("--backend", choices=["ollama", "openai"])
    p.add_argument("--url")
    p.add_argument("--skills", default="skills", help="folder of skill directories")
    p.add_argument("-s", "--system", default="")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("prompt")
    r.add_argument("-i", "--image", action="append", default=[])
    sub.add_parser("chat")
    sub.add_parser("skills")
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=8080)
    a = p.parse_args(argv)

    found = skills_mod.load(a.skills)
    if a.cmd == "skills":
        print(skills_mod.catalog(found) or "no skills in " + a.skills)
        return 0
    agent = Agent(Client(a.model, a.backend, a.url), system=a.system, skills=found)
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
