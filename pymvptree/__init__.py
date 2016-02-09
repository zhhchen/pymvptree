import pickle

import _c_mvptree as mvp


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

            # Serialize `point_id`
            try:
                serialized_id = pickle.dumps(point_id, protocol=0)
            except TypeError as exc:
                raise ValueError("`point_id` must be serializable") from exc

            # `data` must be bytes
            if not isinstance(data, bytes):
                raise ValueError("data must be bytes")

            # Create the C object.
            c_obj = mvp.lib.mkpoint(serialized_id, data, len(data))

        elif c_obj is None:
            raise ValueError(
                "Either (`point_id` and `data`) or `c_obj` must be defined")

        if c_obj == mvp.ffi.NULL:
            raise ValueError("Invalid point NULL.")
        else:
            self._c_obj = c_obj

    @property
    def point_id(self):
        point_id_char_p = mvp.lib.get_point_id(self._c_obj)
        point_id_raw = mvp.ffi.string(point_id_char_p)
        return pickle.loads(point_id_raw)

    @property
    def data(self):
        datalen = mvp.lib.get_point_datalen(self._c_obj)
        data_void_p = mvp.lib.get_point_data(self._c_obj)
        return mvp.ffi.buffer(data_void_p, datalen)[:]


class Tree:
    def __init__(self, c_obj=None):
        self.points = []
        if c_obj is None:
            self._c_obj = mvp.lib.newtree()
        else:
            self._c_obj = c_obj

    @classmethod
    def from_file(cls, filename):
        return cls(c_obj=mvp.lib.load(filename.encode("utf-8")))

    def to_file(self, filename):
        mvp.lib.save(filename.encode("utf-8"), self._c_obj)

    def add(self, point):
        if not isinstance(point, Point):
            raise ValueError("Must be a point.")
        self.points.append(point)
        mvp.lib.addpoint(self._c_obj, point._c_obj)

    def exact(self, data):
        p = Point(b'', data)
        nbresults = ffi.lib.new("unsigned int *")
        error = ffi.lib.new("MVPError *")
        res = mvp.lib.mvptree_retrieve(self._c_obj, p._c_obj, 1, 1, nbresults, error)
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
