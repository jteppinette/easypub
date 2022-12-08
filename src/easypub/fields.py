import bleach


class Title(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        v = v.strip()

        if not isinstance(v, str):
            raise TypeError("must be a string")

        if not v:
            raise ValueError("length must be greater than 1")

        if len(v) > 256:
            raise ValueError("length must be less than 256")

        return v

    def __repr__(self):
        return f"Title({super().__repr__()})"


class SafeHTML(str):
    ALLOWED_TAGS = bleach.ALLOWED_TAGS + ["h1", "h2", "h3", "p", "br", "u"]

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("must be a string")

        return cls(
            bleach.clean(v, strip=True, strip_comments=True, tags=cls.ALLOWED_TAGS)
        )

    def __repr__(self):
        return f"SafeHTML({super().__repr__()})"
