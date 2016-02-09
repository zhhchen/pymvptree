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
def test_import_Point():
    try:
        from pymvptree import Point
    except ImportError:
        assert False, "Cannot import Point."


@pytest.mark.wip
def test_Point_accept_bytes_in_data():
    from pymvptree import Point

    MYBYTES = b'TEST'
    p = Point(b'id', MYBYTES)
    assert p.data == MYBYTES

    with pytest.raises(ValueError):
        Point(b'id', 'NONBYTES')


@pytest.mark.wip
@given(data=st.binary())
def test_Point_accept_ANY_bytes_in_data(data):
    from pymvptree import Point

    p = Point(b'id', data)
    assert p.data == data


@pytest.mark.wip
def test_Point_point_id_must_be_serializable():
    from pymvptree import Point
    from queue import Queue

    with pytest.raises(ValueError):
        p = Point(Queue(), b'data')


@pytest.mark.wip
def test_Point_needs_c_obj():
    from pymvptree import Point

    with pytest.raises(ValueError):
        p = Point()


@pytest.mark.wip
def test_Point_needs_c_obj_cant_be_null():
    from pymvptree import Point
    from _c_mvptree import ffi

    with pytest.raises(ValueError):
        p = Point(c_obj=ffi.NULL)


@pytest.mark.wip
def test_Point_point_id_is_complex_object():
    from pymvptree import Point

    SOMETHING = {'a': [1, 2, 3], 'b': "It's something!"}

    p = Point(point_id=SOMETHING, data=b'TEST')

    # Because is serialized and deserialized it must be equal but not
    # the same object
    assert p.point_id is not SOMETHING
    assert p.point_id == SOMETHING
