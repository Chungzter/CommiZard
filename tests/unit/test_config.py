from commizard import config


def test_set_url(monkeypatch):
    monkeypatch.setattr(config, "LLM_URL", None)
    config.set_url("eggs and bacon")
    assert config.LLM_URL == "eggs and bacon"


def test_gen_request_url():
    assert config.gen_request_url() == "http://127.0.0.1:11434/api/generate"
