from datetime import date

from app.scraper.parser import (
    _NOT_A_COUNTRY_RE,
    _parse_nights,
    _parse_review_date,
    _parse_score,
    _parse_stay_month,
)


def test_parse_review_date_day_first_en_au():
    assert _parse_review_date("9 July 2026") == date(2026, 7, 9)


def test_parse_review_date_us_format_fallback():
    assert _parse_review_date("July 9, 2026") == date(2026, 7, 9)


def test_parse_review_date_strips_reviewed_prefix():
    assert _parse_review_date("Reviewed: 9 July 2026") == date(2026, 7, 9)


def test_parse_review_date_none_on_garbage():
    assert _parse_review_date("not a date") is None


def test_parse_review_date_none_on_empty():
    assert _parse_review_date(None) is None
    assert _parse_review_date("") is None


def test_not_a_country_regex_rejects_placeholders():
    assert _NOT_A_COUNTRY_RE.match("7 reviews")
    assert _NOT_A_COUNTRY_RE.match("1 review")
    assert _NOT_A_COUNTRY_RE.match("Active since 2018")


def test_not_a_country_regex_accepts_real_countries():
    assert not _NOT_A_COUNTRY_RE.match("Australia")
    assert not _NOT_A_COUNTRY_RE.match("Italy")


def test_parse_stay_month():
    assert _parse_stay_month("July 2026") == date(2026, 7, 1)
    assert _parse_stay_month(None) is None
    assert _parse_stay_month("garbage") is None


def test_parse_score():
    assert _parse_score("8.5") == 8.5
    assert _parse_score("Scored 10") == 10.0
    assert _parse_score(None) is None
    assert _parse_score("no digits here") is None


def test_parse_nights():
    assert _parse_nights("3 nights") == 3
    assert _parse_nights(None) is None
