import pytest


@pytest.mark.wip
def test_package_import():
    try:
        import pymvptree
    except ImportError as exc:
        assert False, "Cannot import pymvptree."
