from hypothesis import given
from hypothesis import strategies as st
import pytest


@pytest.mark.wip
def test_import_Tree():
    try:
        from pymvptree import Tree
    except ImportError:
        assert False, "Cannot import Tree."


@pytest.mark.wip
def test_Tree_new():
    from pymvptree import Tree

    t = Tree()

    assert t._c_obj


@pytest.mark.wip
def test_Tree_c_obj_must_be_MVPTree():
    from pymvptree import Tree
    from _c_mvptree import ffi, lib

    with pytest.raises(TypeError):
        Tree(c_obj=b'lala')

    with pytest.raises(TypeError):
        Tree(c_obj=ffi.new('int *'))

    with pytest.raises(TypeError):
        Tree(c_obj=ffi.NULL)

    Tree(c_obj=lib.newtree())


@pytest.mark.wip
def test_Tree_load_from_file_unknown():
    from pymvptree import Tree
    from tempfile import mktemp

    with pytest.raises(IOError):
        Tree.from_file(mktemp())


@pytest.mark.wip
def test_Tree_save_to_file_impossible():
    from pymvptree import Tree
    from tempfile import TemporaryDirectory

    t = Tree()
    with TemporaryDirectory() as filename:
        with pytest.raises(RuntimeError):
            t.to_file(filename)


@pytest.mark.wip
def test_Tree_add_non_point():
    from pymvptree import Tree

    t = Tree()
    with pytest.raises(TypeError):
        t.add(b'ojete')
