import pickle
from contextlib import contextmanager

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
    def __init__(self, point_id=None, data=None, c_obj=None):
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
            c_obj = mvp.lib.mkpoint(serialized_id, data, len(data))

        elif c_obj is None:
            raise ValueError(
                "Either (`point_id` and `data`) or `c_obj` must be defined")

        try:
            if mvp.ffi.typeof(c_obj).cname != 'struct mvp_datapoint_t *':
                raise TypeError("`c_obj` must be a MVPDP pointer.")
        except Exception as exc:
            raise TypeError("Invalid initialization value.") from exc
        else:
            self._c_obj = c_obj

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
            self._c_obj = mvp.lib.newtree()
        else:
            try:
                if mvp.ffi.typeof(c_obj).cname != 'MVPTree *':
                    raise TypeError("`c_obj` must be a MVPTree pointer.")
            except Exception as exc:
                raise TypeError("Invalid initialization value.") from exc
            else:
                self._c_obj = c_obj

        self.points = set()

    @classmethod
    def from_file(cls, filename):
        raw_filename = filename.encode("utf-8")
        with mvp_errors() as error:
            return mvp.lib.load(raw_filename, error)

    def to_file(self, filename):
        raw_filename = filename.encode("utf-8")
        with mvp_errors() as error:
            mvp.lib.save(raw_filename, self._c_obj, error)

    def add(self, point):
        if not isinstance(point, Point):
            raise TypeError("Must be a point.")

        if self.exact(point) is not None:
            self.points.add(point)
            mvp.lib.addpoint(self._c_obj, point._c_obj)

    def exact(self, data):
        p = Point(b'', data)
        nbresults = ffi.lib.new("unsigned int *")
        error = ffi.lib.new("MVPError *")
        res = mvp.lib.mvptree_retrieve(self._c_obj,
                                       p._c_obj,
                                       1,
                                       1,
                                       nbresults,
                                       error)
        if nbresults[0] > 0:
            return Point(c_obj=res[0])

    def search(self, data, radius, limit=65535):
        p = Point(b'', data)
        nbresults = ffi.lib.new("unsigned int *")
        error = ffi.lib.new("MVPError *")
        res = mvp.lib.mvptree_retrieve(self._c_obj,
                                       p._c_obj,
                                       limit,
                                       radius,
                                       nbresults,
                                       error)
        if error[0]:
            raise RuntimeError(ffi.lib.string(mvp.lib.mvp_errstr(error[0])))
        for i in range(nbresults[0]):
            try:
                p = Point(c_obj=res[i])
            except ValueError:
                break
            else:
                yield p
