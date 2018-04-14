#include "Preprocessor.h"
#include "BeeFVirtualMachine.h"

void* ppd_make_console_out(char* dir){
    size_t len = (strlen(dir)+1)*sizeof(char); //include newline
    void* msg = malloc(len);
    return strcpy(msg,dir);
}

int pp_make_debug_data(PP_DEBUG_T* dest, char* dir){
    //parse the directive
    if(dir[0] != PP_DELIM){//what are ya doin man
        return 1;
    }
    int idx = 0;
    while(dir[++idx] != PP_DELIM); //seek next delimiter
    dir[idx] = 0; //null terminate the ID
    dest->ID = atoi(dir+1);

    //type-specific parsing
    switch(dest->ID){
        case PP_DIR_CONSOLE_OUT: //print to console 
        default: //default to printing directive if we dont recognize it
            dest->data = ppd_make_console_out(dir+idx+1);
            printf("dir: %s",dest->data);
            break;
    }

    return 0;
}

SRC_LEN_T pp_get_debug_info(FILE* src, PP_INFO_T* info){
    const int READ_BUFFER_SIZE = 256; //these dont need to be exposed
    const int DEBUG_DATA_SIZE  = 16;  //where to put

    char read_buffer[READ_BUFFER_SIZE];
    info->d_count = 0;
    int debug_array_size = DEBUG_DATA_SIZE;
    info->debug_data = PP_MK_DEBUG_BUF(DEBUG_DATA_SIZE);

    while(1){
        if(!fgets(read_buffer,READ_BUFFER_SIZE,src)){
            break;
        }
        if(read_buffer[0] == PP_DELIM){
            info->d_count++;
            if(info->d_count == debug_array_size){
                PP_DEBUG_T* tmp = PP_MK_DEBUG_BUF(debug_array_size*2);
                memcpy(tmp,info->debug_data,debug_array_size);
                free(info->debug_data);
                debug_array_size *= 2;
                info->debug_data = tmp;
            }
            pp_make_debug_data(info->debug_data+info->d_count,read_buffer);
        }
    }

    return ftell(src);
}




PP_INFO_T* ppreprocessor(FILE* src){
    PP_INFO_T* info = (PP_INFO_T*)malloc(sizeof(PP_INFO_T));

    SRC_LEN_T pos = 0;
    pos = pp_get_debug_info(src,info);
    
    return info;
}