#include <stdlib.h>
#include <stdio.h>

#include "lfsr.h"

const int num_taps = 8;
const BYTE taps[] = {0xe1, 0xd4, 0xc6, 0xb8, 0xb4, 0xb2, 0xfa, 0xf3}; 
const BYTE SPACE_CHAR = ' ';
const BYTE CAP_M_CHAR = 'M';

typedef struct{
    BYTE seed;
    BYTE tap; 
} LFSR_INFO;

void file_too_short(){
  printf("Error: Message file too short.\n");
  exit(1);
}

void get_encryption_info(FILE* msg,LFSR_INFO* info){
  //find the seed by looking at the bits
  BYTE seed,lfsr_prev, lfsr_next;
  int impossible[num_taps] = {0};
  int valid_count = num_taps;
  //get the first two chars
  int c;
  int i = 0;
  unsigned int dec;
  c=fgetc(msg);
  lfsr_prev = (BYTE)c^SPACE_CHAR;
  seed = lfsr_prev;
  while((c=fgetc(msg))!=EOF){
    lfsr_next = (BYTE)c^SPACE_CHAR;
    for(i = 0; i < num_taps; i++){
      if(lfsr_next != advance(lfsr_prev,taps[i])){
        if(!impossible[i]){
            valid_count--;
        }
        impossible[i] = 1;
      }
    }
    if(valid_count <= 1){
        break;
    }
    lfsr_prev = lfsr_next;
  }

  if(c == EOF){
      file_too_short();
  }

  BYTE tap = 0;

  for(i=0;i<num_taps;i++){
      if(!impossible[i]){
          tap = taps[i];
          printf("Found tap value: 0x%x\n",tap);
          break;
      }
  }

  info->tap  = tap;
  info->seed = seed;

  fseek(msg,0,SEEK_SET);
}

//decrypt a message that starts with 0+ space chars + "Mr. Watson"
int main(int argc,char** argv){
  if(argc != 2){
    printf("usage: lfsr_decrypt message_text_file\n");
    return 1;
  }
  FILE* msg = fopen(argv[1],"r");
  if(!msg){
      printf("Error: Could not open file: %s\n",argv[1]);
      exit(1);
  }

  LFSR_INFO info;
  get_encryption_info(msg,&info);

  BYTE seed = info.seed;
  int c;
  int i = 0;
  unsigned int dec;
  while((c=fgetc(msg))!=EOF){
    dec = seed^(BYTE)c;
    printf("Seed: 0x%x\tDecrypted: 0x%x\t\t%c\n",seed,dec,dec);
    seed = advance(seed,info.tap);
    i++;
  }
  printf("Done.... Decrypted %d chars\n",i);
  fclose(msg);
  return 0;

}