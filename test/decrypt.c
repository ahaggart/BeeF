#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "lfsr.h"

const int num_taps = 8;
const int num_tapped = 4;
const BYTE taps[] = {0xe1, 0xd4, 0xc6, 0xb8, 0xb4, 0xb2, 0xfa, 0xf3}; 
const BYTE SPACE_CHAR = ' ';
const BYTE CAP_M_CHAR = 'M';
int INVALID_REF = 8;

typedef struct{
    BYTE seed;
    BYTE tap; 
} LFSR_INFO;

void file_too_short(){
  printf("Error: Message file too short.\n");
  exit(1);
}

int count_bits(BYTE val){
    int count = 0;
    int i;
    for(i=0;i<8;i++){
        if((val>>i)&0x01){
            count++;
        }
    }
    return count;
}

void get_zero_pair(BYTE val, int* dest){
    int got_first = 0;
    int i;
    for(i=0;i<7;i++){ //only check first 7 bits
        if(!((val>>i)&0x01)){
            if(got_first){
                dest[1] = i;
                break;
            } else{
                dest[0] = i;
                got_first = 1;
            }
        }
    }
}

void insert_ref(int* pair,BYTE* refs){
    int done_first = 0;
    int item = pair[0];
    int ref  = pair[1];
    int i;
    for(i=0;i<num_tapped;i++){
        if(refs[item*num_tapped + i] == INVALID_REF){
            refs[item*num_tapped + i] = ref;
            if(!done_first){
                done_first = 1;
                i = -1;
                item = pair[1];
                ref = pair[0];
                continue;
            } else{
                break;
            }
        }
    }
}

void get_encryption_info_2(FILE* msg,LFSR_INFO* info){
    BYTE possible = 0xFF;
    BYTE suspected = 0;
    BYTE crossref[num_tapped * 8];
    memset(crossref,INVALID_REF,num_tapped*8);
    int pair[2];
    int valid_counter = 8;

    int c,lsb,nbits;
    BYTE curr_seed,old_known;
    BYTE expected_val = SPACE_CHAR;
    //we can determine the number of 1s in the tapped byte based on the LSB
    while((c=fgetc(msg))!=EOF){
        curr_seed = (BYTE)c ^ expected_val;
        old_known = curr_seed >> 1;
        nbits = count_bits(curr_seed);
        BYTE lsb = curr_seed & 0x01;
        if(lsb && nbits < 2){ //odd number of 1s

        } else if(nbits > 5){ //even number of 1s
            if(nbits == 6){
                get_zero_pair(old_known,pair);
                insert_ref(pair,crossref);
            } else if(nbits == 7){

            }
        }
    }

}

void get_encryption_info(FILE* msg,LFSR_INFO* info){
  //find the seed by looking at the bits
  BYTE seed,lfsr_prev, lfsr_next;
  int impossible[num_taps] = {0};
  int valid_count = num_taps;
  //get the first two chars
  int c;
  int count = 1;
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
    count++;
  }

  if(c == EOF){
      file_too_short();
  }

  BYTE tap = 0;

  for(i=0;i<num_taps;i++){
      if(!impossible[i]){
          tap = taps[i];
          printf("Found tap value: 0x%x in %d bytes\n",tap,count);
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