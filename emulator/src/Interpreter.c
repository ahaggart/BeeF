/**
 *  Alexander Haggart, 4/11/18
 *
 *  BeeF interpreter implementation
 *
 *  supply instruction plaintext file as a command-line argument
 */

#include <stdio.h>
#include <time.h>

#include "BeeFVirtualMachine.h"
#include "BVMStack.h"
#include "Preprocessor.h"

void print_usage(){
  printf("usage: roast -[d] path_to_beef_assembly\n");
}

typedef struct{
  char* code;
  char* mem;
  char debug;
} arg_info;

void process_user_input(char input,int* autorun,BVM* vm){
  switch(input){
    case '\n':
      dump_bvm(vm);
      break;
    case 'q':
      *autorun = 1;
      break;
    case 'r': //run to next break point
      *autorun = 1;
    default:
      break;
  }
}

void parse_args(int argc,char** argv,arg_info* dest){
  int arg;
  int iflag = 1;
  char flag;
  dest->debug = 0;
  dest->code = 0;
  dest->mem = 0;
  for(arg = 1; arg < argc; arg++){
    if(argv[arg][0] == '-'){
      while((flag=argv[arg][iflag++])){
        switch(flag){
          case 'd':
            dest->debug = 1;
            break;
          default:
            break;
        }
      }
      iflag = 0;
    }
    else if(!dest->code){
      dest->code = argv[arg];
    }else if(!dest->mem){
      dest->mem = argv[arg];
    }
  }
}

int get_starting_mem(char* file,CELL** dest,int default_size){
  if(!file){
    *dest = 0;
    return default_size;
  }
  FILE* memsrc = fopen(file,"r");
  int i = 0;
  int ccount = 0;
  int readbuffer_size = 4;
  char readbuffer[readbuffer_size];
  int in_char;
  int total_size = default_size;
  CELL* mem = (CELL*)malloc(total_size*sizeof(CELL));
  int mem_size = 0;
  while((in_char = fgetc(memsrc))!=EOF){
    readbuffer[i] = (char)in_char;
    ccount++;
    if(readbuffer[i] == '\n'){
      continue;
    }else if(readbuffer[i] == ','){
      readbuffer[i] = 0;
      if(mem_size == total_size){
        CELL* tmp = (CELL*)malloc(total_size*2*sizeof(CELL));
        memcpy(tmp,mem,mem_size*sizeof(CELL));
        free(mem);
        mem = tmp;
        total_size *= 2;
      }
      mem[mem_size++] = (CELL)atoi(readbuffer);
      i = 0;
    } else{
      i++;
    }

    if(i == readbuffer_size){
      printf("Error: starting cell value at %d out of bounds.",ccount-1);
      exit(1);
    }
  }
  if(i != 0){ //TODO: this is duplicated from the loop body
    readbuffer[i] = 0;
    if(mem_size == total_size){
      CELL* tmp = (CELL*)malloc(total_size*2*sizeof(CELL));
      memcpy(tmp,mem,mem_size*sizeof(CELL));
      free(mem);
      mem = tmp;
      total_size *= 2;
    }
    mem[mem_size++] = (CELL)atoi(readbuffer);
  }
  *dest = mem;
  return mem_size;
}

int main(int argc, char** argv){
  if(argc < 2){
    print_usage();
    return 1;
  }
  arg_info args;
  parse_args(argc,argv,&args);
  int debugging = args.debug;
  int autorun = !debugging;
  CELL* cells;
  int memsize = get_starting_mem(args.mem,&cells,12);
  BVM* vm = create_bvm(memsize,cells); //big enough for the hello world program
  FILE* insns = fopen(args.code,"r");
  FILE* prog = insns;
  PP_INFO_T* info = ppreprocessor(prog);
  fclose(insns);
  pp_dump_info(info);

  printf("Starting Virtual Machine...\n* * * * *\n");
  unsigned int step_counter = 0;
  SRC_LEN_T dref;
  int status = 0;
  char insn;
  time_t start = clock();
  char user_input = 0;
  int running = 1;
  while(running){
    running = (autorun || (user_input=getchar())!=EOF);
    if(user_input){ //see if we got a character
      process_user_input(user_input,&autorun,vm);
      user_input = 0;
    }
    insn = info->i_cache[vm->pc];
    if((status=process(vm,insn))>0){
      printf("Line %ld: Error: Interpreter exited with code: %d\n",
              info->d_cache[vm->pc*2+1],status);
      break;
    }else if(status == BVM_REQ_BRANCH){ //vm requests pc branch
      vm->pc = info->br_cache[vm->pc-1]; //find matching brace
    }
    if(vm->pc >= info->i_count){
      break;
    }
    if((dref=info->d_cache[vm->pc * 2]) != PPD_REF_INVALID){
      if((status=info->debug_data[dref]->execute(info->d_cache[vm->pc*2+1],info->debug_data[dref]->data,vm))){
        printf("VM flags raised an error: %d\n",status);
        if(debugging){
          printf("Continue in debug mode? (return):");
          if(getchar() == '\n'){
            autorun = 0;
          } else {
            break;
          }
        } else{
          break;
        }
      }
    }
    step_counter++;
  }

  const char* fmt = "* * * * *\nStopping Virtual Machine...\nCompleted %u steps in %fs\n";
  printf(fmt,step_counter,(float)(clock() - start)/CLOCKS_PER_SEC);
  dump_bvm(vm);

  return status;
}
