from hypothesis import given, assume, example
from hypothesis import strategies as st
import pytest


def test_import_Tree():
    try:
        from pymvptree import Tree
    except ImportError:
        assert False, "Cannot import Tree."


def test_Tree_new():
    from pymvptree import Tree

    t = Tree()

    assert t._c_obj


def test_Tree_c_obj_must_be_MVPTree():
    from pymvptree import Tree
    from _c_mvptree import ffi, lib

    with pytest.raises(TypeError):
        Tree(c_obj=b'lala')

    with pytest.raises(TypeError):
        Tree(c_obj=ffi.new('int *'))

    with pytest.raises(TypeError):
        Tree(c_obj=ffi.NULL)

    Tree(c_obj=lib.mktree())


def test_Tree_load_from_file_unknown():
    from pymvptree import Tree
    from tempfile import mktemp

    with pytest.raises(IOError):
        Tree.from_file(mktemp())


def test_Tree_save_to_file_impossible():
    from pymvptree import Tree
    from tempfile import TemporaryDirectory

    t = Tree()
    with TemporaryDirectory() as filename:
        with pytest.raises(RuntimeError):
            t.to_file(filename)


def test_Tree_add_non_point():
    from pymvptree import Tree

    t = Tree()
    with pytest.raises(TypeError):
        t.add(b'BADTYPE')


@given(numpoints=st.integers(min_value=0, max_value=100))
def test_Tree_add_returns_same_number(numpoints):
    from pymvptree import Tree, Point
    from hashlib import md5

    t = Tree()
    for i in range(numpoints):
        t.add(Point(('p%d' % i).encode('ascii'),
                    md5(bytes(i)).digest()))

    assert len(list(t.filter(bytes(16), 16*8))) == numpoints


@given(numpoints=st.integers(min_value=0, max_value=100))
def test_Tree_add_list_returns_same_number(numpoints):
    from pymvptree import Tree, Point
    from hashlib import md5

    t = Tree()
    pp = []
    for i in range(numpoints):
        pp.append(Point(('p%d' % i).encode('ascii'),
                        md5(bytes(i)).digest()))

    t.add(pp)
    assert len(list(t.filter(bytes(16), 16*8))) == numpoints


def test_Tree_add_returns_True_on_added():
    from pymvptree import Tree, Point

    t = Tree()
    p = Point(b'', b'')
    assert t.add(p) is True


def test_Tree_add_returns_False_on_non_added():
    from pymvptree import Tree, Point

    t = Tree()
    p = Point(b'', b'')
    t.add(p)
    assert t.add(p) is False


@given(data=st.binary(min_size=1))
def test_Tree_get_from_memory(data):
    from pymvptree import Tree, Point

    p = Point(b'', data)
    t = Tree()
    t.add(p)

    found = t.get(p) 

    assert found == p


@given(data=st.binary())
def test_Tree_exists_zero(data):
    from pymvptree import Tree, Point

    p = Point(b'', data)
    t = Tree()

    assert not t.exists(p)


@given(p1_data=st.binary(), p2_data=st.binary())
@example(p1_data=bytes(4), p2_data=b'\x00\x00\x00\x01')
def test_Tree_exists_one_different(p1_data, p2_data):
    from pymvptree import Tree, Point

    assume(p1_data != p2_data)

    p = Point(b'p1', p1_data)
    t = Tree()
    t.add(p)

    assert not t.exists(Point(b'p2', p2_data))


@given(p1_data=st.binary())
def test_Tree_exists_one_equal(p1_data):
    from pymvptree import Tree, Point

    t = Tree()
    p = Point(b'', p1_data)
    t.add(p)

    assert t.exists(Point(b'', p1_data))


def test_Tree_get_needs_arguments():
    from pymvptree import Tree 

    t = Tree()
    with pytest.raises(TypeError):
        assert t.get()


def test_Tree_get_zero():
    from pymvptree import Tree, Point

    t = Tree()

    with pytest.raises(ValueError):
        t.get(Point(b'', b''))


@given(datas=st.lists(st.binary(min_size=4, max_size=4)))
def test_Tree_filter_all_points(datas):
    from pymvptree import Tree, Point

    def hamming(p_a, p_b): 
        return sum(bin(a ^ b).count("1") for a, b in zip(p_a.data, p_b.data))

    t = Tree()

    all_points = {Point(b'', d) for d in datas}
    for p in all_points:
        t.add(p)
    
    current_points = {p for p in t.filter(bytes(4), 4*8)}

    assert current_points == all_points


@given(datas=st.lists(st.binary(min_size=4, max_size=4),
                      average_size=100),
       target_data=st.binary(min_size=4, max_size=4),
       threshold=st.integers(min_value=0, max_value=32))
def test_Tree_filter_all_points_in_threshold(datas, target_data, threshold):
    from pymvptree import Tree, Point

    target = Point(b'', target_data)

    def hamming(p_a, p_b): 
        return sum(bin(a ^ b).count("1") for a, b in zip(p_a.data, p_b.data))

    t = Tree()

    all_points = {Point(b'', d) for d in datas}
    accepted_points = []
    for p in all_points:
        try:
            t.add(p)
        except:
            pass
        else:
            accepted_points.append(p)

    matching_points = {p
                       for p in accepted_points
                       if hamming(p, target) <= threshold}
    
    current_points = {p for p in t.filter(target.data, threshold)}

    assert current_points == matching_points


@given(datas=st.lists(st.binary(min_size=4, max_size=4),
                      average_size=10000,
                      min_size=1,
                      unique=True))
def test_Tree_save_and_load_match(datas):
    from pymvptree import Tree, Point
    from tempfile import mktemp

    t1 = Tree()

    saved_points = {Point(b'', d) for d in datas}
    for p in saved_points:
        try:
            t1.add(p)
        except:
            pass

    tempfile = mktemp()
    t1.to_file(tempfile)
    added_points = {p for p in t1.filter(bytes(4), 4*8)}

    t2 = Tree.from_file(tempfile)
    loaded_points = {p for p in t2.filter(bytes(4), 4*8)}

    assert added_points == loaded_points
