#ifndef PREPROCESSOR_H
#define PREPROCESSOR_H

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

#include "BVMStack.h"
#include "BeeFVirtualMachine.h"
#include "Directives.h"
#include "Common.h"

#define PP_INFO_T   Preprocessor_Info

#define BF_INSN_T          char
#define BF_INSN_PTR_T      BF_INSN_T*

#define PPD_REF_INVALID -1
#define PP_NO_BRANCH    -1

#define PP_MK_DEBUG_BUF(sz) (PP_DEBUG_T**)malloc(sz*sizeof(PP_DEBUG_T*))

typedef struct {
    SRC_LEN_T i_count;
    SRC_LEN_T d_count;

    BF_INSN_PTR_T i_cache;
    SRC_LEN_T* br_cache;
    SRC_LEN_T* d_cache; //double-wide, stores debug info ref and line number
    PP_DEBUG_T** debug_data;

    SRC_LEN_T line_count;

    int assertions;
} Preprocessor_Info;

PP_INFO_T* ppreprocessor(FILE* src);
void pp_dump_info(PP_INFO_T* info);

#endif //PREPROCESSOR_H