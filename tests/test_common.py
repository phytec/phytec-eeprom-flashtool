import pytest
from src.common import str_to_revision
from src.common import sub_revision_to_str

@pytest.mark.parametrize("value, expect", [
    ("1", (1, '0000')),
    ("1a", (1, '0001')),
    ("3a", (3, '0001')),
    ("3b", (3, '0010')),
    ("3o", (3, '1111')),
])
def test_str_to_revision(value, expect):
    """test str_to_revision"""
    revs = str_to_revision(value)
    assert revs == expect

@pytest.mark.parametrize("value", [
    ("3p"),
])
def test_str_to_revision_failure(value):
    """test str_to_revision"""
    with pytest.raises(ValueError):
        str_to_revision(value)

@pytest.mark.parametrize("value, expect", [
    ("0001", ('a')),
])
def test_sub_revision_to_str(value, expect):
    """test sub_revision_to_str"""
    revs = sub_revision_to_str(value)
    assert revs == expect
