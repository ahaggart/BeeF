#ifndef BVMLOCK_H
#define BVMLOCK_H
/**
 *  Lock and Lock Management Code 
 * 
 */

#define PPD_FSL_LOCK        0
#define PPD_FSL_MSG         1

typedef struct {
    CELL_IDX height;
    CELL* data;
} Full_Stack_Lock;

#endif //BVMLOCK_H