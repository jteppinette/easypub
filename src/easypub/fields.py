import bleach


class Slug(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("must be a string")

        if not v:
            raise ValueError("length must be greater than 1")

        for token in v:
            if not (token.islower() or token.isdigit() or token == "-"):
                raise ValueError(
                    "can only be made from lowercase letters, numeric digits, and hyphens"
                )

        if v.startswith("-") or v.endswith("-"):
            raise ValueError("cannot start or end with a hyphen")

        if "--" in v:
            raise ValueError("cannot have more than one hyphen in a row")

        return v

    def __repr__(self):
        return f"Slug({super().__repr__()})"


class SafeHTML(str):
    ALLOWED_TAGS = bleach.ALLOWED_TAGS + ["h1", "h2", "h3", "p", "br", "u"]

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("must be a string")

        return cls(bleach.clean(v, tags=cls.ALLOWED_TAGS))

    def __repr__(self):
        return f"SafeHTML({super().__repr__()})"
