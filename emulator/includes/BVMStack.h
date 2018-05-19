#ifndef BVMS_H
#define BVMS_H

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#include "Common.h"

#define BVMS_PTR_T unsigned int
#define BVMS_DATA_T    char
#define BVMS_DATA_PTR_T BVMS_DATA_T*
#define BVMS_WIDTH_T  int

#define BVMS BVMStack

typedef struct{
    BVMS_PTR_T top;   //top element index
    BVMS_PTR_T size;  //in elements
    BVMS_WIDTH_T width; //in bytes
    BVMS_DATA_PTR_T stack;
} BVMStack;

BVMS* bvms_create_stack(BVMS_PTR_T initial_size,BVMS_WIDTH_T width);
int bvms_push(BVMS* stack,BVMS_DATA_PTR_T source);
BVMS_DATA_PTR_T bvms_pop(BVMS* stack);
void bvms_dump(BVMS* stack);
int bvms_destroy(BVMS* stack);

#endif //BVMS_H