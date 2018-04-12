/**
 *  Alexander Haggart, 4/11/18
 *
 *  BeeF interpreter implementation
 *
 *  supply instruction plaintext file as a command-line argument
 */

#include <stdio.h>
#include "Grinder.h"

void print_usage(){
  printf("usage:\n");
}

int main(int argc, char** argv){
  if(argc < 2){
    print_usage();
    return 1;
  }
  Grinder* vm = create_grinder(3);
  FILE* insns = fopen(argv[1],"r");

  char instruction_count = 0;
  char instruction_cache[100];
  
  char insn;
  int ret;
  int running = 1;
  PC_t pc = 0;
  while(running){
    while(instruction_count <= pc){
      if((insn=fgetc(insns))!=EOF){
        instruction_cache[instruction_count] = insn;
        instruction_count++;
      }else{
        running = 0;
        break;
      }
    }

    insn = instruction_cache[pc];

    if((ret=process(vm,insn))>0){
      printf("Interpreter exited with code: %d\n",ret);
      break;
    }else if(ret == GRINDREQ_BRANCH_FWD){
      printf("seeking next instruction\n");
      while(insn != ']'){
        if(pc++ >= instruction_count){
          if((insn=fgetc(insns)!=EOF)){
            instruction_cache[instruction_count] = insn;
            instruction_count++;
          }else{
            printf("Error: Reached EOF expecting: ']'\n");
            running = 0;
            break;
          }
        }else{
          insn = instruction_cache[pc-1];
        }
      }
    }

    pc = vm->pc;
  }
  printf("Done interpretting!\n");
  dump_grinder(vm);

  return 0;
}
