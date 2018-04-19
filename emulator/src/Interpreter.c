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

int main(int argc, char** argv){
  if(argc < 2){
    print_usage();
    return 1;
  }
  char* srcname = 0;
  int autorun = 1;
  int debugging = 0;
  if(argc == 3 && argv[1][0] == '-'){ //flags
    if(argv[1][1] == 'd'){ //TODO: better arg parsing lol
      autorun = 0;
      debugging = 1;
    }
    srcname = argv[2];
  } else{
    srcname = argv[1];
  }
  BVM* vm = create_bvm(12); //big enough for the hello world program
  FILE* insns = fopen(srcname,"r");
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
