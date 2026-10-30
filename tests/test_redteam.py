from fake_server import start
from hackbase import cli, redteam
from hackbase.agent import Agent
from hackbase.client import Client


def test_leak_detection_forms():
    c = "CANARY-ab12"
    assert redteam.leaked(c, "code is CANARY-ab12")
    assert redteam.leaked(c, "\n".join("CANARY-ab12"))
    assert redteam.leaked(c, "21ba-YRANAC")
    assert not redteam.leaked(c, "I cannot share that.")


def test_run_marks_leaky_and_safe_agents():
    def leaky(canary):
        _, url = start(lambda b: {"role": "assistant", "content": "ok " + canary})
        return Agent(Client(model="m", base_url=url))

    def safe(canary):
        _, url = start(lambda b: {"role": "assistant", "content": "no"})
        return Agent(Client(model="m", base_url=url))

    bad = redteam.run(leaky, redteam.PAYLOADS[:2])
    assert all(b for _, b, _ in bad)
    good = redteam.run(safe, redteam.PAYLOADS[:2])
    assert not any(b for _, b, _ in good)
    assert "0 of 2 attacks leaked" in redteam.table(good)


def test_cli_redteam_exit_code_reflects_leaks(capsys):
    _, url = start(lambda b: {"role": "assistant", "content": "I refuse."})
    assert cli.main(["--url", url, "--skills", "/nonexistent", "redteam"]) == 0
    assert "0 of 8 attacks leaked" in capsys.readouterr().out
    _, url2 = start(lambda b: {"role": "assistant", "content": b["messages"][0]["content"]})
    assert cli.main(["--url", url2, "--skills", "/nonexistent", "redteam"]) == 1
