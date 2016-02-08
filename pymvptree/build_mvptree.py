import os
from cffi import FFI
from glob import glob

HERE = os.path.realpath(os.path.dirname(__file__))

ffi = FFI()

ffi.set_source("_mvptree",
    """
    #include "mvptree.h"
    #include "mvpwrapper.h"
    
    """,
    libraries=["m"],
    include_dirs=[HERE],
    sources=glob(os.path.basename(HERE) + '*.c'),
    # extra_compile_args=["-g"],
)

ffi.cdef("""

typedef ... MVPDP;
typedef ... MVPTree;

/* error codes */
typedef enum mvp_error_t {
    MVP_SUCCESS,            /* no error */
    MVP_ARGERR,             /* argument error */
    MVP_NODISTANCEFUNC,     /* no distance function found */
    MVP_MEMALLOC,           /* mem alloc error */
    MVP_NOLEAF,             /* could not alloc leaf node */
    MVP_NOINTERNAL,         /* could not alloc internal node */
    MVP_PATHALLOC,          /* path alloc error */
    MVP_VPNOSELECT,         /* could not select vantage points */
    MVP_NOSV1RANGE,         /* could not calculate range of points from sv1 */
    MVP_NOSV2RANGE,         /* could not calculate range of points from sv2 */
    MVP_NOSPACE,            /* points too close to one another, too compact */
    MVP_NOSORT,             /* unable to sort points */
    MVP_FILEOPEN,           /* trouble opening file */
    MVP_FILECLOSE,          /* trouble closing file */
    MVP_MEMMAP,             /* mem map trouble */
    MVP_MUNMAP,             /* mem unmap trouble */
    MVP_NOWRITE,            /* could not write to file */
    MVP_FILETRUNCATE,       /* could not extend file */
    MVP_MREMAPFAIL,         /* unable to map/unmap file */
    MVP_TYPEMISMATCH,       /* trying to add datapoints of one datatype */
                            /* to tree that already contains another type */
    MVP_KNEARESTCAP,        /* number results found reaches knearest limit */
    MVP_EMPTYTREE,
    MVP_NOSPLITS,           /* unable to calculate split points */
    MVP_BADDISTVAL,         /* val from distance function either NaN or less than 0 */
    MVP_FILENOTFOUND,       /* file not found */
    MVP_UNRECOGNIZED,       /* unrecognized node */
} MVPError;


MVPDP *mkpoint(char *id, char *data, unsigned int datalen);
void printpoint(MVPDP* point);
float hamming_distance(MVPDP* pointA, MVPDP* pointB);
char *get_point_id(MVPDP *point);
unsigned int get_point_datalen(MVPDP *point);
char *get_point_data(MVPDP *point);
MVPTree *newtree(void);
void addpoint(MVPTree *tree, MVPDP *point);
void printtree(MVPTree *tree);
MVPTree *load(char *filename);
void save(char *filename, MVPTree *tree);
MVPDP** mvptree_retrieve(MVPTree *tree, MVPDP *target, unsigned int knearest, float radius,unsigned int *nbresults, MVPError *error);
const char* mvp_errstr(MVPError err);

""")

if __name__ == '__main__':
    ffi.compile()
