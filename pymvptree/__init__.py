from contextlib import contextmanager
from enum import IntEnum
import base64
import collections
import os
import pickle

import _c_mvptree as mvp


MVP_BRANCHFACTOR = 2
MVP_PATHLENGTH   = 5
MVP_LEAFCAP      = 25


class MVPError(IntEnum):
    MVP_SUCCESS        = 0
    MVP_ARGERR         = 1
    MVP_NODISTANCEFUNC = 2
    MVP_MEMALLOC       = 3
    MVP_NOLEAF         = 4
    MVP_NOINTERNAL     = 5
    MVP_PATHALLOC      = 6
    MVP_VPNOSELECT     = 7
    MVP_NOSV1RANGE     = 8
    MVP_NOSV2RANGE     = 9
    MVP_NOSPACE        = 10
    MVP_NOSORT         = 11
    MVP_FILEOPEN       = 12
    MVP_FILECLOSE      = 13
    MVP_MEMMAP         = 14
    MVP_MUNMAP         = 15
    MVP_NOWRITE        = 16
    MVP_FILETRUNCATE   = 17
    MVP_MREMAPFAIL     = 18
    MVP_TYPEMISMATCH   = 19
    MVP_KNEARESTCAP    = 20
    MVP_EMPTYTREE      = 21
    MVP_NOSPLITS       = 22
    MVP_BADDISTVAL     = 23
    MVP_FILENOTFOUND   = 24
    MVP_UNRECOGNIZED   = 25


@contextmanager
def mvp_errors():
    """
    Convert MVPError values to Python exceptions.

    This context manager returns a pointer to MVPError. When the context is
    exited the value is evaluated and a exception is raised if the value
    is not MVP_SUCCESS.

    """
    try:
        c_error = mvp.ffi.new("MVPError *")
        yield c_error
    finally:
        error = MVPError(c_error[0])

        if error == MVPError.MVP_SUCCESS:
            pass
        else:
            description = mvp.ffi.string(
                mvp.lib.mvp_errstr(c_error[0])).decode('ascii')

            if error in (MVPError.MVP_FILEOPEN,
                         MVPError.MVP_FILECLOSE,
                         MVPError.MVP_FILENOTFOUND):
                raise IOError(error, description)
            elif error == MVPError.MVP_EMPTYTREE:
                raise ValueError(error, description)
            else:
                raise RuntimeError(error, description)


class Point:
    """
    Represents a data point.

    :param point_id: Any hashable and pickelizable object.

    :param data: `bytes`, will be used as measurement data for the inner
                 hamming distance function. Usually your hash value.

    :param c_obj: You can instantiate this object using an `MVPDP`
                  object of `_c_mvptree` directly. Can't be used in
                  conjunction with `point_id` and/or `data`.

    """
    def __init__(self, point_id=None, data=None, c_obj=None,
                 owned_memory=True, tree=None):

        # `point_id` and `data` cache.
        self._point_id = None
        self._data = None

        #: If `True` cffi will free the owned memory.
        self.owned_memory = owned_memory

        #: Tree owning this point.
        self.tree = tree

        # Instantiate with `point_id` and `data`
        if point_id is not None and data is not None:

            # `point_id` must be hashable
            try:
                hash(point_id)
            except TypeError as exc:
                raise TypeError("`point_id` must be hashable.")

            # Serialize `point_id`
            try:
                serialized_id = base64.b64encode(pickle.dumps(point_id))
            except pickle.PicklingError as exc:
                raise TypeError("`point_id` must be picklable.") from exc

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
        if self._point_id is None:
            point_id_char_p = self._c_obj[0].id
            point_id_raw = mvp.ffi.string(point_id_char_p)
            self._point_id = pickle.loads(base64.b64decode(point_id_raw))
        return self._point_id

    @property
    def data(self):
        if self._data is None:
            datalen = self._c_obj[0].datalen
            data_void_p = self._c_obj[0].data
            self._data = mvp.ffi.buffer(data_void_p, datalen)[:]
        return self._data

    def __hash__(self):
        return hash((self.point_id, self.data))

    def __eq__(self, other):
        return self.point_id == other.point_id and self.data == other.data

    def __repr__(self):
        return "Point(%r, %r)" % (self.point_id, self.data)


class Tree:
    """
    Wrapper around MVPTree.

    """
    def __init__(self,
                 branchfactor=MVP_BRANCHFACTOR,
                 pathlength=MVP_PATHLENGTH,
                 leafcap=MVP_LEAFCAP,
                 c_obj=None):

        if c_obj is None:
            _c_obj = mvp.lib.mktree(branchfactor, pathlength, leafcap)
        else:
            try:
                if mvp.ffi.typeof(c_obj) is not mvp.ffi.typeof('MVPTree *'):
                    raise TypeError("`c_obj` must be a MVPTree pointer.")
            except Exception as exc:
                raise TypeError("Invalid initialization value.") from exc
            else:
                _c_obj = c_obj

        self._c_obj = mvp.ffi.gc(_c_obj, mvp.lib.rmtree)
        self.branchfactor = _c_obj[0].branchfactor
        self.pathlength = _c_obj[0].pathlength
        self.leafcap = _c_obj[0].leafcap

    @classmethod
    def from_file(cls, filename):
        """Loads the tree from disk."""
        with mvp_errors() as error:
            return cls(c_obj=mvp.lib.load(os.fsencode(filename), error))

    def to_file(self, filename):
        """Writes the tree to disk."""
        with mvp_errors() as error:
            mvp.lib.save(os.fsencode(filename), self._c_obj, error)

    def add(self, point):
        """
        Add a point or a list of points to the tree.

        Only new points will be added to the tree.

        """
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
        """
        Retrieve and return the point from the tree if exists.

        """
        for found in self.filter(point.data, 0):
            if found == point:
                return point
        raise ValueError("Point not found")

    def exists(self, point):
        """
        Returns `True` if the point exists in the tree.

        """
        try:
            self.get(point)
        except ValueError:
            return False
        else:
            return True

    def filter(self, data, radius, limit=65535):
        """
        Retrieve `limit` points from the tree at distance less or equal
        to `threshold` from `data`.

        This is a generator.

        """
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

        except ValueError:  # EmptyTree
            pass
        else:
            for i in range(nbresults[0]):
                yield Point(c_obj=res[i], owned_memory=False, tree=self)
        finally:
            if res is not mvp.ffi.NULL:  # pragma: no branch
                mvp.lib.free(res)


__all__ = ['Point', 'Tree']
