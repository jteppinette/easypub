import pytest

from easypub.fields import SafeHTML


@pytest.mark.parametrize(
    "value, expected",
    [
        ('<p>hi<span class="ql-cursor"></span></p>', "<p>hi</p>"),
        ("<p>hi<script>console.log()</script></p>", "<p>hiconsole.log()</p>"),
    ],
)
def test_safe_html(value, expected):
    assert SafeHTML.validate(value) == expected
