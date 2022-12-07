import pytest

from easypub.caching import build_cache_control, duration_to_seconds


@pytest.mark.parametrize(
    "value, expected",
    [
        ("1s", 1),
        ("5s", 5),
        ("1m", 60),
        ("1h", 3600),
        ("1d", 86400),
        ("1w", 604800),
        ("1y", 31536000),
    ],
)
def test_duration_to_seconds(value, expected):
    assert duration_to_seconds(value) == expected


@pytest.mark.parametrize(
    "options, expected",
    [
        (dict(immutable=True), "max-age=31536000, immutable"),
        (dict(max_age="5s"), "max-age=5"),
        (
            dict(max_age="5s", stale_while_revalidate="1s"),
            "max-age=5, stale-while-revalidate=1",
        ),
    ],
)
def test_build_cache_control(options, expected):
    assert build_cache_control(**options) == expected
