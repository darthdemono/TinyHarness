from fake_server import start
from tinyharness import bench, cli


def test_rows_and_table_records_failure_per_model():
    _, url = start(lambda b: {"role": "assistant", "content": "ans " + b["model"]})
    rows = bench.run(["a", "b"], ["q|1"], base_url=url)
    assert [r[0] for r in rows] == ["a", "b"] and rows[0][3] == "ans a"
    bad = bench.run(["x"], ["q"], base_url="http://127.0.0.1:1")
    assert bad[0][3].startswith("error:")
    t = bench.table(rows)
    assert t.splitlines()[2].startswith("| a | q/1 |") and "|---|" in t


def test_cli_bench(capsys):
    _, url = start(lambda b: {"role": "assistant", "content": "hello"})
    assert cli.main(["--url", url, "bench", "--models", "m1,m2", "hi"]) == 0
    out = capsys.readouterr().out
    assert "| m1 | hi |" in out and "| m2 | hi |" in out
