#ifndef DIRECTIVES_H
#define DIRECTIVES_H

#include <stdio.h>
#include <string.h>

#include "BeeFVirtualMachine.h"
#include "Common.h"

#define PP_DELIM    '#'   

#define PP_DIR_EXIT            -1
#define PP_DIR_CONSOLE_OUT      0
#define PP_DIR_PRINT_DATA_HEAD  1

#define PPD_RETURN_T    int
#define PPD_SUCCESS             0
#define PPD_EXIT                1

#define PPD_TYPE_T  int
#define PPD_DATA_PTR_T  void*

#define PP_DEBUG_T  Debug_Data

typedef struct {
    PPD_TYPE_T type;
    PPD_DATA_PTR_T data;
    PPD_RETURN_T(*execute)(SRC_LEN_T,PPD_DATA_PTR_T, BVM*);
} Debug_Data;

void ppd_make_console_out(PP_DEBUG_T* dest,char* dir);
void ppd_make_print_data_head(PP_DEBUG_T* dest);
void ppd_make_exit(PP_DEBUG_T* dest,char* dir);

#endif