#include "Directives.h"

void ppd_null_finalize(SRC_LEN_T line,PPD_DATA_PTR_T data, BVM* bvm){

}

char* ppd_pack_str(char* dir,size_t offset){
    size_t len = (strlen(dir)+offset+1)*sizeof(char); //include extra space
    void* msg = malloc(len);
    return strcpy(msg+offset,dir)-offset;
}

void ppd_pack_msg(PP_DEBUG_T* dest, char* dir,size_t offset){
    dest->data = ppd_pack_str(dir,offset);
}

char* ppd_extract_msg(char* dir){
    return ppd_pack_str(dir,0);
}

PPD_RETURN_T ppd_print_to_console(SRC_LEN_T line,PPD_DATA_PTR_T data, BVM* bvm){
    printf("Line %ld: %s",line,data);
    return PPD_SUCCESS;
}

void ppd_make_console_out(PP_DEBUG_T* dest,char* dir){
    ppd_pack_msg(dest,dir,0);
    dest->execute = &ppd_print_to_console;
    dest->finalize = &ppd_null_finalize;
}

PPD_RETURN_T ppd_print_data_head(SRC_LEN_T line,PPD_DATA_PTR_T data, BVM* bvm){
    printf("Line %ld: Data head @ %u\n",line,bvm->data_head);
    return PPD_SUCCESS;
}

void ppd_make_print_data_head(PP_DEBUG_T* dest){
    dest->execute = &ppd_print_data_head;
    dest->finalize = &ppd_null_finalize;
}

void ppd_value_assertion_violation(SRC_LEN_T line,PPD_DATA_PTR_T data, BVM* bvm){
    VAD* adata = (VAD*)data;
    int index = adata->index;
    const char* message = adata->msg;
    ASSERT* assertion = bvm->assertions[index];
    CELL expected = assertion->value;
    CELL actual   = bvm->cells[assertion->address];

    printf(PPD_ERRSTR(  
        "Assertion Violation (id=%d) @ Cell %u: Expected %u, got %u\n"
        ">> Assertion: %s"
        ">> Asserted on step %u (pc=%u), Violated on step %u (pc=%u)"),
        index, assertion->address, expected, actual,
        message,
        assertion->locked,assertion->pc,bvm->steps,bvm->pc);
}

PPD_RETURN_T ppd_toggle_value_assertion(SRC_LEN_T line,PPD_DATA_PTR_T data, BVM* bvm){
    VAD* adata = (VAD*)data;
    int index = adata->index;
    ASSERT* assertion = bvm->assertions[index];

    if(!assertion){
        CELL_IDX offset = adata->offset;
        bvm->assertions[index] = (ASSERT*)malloc(sizeof(ASSERT));
        assertion = bvm->assertions[index];
        assertion->locked = 0;
        assertion->value = 0;
        assertion->offset = offset;
        assertion->pc = 0;
    }

    if(assertion->locked){
        BVM_DEBUG("unasserting %d @ %u\n",index,assertion->address);
        if(bvm->cells[assertion->address] != assertion->value){
            return PPD_EXIT;
        }
        assertion->locked = 0;
        bvm->meta[assertion->address]->assert_ptr = 0;
    } else {
        assertion->locked = bvm->steps;
        assertion->pc = bvm->pc;
        assertion->address = bvm->data_head + assertion->offset;
        if(assertion->address >= bvm->num_cells){
            bvm_resize(bvm,assertion->address*2);
        }
        assertion->value = bvm->cells[assertion->address];
        BVM_DEBUG("asserting %d @ %u to %u\n",index,assertion->address,assertion->value);
        BVM_META* meta = bvm_get_metadata(bvm,assertion->address);
        meta->assert_ptr = data;
    }
    return PPD_SUCCESS;
}

size_t parse_value_assertion_offset(char* dir,CELL_IDX* offset){
    char** argv;
    int argc;
    size_t msg_start = ppd_parse_directive_args(dir,&argc,&argv);

    if(!argc){
        *offset = 0;
        return msg_start;
    }
    long offset_value =  atol(argv[0]);
    if(offset_value < 0){
        printf("Error: Invalid assertion offset %ld\n",offset_value);
        exit(1);
    }
    // printf("Adding assertion at offset %ld\n",offset_value);
    *offset = offset_value;

    return msg_start;
}

void ppd_make_cell_assertion(PP_DEBUG_T* dest,char* dir,int index){
    CELL_IDX offset;
    dir += parse_value_assertion_offset(dir,&offset);
    char* msg = ppd_extract_msg(dir);
    VAD* data = (VAD*)malloc(sizeof(VAD));
    data->msg = msg;
    data->index = index;
    data->offset = offset;
    data->d_ptr = dest;

    dest->data = data;
    dest->execute  = &ppd_toggle_value_assertion;
    dest->finalize = &ppd_value_assertion_violation;
}

void ppd_make_position_assertion(PP_DEBUG_T* dest,char* dir,int index){
    ppd_pack_msg(dest,dir,sizeof(int));
    *((int*)dest->data) = index;
    dest->execute  = 0;
    dest->finalize = 0;
}

PPD_RETURN_T ppd_exit(SRC_LEN_T line,PPD_DATA_PTR_T data, BVM* bvm){
    ppd_print_to_console(line,data,bvm);
    return PPD_EXIT;
}

void ppd_make_exit(PP_DEBUG_T* dest,char* dir){
    ppd_pack_msg(dest,dir,0);
    dest->execute = &ppd_exit;
    dest->finalize = &ppd_null_finalize;
}

size_t ppd_parse_directive_args(char* dir,int* argc_ptr,char*** argv_ptr){
    size_t len = strlen(dir);
    char* arg_values[MAX_ARGS];
    char arg[len]; //buffer
    size_t text_start;
    int arg_count = 0;
    size_t i = 0;
    size_t arg_i;
    while(i<len && arg_count < MAX_ARGS){
        text_start = i;
        for(arg_i=0;i<len && dir[i]!=PP_DELIM;i++,arg_i++){
            arg[arg_i] = dir[i];
        }
        if(i==len){
            break;
        }
        arg_values[arg_count] = (char*)malloc(arg_i*sizeof(char)+1);
        arg_values[arg_count][arg_i] = 0; //null terminate
        memcpy(arg_values[arg_count],arg,arg_i);

        // printf("argv[%d] = %s @ %p\n",arg_count,arg_values[arg_count],arg_values[arg_count]);

        arg_count++;
        i++; //skip the delimiter
    }
    
    char** argv = 0;
    if(arg_count){
        argv = (char**)malloc(sizeof(char*)*arg_count);
        memcpy(argv,arg_values,arg_count*sizeof(char*));
    } 
    *argc_ptr = arg_count;
    *argv_ptr = argv;

    return text_start;
}