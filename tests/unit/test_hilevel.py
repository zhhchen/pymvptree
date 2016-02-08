import pytest

@pytest.mark.wip
def test_import_Tree():
    try:
        from pymvptree import Tree
    except ImportError:
        assert False, "Cannot import Tree."
