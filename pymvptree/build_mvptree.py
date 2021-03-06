import os
from cffi import FFI
from glob import glob

HERE = os.path.realpath(os.path.dirname(__file__))
SOURCES = glob(os.path.join(os.path.basename(HERE), '*.c'))

ffi = FFI()

ffi.set_source("_c_mvptree",
    """
    #include "mvptree.h"
    #include "mvpwrapper.h"
    """,
    libraries=["m"],
    include_dirs=[HERE],
    sources=SOURCES,
    ## Enable debug, disable optimizations.
    # extra_compile_args=["-g", "-O0"],
)

ffi.cdef("""


typedef enum mvp_datatype_t { 
    MVP_BYTEARRAY = 1, 
    MVP_UINT16ARRAY = 2, 
    MVP_UINT32ARRAY = 4, 
    MVP_UINT64ARRAY = 8 
} MVPDataType;

typedef struct mvp_datapoint_t {
    char *id;               /* null-terminated id string */
    void *data;             /* data for this data point */
    float *path;            /* path of distances of data point from all vantage points down tree*/
    unsigned int datalen;   /* length of data in the type designated */    
    MVPDataType type;       /* type of data (the bitwidth of each data element) */
} MVPDP;

typedef enum nodetype_t { 
    INTERNAL_NODE = 1, 
    LEAF_NODE 
} NodeType;

typedef struct node_internal_t {
    NodeType type;
    MVPDP *sv1, *sv2;
    float *M1, *M2;
    void **child_nodes;
} InternalNode;

typedef struct node_leaf_t {
    NodeType type;
    MVPDP *sv1, *sv2;
    MVPDP **points;
    float *d1, *d2;
    unsigned int nbpoints;
} LeafNode;
   
typedef union node_t {
    LeafNode leaf;
    InternalNode internal;
} Node;

typedef float (*CmpFunc)(MVPDP *pointA, MVPDP *pointB);

typedef long off_t;

typedef struct mvptree_t {
    int branchfactor;
    int pathlength;
    int leafcap;
    int fd;
    int k;
    MVPDataType datatype;
    off_t pos;
    off_t size;
    off_t pgsize;
    char *buf;
    Node *node;
    CmpFunc dist;
} MVPTree;

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

const char* mvp_errstr(MVPError err);

unsigned char count_set_bits(unsigned char n);
float bitlevenshtein(MVPDP *pointA, MVPDP *pointB);

MVPDP *mkpoint(char *id, char *data, unsigned int datalen);
void rmpoint(MVPDP *point);

MVPTree *mktree(unsigned int bf, unsigned int p, unsigned int k);
void rmtree(MVPTree *tree);

void printpoint(MVPDP* point);
void printtree(MVPTree *tree);

MVPTree *load(char *filename, MVPError *err);
void save(char *filename, MVPTree *tree, MVPError *err);

MVPError mvptree_add(MVPTree *tree, MVPDP **points, unsigned int nbpoints);
MVPDP** mvptree_retrieve(MVPTree *tree, MVPDP *target, unsigned int knearest, float radius,unsigned int *nbresults, MVPError *error);

void free(void *ptr);

""")

if __name__ == '__main__':
    ffi.compile()
