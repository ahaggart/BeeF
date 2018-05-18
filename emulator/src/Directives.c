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

int get_assertion_index(PPD_DATA_PTR_T data,BVM* bvm){
    return *((int*)data);
}

CELL_IDX get_assertion_offset(PPD_DATA_PTR_T data,BVM* bvm){
    return *((CELL_IDX*)(data+sizeof(int)));
}

char* get_assertion_msg(PPD_DATA_PTR_T data){
    return (char*)(data + sizeof(int) + sizeof(CELL_IDX));
}

void ppd_assertion_violation(SRC_LEN_T line,PPD_DATA_PTR_T data, BVM* bvm){
    int index = get_assertion_index(data,bvm);
    const char* message = get_assertion_msg(data);
    ASSERT* assertion = bvm->assertions[index];
    CELL expected = assertion->value;
    CELL actual   = bvm->cells[assertion->address];

    printf(PPD_ERRSTR( "Assertion Violation (id=%d) @ %u: Expected %u, got %u\n"
                       ">> Assertion: %s"),
                index,
                assertion->address,
                expected,
                actual,
                message);
}

PPD_RETURN_T ppd_toggle_assertion(SRC_LEN_T line,PPD_DATA_PTR_T data, BVM* bvm){
    int index = get_assertion_index(data,bvm);
    ASSERT* assertion = bvm->assertions[index];

    if(!(bvm->assertions[index])){
        CELL_IDX offset = get_assertion_offset(data,bvm);
        bvm->assertions[index] = (ASSERT*)malloc(sizeof(ASSERT));
        assertion = bvm->assertions[index];
        assertion->locked = 0;
        assertion->value = 0;
        assertion->offset = offset;
    }

    if(assertion->locked){
        BVM_DEBUG("unasserting %d @ %u\n",index,assertion->address);
        if(bvm->cells[assertion->address] != assertion->value){
            return PPD_EXIT;
        }
        assertion->locked = 0;
        bvm->meta[assertion->address]->assert_index = 0;
    } else {
        assertion->locked = 1;
        assertion->address = bvm->data_head + assertion->offset;
        if(assertion->address >= bvm->num_cells){
            bvm_resize(bvm,assertion->address*2);
        }
        assertion->value = bvm->cells[assertion->address];
        BVM_DEBUG("asserting %d @ %u to %u\n",index,assertion->address,assertion->value);
        BVM_META* meta = bvm->meta[assertion->address];
        if(!meta){
            meta = (BVM_META*)calloc(sizeof(BVM_META),1);
            bvm->meta[assertion->address] = meta;
        }
        meta->assert_index = index+1;
    }
    return PPD_SUCCESS;
}

void ppd_make_cell_assertion(PP_DEBUG_T* dest,char* dir,int index){
    CELL_IDX offset;
    dir += ppd_parse_directive_idx(dir,&offset);
    ppd_pack_msg(dest,dir,sizeof(int) + sizeof(CELL_IDX));
    *((int*)dest->data) = index;
    *((CELL_IDX*)(dest->data+sizeof(int))) = offset;
    dest->execute  = &ppd_toggle_assertion;
    dest->finalize = &ppd_assertion_violation;
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

size_t ppd_parse_directive_idx(char* dir,CELL_IDX* dest){
    size_t len = strlen(dir);
    char tmp[len];
    int i;
    for(i=0;i<len && dir[i]!=PP_DELIM;i++){
        tmp[i] = dir[i];
    }
    if(i==len){
        printf("Error: Malformed directive: Unable to parse index from: %s\n",dir);
        exit(1);
    }
    tmp[i] = 0;
    long offset =  atol(tmp);
    if(offset < 0){
        printf("Error: Invalid assertion offset %ld\n",offset);
        exit(1);
    }
    printf("Adding assertion at offset %ld\n",offset);
    *dest = offset;
    return i+1;
}