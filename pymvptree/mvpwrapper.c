#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "mvptree.h"

#define MVP_BRANCHFACTOR 2
#define MVP_PATHLENGTH   5
#define MVP_LEAFCAP     25


unsigned char count_set_bits(unsigned char n){
    unsigned char count = 0; // count accumulates the total bits set 
    for (count = 0; n != 0; count++)
    {
        n &= n - 1; // this clears the LSB-most set bit
    }
    return count;
}


float hamming_distance(MVPDP *pointA, MVPDP *pointB){
    float count = 0;
    int i;
    char n;

    if (pointA == NULL || pointB == NULL) {
        printf("NULLLL!\n");
        return 0;
    }

    int maxlen = pointA->datalen > pointB->datalen ? pointA->datalen : pointB->datalen;

    for (i=0; i < maxlen; i++) {
        if ((int)pointA->datalen > i) {
            n = ((char *)pointA->data)[i];
        } else {
            n = 0;
        }

        if ((int)pointB->datalen > i) {
            n = n ^ ((char *)pointB->data)[i];
        } else {
            n = n ^ 0;
        }

        count += count_set_bits(n);
    }
    
    return count;
}


char *get_point_id(MVPDP *point) {
    return point->id;
}


unsigned int get_point_datalen(MVPDP *point) {
    return point->datalen;
}


char *get_point_data(MVPDP *point) {
    return point->data;
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


MVPTree *newtree(void) {
    CmpFunc distance_func = hamming_distance;
    return mvptree_alloc(NULL, distance_func, MVP_BRANCHFACTOR, MVP_PATHLENGTH, MVP_LEAFCAP);
}


void addpoint(MVPTree *tree, MVPDP *point) {
    MVPError err;
    MVPDP **pointlist = (MVPDP**)malloc(sizeof(MVPDP*));
    pointlist[0] = point;
    err = mvptree_add(tree, pointlist, 1);
    if (err != MVP_SUCCESS){
	fprintf(stdout,"Unable to add to tree - %s\n", mvp_errstr(err));
    }
}


void printtree(MVPTree *tree) {
    mvptree_print(stdout, tree);
}


MVPTree *load(char *filename) {
    MVPError err;
    MVPTree *tree;
    CmpFunc distance_func = hamming_distance;
    tree = mvptree_read(filename, distance_func,
                        MVP_BRANCHFACTOR, MVP_PATHLENGTH, MVP_LEAFCAP, &err);
    if (err != MVP_SUCCESS) {
        printf("ERROR(%d): %s\n", err, mvp_errstr(err));
        return NULL;
    } else {
        return tree;
    }
}


void save(char *filename, MVPTree *tree) {
    MVPError err;
    err = mvptree_write(tree, filename, 00755);
    if (err != MVP_SUCCESS) {
        printf("ERROR(%d): %s\n", err, mvp_errstr(err));
    }
}
