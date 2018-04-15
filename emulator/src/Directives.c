#include "Directives.h"

char* ppd_pack_str(char* dir){
    size_t len = (strlen(dir)+1)*sizeof(char); //include newline
    void* msg = malloc(len);
    return strcpy(msg,dir);
}

void ppd_pack_msg(PP_DEBUG_T* dest, char* dir){
    dest->data = ppd_pack_str(dir);
}

PPD_RETURN_T ppd_print_to_console(SRC_LEN_T line,PPD_DATA_PTR_T data, BVM* bvm){
    printf("Line %ld: %s",line,data);
    return PPD_SUCCESS;
}

void ppd_make_console_out(PP_DEBUG_T* dest,char* dir){
    ppd_pack_msg(dest,dir);
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
    ppd_pack_msg(dest,dir);
    dest->execute = &ppd_exit;
}

// void ppd_make_full_stack_lock(PP_DEBUG_T* dest,char* dir){
//     //create a full stack lock
//     PP_FSL_T* lock = (PP_FSL_T*)malloc(sizeof(PP_FSL_T));
//     dest->data = malloc(2*sizeof(void*));//hold two pointers
//     //pointer and typing fuckery
//     *((PP_FSL_T**)(dest->data + PPD_FSL_LOCK)) = lock;
//     *((char**)(dest->data + PPD_FSL_MSG)) = ppd_pack_str(dir);

//     // printf("lock: %p, msg: %s",lock,*((char**)(dest->data + PPD_FSL_MSG)));
// }

// void ppd_make_full_stack_unlock(PP_DEBUG_T* dest,char* dir){

// }