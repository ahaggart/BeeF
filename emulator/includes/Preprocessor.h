#ifndef PREPROCESSOR_H
#define PREPROCESSOR_H

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

#include "BVMStack.h"
#include "BeeFVirtualMachine.h"
#include "Common.h"

#define PP_DIR_CONSOLE_OUT      0

#define SRC_LEN_T   long
#define PP_DELIM    '#'   

#define PP_INFO_T   Preprocessor_Info
#define PP_DEBUG_T  Debug_Data
#define PPD_TYPE_T  int
#define PPD_DATA_PTR_T  void*

#define BF_INSN_T          char
#define BF_INSN_PTR_T      BF_INSN_T*

#define PPD_REF_INVALID -1
#define PP_NO_BRANCH    -1

#define PPD_RETURN_T    int

#define PP_MK_DEBUG_BUF(sz) (PP_DEBUG_T**)malloc(sz*sizeof(PP_DEBUG_T*))

typedef struct {
    PPD_TYPE_T type;
    PPD_DATA_PTR_T data;
    PPD_RETURN_T(*execute)(SRC_LEN_T,PPD_DATA_PTR_T);
} Debug_Data;

typedef struct {
    SRC_LEN_T i_count;
    SRC_LEN_T d_count;

    BF_INSN_PTR_T i_cache;
    SRC_LEN_T* br_cache;
    SRC_LEN_T* d_cache; //double-wide, stores debug info ref and line number
    PP_DEBUG_T** debug_data;

    SRC_LEN_T line_count;
} Preprocessor_Info;

PP_INFO_T* ppreprocessor(FILE* src);
void pp_dump_info(PP_INFO_T* info);

#endif //PREPROCESSOR_H