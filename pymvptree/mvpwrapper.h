const char* mvp_errstr(MVPError err);

unsigned char count_set_bits(unsigned char n);
float bitlevenshtein(MVPDP *pointA, MVPDP *pointB);

MVPDP *mkpoint(char *id, char *data, unsigned int datalen);
void rmpoint(MVPDP *point);

MVPTree *mktree(void);
void rmtree(MVPTree *tree);

void printpoint(MVPDP* point);
void printtree(MVPTree *tree);

MVPTree *load(char *filename, MVPError *err);
void save(char *filename, MVPTree *tree, MVPError *err);
