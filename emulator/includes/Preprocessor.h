#ifndef PREPROCESSOR_H
#define PREPROCESSOR_H

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "BVMStack.h"

#define PP_DIR_CONSOLE_OUT      0

#define SRC_LEN_T   long
#define PP_DELIM    '#'    

#define PP_INFO_T   Preprocessor_Info
#define PP_DEBUG_T  Debug_Data

#define PP_MK_DEBUG_BUF(sz) (PP_DEBUG_T*)malloc(sz*sizeof(PP_DEBUG_T))

typedef struct {
    int ID;
    void* data;
} Debug_Data;

typedef struct {
    SRC_LEN_T i_count;
    int d_count;

    char* i_cache;
    SRC_LEN_T* br_cache;
    PP_DEBUG_T* debug_cache;
    PP_DEBUG_T* debug_data;
} Preprocessor_Info;

PP_INFO_T* ppreprocessor(FILE* src);

#endif //PREPROCESSOR_H