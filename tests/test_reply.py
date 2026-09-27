import pytest

from jobparse_cli.reply import parse_reply


def test_valid_object_returns_dict():
    text = '{"title": "Backend Engineer", "skills": ["Python", "SQL"], "seniority": "mid"}'
    result = parse_reply(text)
    assert result == {
        "title": "Backend Engineer",
        "skills": ["Python", "SQL"],
        "seniority": "mid",
    }


def test_fenced_json_raises_value_error():
    text = '```json\n{"title": null, "skills": [], "seniority": null}\n```'
    with pytest.raises(ValueError):
        parse_reply(text)


def test_missing_key_raises_value_error():
    text = '{"title": "Engineer", "skills": []}'
    with pytest.raises(ValueError, match="missing key: seniority"):
        parse_reply(text)


def test_wrong_type_raises_value_error():
    text = '{"title": "Engineer", "skills": "Python", "seniority": "mid"}'
    with pytest.raises(ValueError, match="skills must be a list of strings"):
        parse_reply(text)


def test_out_of_range_seniority_raises_value_error():
    text = '{"title": "Engineer", "skills": [], "seniority": "staff"}'
    with pytest.raises(ValueError, match="seniority must be one of"):
        parse_reply(text)
