#ifndef GSTACK_H
#define GSTACK_H

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#define GSTACK_PTR_T unsigned int
#define GSTACK_DATA_T    char
#define GSTACK_DATA_PTR_T GSTACK_DATA_T*
#define GSTACK_WIDTH_T  int

typedef struct{
    GSTACK_PTR_T top;   //top element index
    GSTACK_PTR_T size;  //in elements
    GSTACK_WIDTH_T width; //in bytes
    GSTACK_DATA_PTR_T stack;
} GStack;

GStack* gcreate_stack(GSTACK_PTR_T initial_size,GSTACK_WIDTH_T width);
int gspush(GStack* stack,GSTACK_DATA_PTR_T source);
GSTACK_DATA_PTR_T gspop(GStack* stack);
void gsdump(GStack* stack);

#endif //GSTACK_H