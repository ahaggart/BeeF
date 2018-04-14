#include "Directives.h"

PPD_RETURN_T ppd_print_to_console(SRC_LEN_T line,PPD_DATA_PTR_T data, BVM* bvm){
    printf("Line %ld: %s",line,data);
    return PPD_SUCCESS;
}

void ppd_make_console_out(PP_DEBUG_T* dest,char* dir){
    size_t len = (strlen(dir)+1)*sizeof(char); //include newline
    void* msg = malloc(len);
    dest->data = strcpy(msg,dir);
    dest->execute = &ppd_print_to_console;
}

PPD_RETURN_T ppd_print_data_head(SRC_LEN_T line,PPD_DATA_PTR_T data, BVM* bvm){
    printf("Line %ld: Data head @ %u\n",line,bvm->data_head);
    return PPD_SUCCESS;
}

void ppd_make_print_data_head(PP_DEBUG_T* dest){
    dest->execute = &ppd_print_data_head;
}

PPD_RETURN_T ppd_exit(SRC_LEN_T line,PPD_DATA_PTR_T data, BVM* bvm){
    ppd_print_to_console(line,data,bvm);
    return PPD_EXIT;
}

void ppd_make_exit(PP_DEBUG_T* dest,char* dir){
    size_t len = (strlen(dir)+1)*sizeof(char); //include newline
    void* msg = malloc(len);
    dest->data = strcpy(msg,dir);
    dest->execute = &ppd_exit;
}