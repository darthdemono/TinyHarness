import pytest

from fake_server import start
from hackbase.client import Client
from hackbase.structured import ask_json, find_json, to_csv

S = {"item": "str", "price": "float"}


def scripted(*replies):
    it = iter(replies)
    return start(lambda b: {"role": "assistant", "content": next(it)})


def test_find_json_inside_fence_and_chatter():
    assert find_json('Sure:\n```json\n{"a": [1, 2]}\n```') == {"a": [1, 2]}
    with pytest.raises(ValueError):
        find_json("nothing here")


def test_retry_feeds_error_back_then_succeeds():
    srv, url = scripted('{"item": "tea"}', '{"item": "tea", "price": 2.5}')
    got = ask_json(Client(model="m", base_url=url), "read", S)
    assert got == {"item": "tea", "price": 2.5}
    assert "missing key: price" in srv.seen[1][1]["messages"][-1]["content"]


def test_many_rows_and_csv():
    _, url = scripted('[{"item": "a", "price": 1}, {"item": "b", "price": 2.5}]')
    rows = ask_json(Client(model="m", base_url=url), "read", S, many=True)
    assert to_csv(rows, S) == "item,price\na,1\nb,2.5\n"


def test_gives_up_and_rejects_bool_as_number():
    _, url = scripted('{"item": "a", "price": true}', '{"item": "a", "price": true}')
    with pytest.raises(ValueError, match="should be float"):
        ask_json(Client(model="m", base_url=url), "read", S, retries=1)
