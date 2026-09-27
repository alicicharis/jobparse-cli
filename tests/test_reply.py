import pytest

from jobparse_cli.reply import NotAJobAdError, parse_reply


def test_valid_reply_dumps_without_is_job_ad():
    text = '{"is_job_ad": true, "title": "Backend Engineer", "skills": ["Python", "SQL"], "seniority": "mid"}'
    assert parse_reply(text).model_dump() == {
        "title": "Backend Engineer",
        "skills": ["Python", "SQL"],
        "seniority": "mid",
    }


def test_missing_key_raises_value_error():
    text = '{"is_job_ad": true, "title": "Engineer", "skills": []}'
    with pytest.raises(ValueError, match="invalid reply: seniority"):
        parse_reply(text)


def test_unexpected_key_raises_value_error():
    text = '{"is_job_ad": true, "title": "Engineer", "skills": [], "seniority": null, "salary": "100k"}'
    with pytest.raises(ValueError, match="invalid reply: salary"):
        parse_reply(text)


def test_wrong_type_raises_value_error():
    text = '{"is_job_ad": true, "title": "Engineer", "skills": "Python", "seniority": "mid"}'
    with pytest.raises(ValueError, match="invalid reply: skills"):
        parse_reply(text)


def test_out_of_range_seniority_raises_value_error():
    text = '{"is_job_ad": true, "title": "Engineer", "skills": [], "seniority": "staff"}'
    with pytest.raises(ValueError, match="invalid reply: seniority"):
        parse_reply(text)


def test_not_a_job_ad_raises_not_a_job_ad_error():
    text = '{"is_job_ad": false, "title": null, "skills": [], "seniority": null}'
    with pytest.raises(NotAJobAdError):
        parse_reply(text)
