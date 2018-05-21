#ifndef DIRECTIVES_H
#define DIRECTIVES_H

#include <stdio.h>
#include <string.h>

#include "BeeFVirtualMachine.h"
#include "Common.h"

#define PP_DELIM               '#'   

#define MAX_ARGS                8

#define PP_DIR_EXIT            -1
#define PP_DIR_CONSOLE_OUT      0
#define PP_DIR_PRINT_DATA_HEAD  1
#define PP_DIR_FULL_STACK_LOCK  2
#define PP_DIR_VALUE_ASSERT     3
#define PP_DIR_LOCK_TOGGLE      4

#define PPD_RETURN_T            int
#define PPD_SUCCESS             0
#define PPD_EXIT                1

#define PPD_TYPE_T              int
#define PPD_DATA_PTR_T          void*

#define PP_DEBUG_T  Debug_Data
#define PP_FSL_T    Full_Stack_Lock

#define PPD_ERRSTR(msg) "Error: Line %ld: " msg "\n",line

typedef struct {
    PPD_TYPE_T type;
    PPD_DATA_PTR_T data;
    PPD_RETURN_T(*execute)(SRC_LEN_T,PPD_DATA_PTR_T, BVM*);
    void(*finalize)(SRC_LEN_T,PPD_DATA_PTR_T, BVM*);
} Debug_Data;

#define VAD ValueAssertionData

typedef struct {
    int index;
    CELL_IDX offset;
    char* msg;
    PP_DEBUG_T* d_ptr;
} ValueAssertionData;

#define PAD PositionAssertionData

typedef struct {
    int index;
    char* msg;
    PP_DEBUG_T* d_ptr;
} PositionAssertionData;

void ppd_make_console_out(PP_DEBUG_T* dest,char* dir);
void ppd_make_print_data_head(PP_DEBUG_T* dest);
void ppd_make_exit(PP_DEBUG_T* dest,char* dir);
void ppd_make_dump_stack(PP_DEBUG_T* dest,char* dir);
void ppd_make_full_stack_lock(PP_DEBUG_T* dest,char* dir);
void ppd_make_cell_assertion(PP_DEBUG_T* dest,char* dir,int index);
void ppd_make_position_assertion(PP_DEBUG_T* dest,char* dir,int index);
void ppd_error(SRC_LEN_T line,const char* msg);

size_t ppd_parse_directive_args(char* dir,int* argc_ptr,char*** argv_ptr);

#endif