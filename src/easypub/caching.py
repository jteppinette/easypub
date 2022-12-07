UNITS_TO_SECONDS = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800,
    "y": 31536000,
}


def duration_to_seconds(v: str) -> int:
    unit = v[-1]
    if unit not in UNITS_TO_SECONDS:
        raise ValueError(
            f'invalid unit "{unit}", must be in {", ".join(UNITS_TO_SECONDS.keys())}'
        )

    return int(v[:-1]) * UNITS_TO_SECONDS[unit]


def build_cache_control(**options) -> str:
    if options.get("immutable"):
        options = dict(max_age="1y") | options

    tokens = {
        key.replace("_", "-"): duration_to_seconds(value)
        if isinstance(value, str)
        else value
        for key, value in options.items()
    }

    if not any(tokens.values()):
        raise ValueError("cache-control header should not be empty")

    return ", ".join(
        [
            key if value is True else f"{key}={value}"
            for key, value in tokens.items()
            if value
        ]
    )
