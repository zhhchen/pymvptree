#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "mvptree.h"

#define MVP_BRANCHFACTOR 2
#define MVP_PATHLENGTH   5
#define MVP_LEAFCAP     15


unsigned char count_set_bits(unsigned char n){
    unsigned char count = 0; // count accumulates the total bits set 
    for (count = 0; n != 0; count++)
    {
        n &= n - 1; // this clears the LSB-most set bit
    }
    return count;
}


float bitlevenshtein(MVPDP *pointA, MVPDP *pointB){
    float count = 0, c;
    unsigned int i;
    char a, b;

    // Extracted from mvptree examples.
    if (!pointA || !pointB) return -1.0f;

    unsigned int maxlen = pointA->datalen > pointB->datalen ? pointA->datalen : pointB->datalen;

    for (i=0; i<maxlen; i++) {
        if ((int)pointA->datalen > i) {
            a = ((char *)pointA->data)[i];
        } else {
            count += 8;
            continue;
        }

        if ((int)pointB->datalen > i) {
            b = ((char *)pointB->data)[i];
        } else {
            count += 8;
            continue;
        }

        c = count_set_bits(a ^ b);
        count += c;
    }
    
    return count;
}


void rmpoint(MVPDP *point) {
    dp_free(point, (MVPFreeFunc *)free);
}


MVPDP *mkpoint(char *id, char *data, unsigned int datalen) {
    MVPDP *newpnt = dp_alloc(MVP_BYTEARRAY);

    if (newpnt == NULL) return NULL;

    newpnt->datalen = datalen;

    newpnt->data = (void *) malloc(sizeof(char)*datalen);
    if (newpnt->data == NULL) {
        free(newpnt);
        return NULL;
    }

    memcpy(newpnt->data, data, sizeof(char)*datalen);

    newpnt->id = strdup(id);

    if (newpnt->id == NULL){
        free(newpnt);
        free(newpnt->data);
        return NULL;
    }

    /*
    int i;
    for (i = 0; i < datalen; i++)
    {
        printf("\\x%02x", (unsigned int)(((char *)newpnt->data)[i] & 0xFF));
    }
    printf("\n");

    */
    return newpnt;
}


void printpoint(MVPDP* point) {
    char data[point->datalen + 1];
    memcpy(data, point->data, point->datalen);
    data[point->datalen] = '\0';
    printf("%s -> %s\n", point->id, data);
}


MVPTree *mktree(void) {
    CmpFunc distance_func = bitlevenshtein;
    return mvptree_alloc(NULL, distance_func, MVP_BRANCHFACTOR, MVP_PATHLENGTH, MVP_LEAFCAP);
}


void rmtree(MVPTree *tree) {
    mvptree_clear(tree, (MVPFreeFunc *)free);
}


void printtree(MVPTree *tree) {
    mvptree_print(stdout, tree);
}


MVPTree *load(char *filename, MVPError *err) {
    MVPTree *tree;
    CmpFunc distance_func = bitlevenshtein;
    tree = mvptree_read(filename, distance_func,
                        MVP_BRANCHFACTOR, MVP_PATHLENGTH, MVP_LEAFCAP, err);
    return tree;
}


void save(char *filename, MVPTree *tree, MVPError *err) {
    *err = mvptree_write(tree, filename, 00755);
}
