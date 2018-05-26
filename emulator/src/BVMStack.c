

#include "BVMStack.h"

void bvms_print_elem_hex(BVMS* stack,BVMS_PTR_T idx){
    BVMS_PTR_T j;
    for(j = 0; j < stack->width; j++){
        printf("\\0x%x ",*((char*)(stack->stack+idx*stack->width+j)));
    }
    printf("\n");
}

BVMS* bvms_create_stack(BVMS_PTR_T initial_size,BVMS_WIDTH_T width){
    BVMS* stack = (BVMS*)malloc(sizeof(BVMS));
    *stack = (BVMS){
        .max = 0,
        .size = initial_size,
        .width = width,
        .stack=(BVMS_DATA_PTR_T)malloc(initial_size*width*sizeof(BVMS_DATA_T)),
    };
    return stack;
}

int bvms_push(BVMS* stack,BVMS_DATA_PTR_T source){
    if(stack->top == stack->size){
        BVMS_DATA_PTR_T newStack = 
            (BVMS_DATA_PTR_T)malloc(stack->size*2*stack->width*sizeof(BVMS_DATA_T));
        memcpy(newStack,stack->stack,stack->size*stack->width*sizeof(BVMS_DATA_T));
        stack->size *= 2;
        free(stack->stack);
        stack->stack = newStack;
    }
    memcpy(stack->stack + stack->top * stack->width,source,stack->width);
    // bvms_print_elem_hex(stack,stack->top);
    stack->top++;
    if(stack->top > stack->max){
        stack->max = stack->top;
    }
    return 0;
}

//return a pointer to the popped element
BVMS_DATA_PTR_T bvms_pop(BVMS* stack){
    if(stack->top == 0){
        //error
        printf("Error: Popping empty stack.\n");
        return (BVMS_DATA_PTR_T)0;
    }
    stack->top--;
    return stack->stack + stack->top*stack->width;
}

void bvms_dump(BVMS* stack){
    printf("Dumping Stack...\n");
    char* fmt = FMT_INDENT"Size: %u\n"
                FMT_INDENT"Height: %u\n"
                FMT_INDENT"Max: %u\n"
                FMT_INDENT"Width: %d byte%s\n"
                FMT_INDENT"Data:\n";
    printf(fmt,
        stack->size,
        stack->top,
        stack->max,
        stack->width,(stack->width==1)?"":"s");
    BVMS_PTR_T i;
    for(i = 0; i < stack->top; i++){
        bvms_print_elem_hex(stack,i);
    }
    if(stack->top == 0){
        printf(FMT_INDENT " <EMPTY>\n");
    }
}

BVMS_PTR_T bvms_max(BVMS* stack){
    return stack->max;
}

int bvms_destroy(BVMS* stack){
    free(stack->stack);
    free(stack);
    return 0;
}