#include <stdlib.h>
#include <stdio.h>

#include "lfsr.h"

int main(int argc,char** argv){
  if(argc < 4){
    printf("usage: lfsr_encrypt seed tap message [outfile]\n");
    return 1;
  }
  FILE* dest = 0;
  if(argc == 5){
      dest = fopen(argv[4],"w");
      if(!dest){
          printf("Error: Could not open file: %s\n",argv[4]);
          exit(1);
      }
  }
  BYTE seed =  (BYTE)atoi(argv[1]);
  BYTE tap  =  (BYTE)atoi(argv[2]);

  char c;
  int i = 0;
  while((c=argv[3][i++])!=0){
    seed = advance(seed,tap);
    if(dest){
        fputc(seed^(BYTE)c,dest);
    }
    //printf("Seed: 0x%x\tEncrypted: 0x%x\n",seed,seed^(BYTE)c);
  }
  printf("Done.... Encrypted %d chars\n",i);
  if(dest){
      fclose(dest);
  }

  return 0;

}
