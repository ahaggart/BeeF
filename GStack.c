

#include "GStack.h"

void gsprint_elem_hex(GStack* stack,GSTACK_PTR_T idx){
    GSTACK_PTR_T j;
    for(j = 0; j < stack->width; j++){
        printf("\\0x%x ",*((char*)(stack->stack+idx*stack->width+j)));
    }
    printf("\n");
}

GStack* gcreate_stack(GSTACK_PTR_T initial_size,GSTACK_WIDTH_T width){
    GStack* stack = (GStack*)malloc(sizeof(GStack));
    *stack = (GStack){
        .size = initial_size,
        .width = width,
        .stack=(GSTACK_DATA_PTR_T)malloc(initial_size*width*sizeof(GSTACK_DATA_T)),
    };
    return stack;
}

int gspush(GStack* stack,GSTACK_DATA_PTR_T source){
    if(stack->top == stack->size){
        GSTACK_DATA_PTR_T newStack = 
            (GSTACK_DATA_PTR_T)malloc(stack->size*2*stack->width*sizeof(GSTACK_DATA_T));
        memcpy(newStack,stack->stack,stack->size*stack->width*sizeof(GSTACK_DATA_T));
        stack->size *= 2;
        free(stack->stack);
        stack->stack = newStack;
    }
    memcpy(stack->stack + stack->top * stack->width,source,stack->width);
    // gsprint_elem_hex(stack,stack->top);
    stack->top++;
    return 0;
}

//return a pointer to the popped element
GSTACK_DATA_PTR_T gspop(GStack* stack){
    if(stack->top == 0){
        //error
        printf("Error: Popping empty stack.\n");
        return (GSTACK_DATA_PTR_T)0;
    }
    stack->top--;
    return stack->stack + stack->top*stack->width;
}

void gsdump(GStack* stack){
    printf("Dumping Stack...\n");
    char* fmt = "Size: %u\nHeight: %u\nWidth: %d byte%s\nData:\n";
    printf(fmt,stack->size,stack->top,stack->width,(stack->width==1)?"":"s");
    GSTACK_PTR_T i;
    for(i = 0; i < stack->top; i++){
        gsprint_elem_hex(stack,i);
    }
    if(stack->top == 0){
        printf(" <EMPTY>\n");
    }
}