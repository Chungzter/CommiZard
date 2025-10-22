from commizard import config


def test_gen_request_url():
    assert config.gen_request_url() == "http://127.0.0.1:11434/api/generate"
