import os

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
    from pymvptree import Tree, MVP_BRANCHFACTOR, MVP_PATHLENGTH, MVP_LEAFCAP
    from _c_mvptree import ffi, lib

    with pytest.raises(TypeError):
        Tree(c_obj=b'lala')

    with pytest.raises(TypeError):
        Tree(c_obj=ffi.new('int *'))

    with pytest.raises(TypeError):
        Tree(c_obj=ffi.NULL)

    Tree(c_obj=lib.mktree(MVP_BRANCHFACTOR, MVP_PATHLENGTH, MVP_LEAFCAP))


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


@given(data=st.lists(st.binary(min_size=4, max_size=4)))
def test_Tree_filter_all_points(data):
    from pymvptree import Tree, Point

    def hamming(p_a, p_b): 
        return sum(bin(a ^ b).count("1") for a, b in zip(p_a.data, p_b.data))

    t = Tree()

    all_points = {Point(b'', d) for d in data}
    for p in all_points:
        t.add(p)

    current_points = {p for p in t.filter(bytes(4), 4*8)}

    assert current_points == all_points


@given(data=st.lists(st.binary(min_size=4, max_size=4),
                     average_size=1000),
       target_data=st.binary(min_size=4, max_size=4),
       threshold=st.integers(min_value=0, max_value=32))
def test_Tree_filter_all_points_in_threshold(data, target_data, threshold):
    from pymvptree import Tree, Point

    target = Point(b'', target_data)

    def hamming(p_a, p_b): 
        return sum(bin(a ^ b).count("1") for a, b in zip(p_a.data, p_b.data))

    t = Tree()

    all_points = {Point(d, d) for d in data}
    accepted_points = []
    for p in all_points:
        try:
            t.add(p)
        except:
            assume(False)
        else:
            accepted_points.append(p)

    matching_points = {p.point_id
                       for p in accepted_points
                       if hamming(p, target) <= threshold}

    current_points = {p.point_id for p in t.filter(target.data, threshold)}

    assert current_points == matching_points


@given(data=st.lists(st.binary(min_size=4, max_size=4),
                     average_size=10000,
                     min_size=1),
       leafcap=st.integers(min_value=1, max_value=1024**2))
def test_Tree_save_and_load_match(data, leafcap):
    data = list(set(data))

    from pymvptree import Tree, Point
    from tempfile import mktemp

    t1 = Tree(leafcap=leafcap)

    saved_points = {Point(d, d) for d in data}
    for p in saved_points:
        try:
            t1.add(p)
        except:
            pass

    tempfile = mktemp()
    try:
        t1.to_file(tempfile)
        t2 = Tree.from_file(tempfile)
    finally:
        os.unlink(tempfile)

    # XXX: Review why len(data) + 2 is necessary here
    added_points = {p.point_id for p in t1.filter(bytes(4),
                                                  4 * 8,
                                                  limit=len(data) + 2)}
    loaded_points = {p.point_id for p in t2.filter(bytes(4),
                                                   4 * 8,
                                                   limit=len(data) + 2)}

    assert added_points == loaded_points


@given(leafcap=st.integers(min_value=1, max_value=50))
def test_Tree_add_same_data_but_different_point_id(leafcap):
    from pymvptree import Tree, Point

    t = Tree(leafcap=leafcap)

    for i in range(leafcap + 2):
        t.add(Point(i, b'TEST'))

    # LEAF is full
    with pytest.raises(RuntimeError):
        t.add(Point(-1, b'TEST'))

    ids = {p.point_id for p in t.filter(b'TEST', 0)}

    assert ids == set(range(leafcap + 2))


def test_Tree_add_until_full_then_search():
    from pymvptree import Tree, Point

    t = Tree(leafcap=3)

    for i in range(5):
        t.add(Point(i, b'TEST'))

    pre_full = {p.point_id for p in t.filter(b'TEST', 0)}

    # LEAF is full
    with pytest.raises(RuntimeError):
        t.add(Point(-1, b'TEST'))

    post_full = {p.point_id for p in t.filter(b'TEST', 0)}

    assert pre_full == post_full


@given(leafcap=st.integers(min_value=1, max_value=10),
       data=st.lists(st.binary(min_size=1, max_size=1),
                     min_size=1,
                     average_size=100))
def test_Tree_add_and_exists_until_full(leafcap, data):
    from pymvptree import Tree, Point

    t = Tree(leafcap=leafcap)

    added_data = set()

    for d in data:
        try:
            point = Point(d, d)
            t.add(point)
        except:
            break
        else:
            assert t.exists(Point(d, d))
            added_data.add(point)

    assert added_data
    assert added_data == set(t.filter(b'0', 8))


@given(point_id=st.text())
def test_Tree_Point_point_id_save_and_restore(point_id):
    from pymvptree import Tree, Point
    from tempfile import mktemp

    t1 = Tree()
    t1.add(Point(point_id, b'TEST'))

    tempfile = mktemp()
    try:
        t1.to_file(tempfile)
        t2 = Tree.from_file(tempfile)
    finally:
        os.unlink(tempfile)

    s1 = {p for p in t1.filter(b'TEST', 1)}
    s2 = {p for p in t2.filter(b'TEST', 1)}

    assert s1 == s2
    assert Point(point_id, b'TEST') in s1


@pytest.mark.wip
@given(leafcap=st.integers(min_value=1, max_value=8),
       max_value=st.integers(min_value=1, max_value=255))
def test_Tree_try_to_add_and_search(leafcap, max_value):
    from pymvptree import Tree, Point

    t = Tree(leafcap=leafcap)

    added_data = []

    maxlength = len(str(max_value))
    data_formatter = "%%0%d.d" % maxlength

    for i in range(max_value):
        try:
            t.add(Point(i, (data_formatter % i).encode("ascii")))
        except:
            pass
        else:
            added_data.append(i)
        finally:
            # YES, we do this in each iteration. The behaviour in issue
            # #1 is changing in each data addition.
            for d in added_data:
                # assert list(t.filter((data_formatter % d).encode("ascii"), 0))
                assert t.exists(Point(d, (data_formatter % d).encode("ascii")))
