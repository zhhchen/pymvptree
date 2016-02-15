import pickle
import gc
from contextlib import contextmanager
import collections

import _c_mvptree as mvp


@contextmanager
def mvp_errors():
    try:
        error = mvp.ffi.new("MVPError *")
        yield error
    finally:
        err_str = mvp.ffi.string(mvp.lib.mvp_errstr(error[0]))
        if err_str == b"no error":
            pass
        elif err_str == b"could not open file":
            raise IOError(err_str)
        elif err_str == b"empty tree":
            pass
        else:
            raise RuntimeError(err_str)


class Point:
    """
    Represents a data point.

    :param point_id: Any pickelizable object.

    :param data: `bytes`, will be used as measurement data for the inner
                 hamming distance function. Usually your hash value.

    :param c_obj: You can instantiate this object using an `MVPDP`
                  object of `_c_mvptree` directly. Can't be used in
                  conjunction with `point_id` and/or `data`.

    """
    def __init__(self, point_id=None, data=None, c_obj=None,
                 owned_memory=True):
        self.owned_memory = owned_memory

        # Instantiate with `point_id` and `data`
        if point_id is not None and data is not None:

            # `point_id` must be hashable
            try:
                hash(point_id)
            except TypeError as exc:
                raise TypeError("`point_id` must be hashable.")

            # Serialize `point_id`
            serialized_id = pickle.dumps(point_id, protocol=0)

            # `data` must be bytes
            if not isinstance(data, bytes):
                raise TypeError("data must be bytes")

            # Create the C object.
            c_obj = mvp.lib.mkpoint(
                mvp.ffi.gc(mvp.ffi.new("char[]", init=serialized_id),
                           lambda x: None),
                mvp.ffi.gc(mvp.ffi.new("char[]", init=data),
                           lambda x: None),
                len(data))

        elif c_obj is None:
            raise ValueError(
                "Either (`point_id` and `data`) or `c_obj` must be defined")

        try:
            if mvp.ffi.typeof(c_obj) is not mvp.ffi.typeof("MVPDP *"):
                raise TypeError("`c_obj` must be a MVPDP pointer.")
            elif c_obj == mvp.ffi.NULL:
                raise TypeError("`c_obj` can't be a NULL pointer.")
        except Exception as exc:
            raise TypeError("Invalid initialization value.") from exc
        else:
            self._c_obj = mvp.ffi.gc(c_obj, self._delete_c_obj)

    def _delete_c_obj(self, c_obj):
        if self.owned_memory:
            mvp.lib.rmpoint(c_obj)

    @property
    def point_id(self):
        point_id_char_p = self._c_obj[0].id
        point_id_raw = mvp.ffi.string(point_id_char_p)
        return pickle.loads(point_id_raw)

    @property
    def data(self):
        datalen = self._c_obj[0].datalen
        data_void_p = self._c_obj[0].data
        return mvp.ffi.buffer(data_void_p, datalen)[:]

    def __hash__(self):
        return hash((self.point_id, self.data))

    def __eq__(self, other):
        return self.point_id == other.point_id and self.data == other.data


class Tree:
    def __init__(self, c_obj=None):
        if c_obj is None:
            _c_obj = mvp.lib.mktree()
        else:
            try:
                if mvp.ffi.typeof(c_obj) is not mvp.ffi.typeof('MVPTree *'):
                    raise TypeError("`c_obj` must be a MVPTree pointer.")
            except Exception as exc:
                raise TypeError("Invalid initialization value.") from exc
            else:
                _c_obj = c_obj

        self._c_obj = mvp.ffi.gc(_c_obj, mvp.lib.rmtree)

    @classmethod
    def from_file(cls, filename):
        raw_filename = filename.encode("utf-8")
        with mvp_errors() as error:
            return cls(c_obj=mvp.lib.load(raw_filename, error))

    def to_file(self, filename):
        raw_filename = filename.encode("utf-8")
        with mvp_errors() as error:
            mvp.lib.save(raw_filename, self._c_obj, error)

    def add(self, point):
        if isinstance(point, Point):
            pointlist = [point]
        elif isinstance(point, collections.Iterable) and \
                all(isinstance(p, Point) for p in point):
            pointlist = point
        else:
            raise TypeError("Must be a point or a list of points.")
        
        tree_points = set()

        for p in pointlist:
            if not self.exists(p):
                tree_points.add(Point(p.point_id, p.data, owned_memory=False))

        if tree_points:
            c_points = mvp.ffi.new('MVPDP *[%d]' % len(tree_points))

            for idx, p in enumerate(tree_points):
                c_points[idx] = p._c_obj

            with mvp_errors() as error:
                error[0] = mvp.lib.mvptree_add(self._c_obj,
                                               c_points,
                                               len(tree_points))
            return True
        else:
            return False

    def get(self, point):
        for found in self.filter(point.data, 0):
            if found == point:
                return point
        raise ValueError("Point not found")

    def exists(self, point):
        try:
            self.get(point)
        except ValueError:
            return False
        else:
            return True

    def filter(self, data, radius, limit=65535):
        p = Point(b'', data)
        nbresults = mvp.ffi.new("unsigned int *")

        try:
            with mvp_errors() as error:
                res = mvp.lib.mvptree_retrieve(self._c_obj,
                                               p._c_obj,
                                               limit,
                                               radius,
                                               nbresults,
                                               error)

            for i in range(nbresults[0]):
                try:
                    p = Point(c_obj=res[i], owned_memory=False)
                except TypeError:
                    pass
                else:
                    yield p
        finally:
            if res is not mvp.ffi.NULL:
                mvp.lib.free(res)
