from hypothesis import given
from hypothesis import strategies as st
import pytest


def test_import_Point():
    try:
        from pymvptree import Point
    except ImportError:
        assert False, "Cannot import Point."


def test_Point_accept_bytes_in_data():
    from pymvptree import Point

    MYBYTES = b'TEST'
    p = Point(b'id', MYBYTES)
    assert p.data == MYBYTES

    with pytest.raises(TypeError):
        Point(b'id', 'NONBYTES')


@given(data=st.binary())
def test_Point_accept_ANY_bytes_in_data(data):
    from pymvptree import Point

    p = Point(b'id', data)
    assert p.data == data


def test_Point_point_id_must_be_serializable():
    from pymvptree import Point
    from queue import Queue

    with pytest.raises(TypeError):
        p = Point(Queue(), b'data')


def test_Point_needs_c_obj():
    from pymvptree import Point

    with pytest.raises(ValueError):
        p = Point()


def test_Point_c_obj_cant_be_NULL():
    from pymvptree import Point
    from _c_mvptree import ffi

    with pytest.raises(TypeError):
        c_obj = ffi.new('MVPDP *[1]', [ffi.NULL])
        p = Point(c_obj=c_obj[0])


def test_Point_needs_c_obj_cant_be_other_ctype():
    from pymvptree import Point
    from _c_mvptree import ffi

    with pytest.raises(TypeError):
        p = Point(c_obj=ffi.NULL)

    with pytest.raises(TypeError):
        p = Point(c_obj=ffi.new("int *"))


def test_Point_point_id_is_complex_object():
    from pymvptree import Point

    SOMETHING = (('a', (1, 2, 3)), ('b', "It's something!"))

    p = Point(point_id=SOMETHING, data=b'TEST')

    # Because is serialized and deserialized it must be equal but not
    # the same object
    assert p.point_id is not SOMETHING
    assert p.point_id == SOMETHING


def test_Point_point_id_must_be_hashable():
    from pymvptree import Point

    SOMETHING = ([], )

    with pytest.raises(TypeError):
        Point(point_id=SOMETHING, data=b'TEST')


def test_Point_is_comparable():
    from pymvptree import Point

    p1  = Point(b'ID', b'DATA1')
    p1_ = Point(b'ID', b'DATA1')

    p2 = Point(b'ID', b'DATA2')


    assert p1 == p1_
    assert p1 is not p1_
    assert p1 != p2


def test_Point_contains():
    from pymvptree import Point

    p1  = Point(b'ID', b'DATA1')
    p1_ = Point(b'ID', b'DATA1')

    p2 = Point(b'ID', b'DATA2')

    assert p1 in {p1, p2}
    assert p1 in {p1_, p2}
    assert p1 not in {p2}
