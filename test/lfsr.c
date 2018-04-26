#include "lfsr.h"

BYTE advance(BYTE seed, BYTE tap){
  int i;
  int toggle = 0;
  for(i = 0; i < 8; i++){
    if(((tap >> i & seed >> i) & 0x01)){
      if(toggle){
        toggle = 0;
      }else{
        toggle = 1;
      }
    }
  }
  return seed << 1 | toggle;
}

//pass a command line argument if you want a standalone lfsr stepper utility
// gcc -D __LFSR__ lfsr.c -o lfsr
#ifdef __LFSR__ 

int main(int argc, char** argv){
  if(argc != 3){
    printf("usage: lfsr seed tap");
    exit(1);
  }
  BYTE seed = (BYTE)atoi(argv[1]);
  BYTE tap  = (BYTE)atoi(argv[2]);

  printf("advance(%u,%u)\t=\t%u\n",seed,tap,advance(seed,tap));
}

#endif