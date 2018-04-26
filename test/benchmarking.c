#include <time.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#include "lfsr.h"
#include "decrypt.h"

const int num_taps = 8;
const int num_tapped = 4;
const BYTE taps[] = {0xe1, 0xd4, 0xc6, 0xb8, 0xb4, 0xb2, 0xfa, 0xf3}; 
const BYTE SPACE_CHAR = ' ';
const BYTE CAP_M_CHAR = 'M';

const char* MESSAGE = "                Mr. Watson, come here. I want to see you.       ";

void encrypt(BYTE seed,BYTE tap,int size,BYTE* message){
    char c;
    int i = 0;
    for(i=0;i<size;i++){
        c=message[i];
        seed = advance(seed,tap);
        message[i] = seed^(BYTE)c;
    }
}

int get_encryption_info(int size,BYTE* msg,LFSR_INFO* info){
    //find the seed by looking at the bits
    BYTE seed,lfsr_prev, lfsr_next;
    int impossible[num_taps] = {0};
    int valid_count = num_taps;
    //get the first two chars
    int count = 1;
    int i = 0;

    int idx = 0;
    BYTE c = msg[idx];
    lfsr_prev = (BYTE)c^SPACE_CHAR;
    seed = lfsr_prev;
    for(idx=1;idx<size;idx++){
        c = msg[idx];
        lfsr_next = (BYTE)c^SPACE_CHAR;
        for(i = 0; i < num_taps; i++){
            if(!impossible[i]){
                if(lfsr_next != advance(lfsr_prev,taps[i])){
                    valid_count--;
                    impossible[i] = 1;
                }
            }
        }
        if(valid_count == 1){
            break;
        }
        lfsr_prev = lfsr_next;
        count++;
    }

    BYTE tap = 0;

    for(i=0;i<num_taps;i++){
        if(!impossible[i]){
            if(tap){
                printf("Error: Multiple valid taps\n");
                break;
            }
            tap = taps[i];
        }
    }
    if(!tap){
        return 0;
    }

    info->tap  = tap;
    info->seed = seed;

    return count;
}

int decrypt(LFSR_INFO* info, int message_size,BYTE* message){
    int bytes = get_encryption_info(message_size,message,info);
    message[0] = SPACE_CHAR; //can make this assumption based on assignment
    encrypt(info->seed,info->tap,message_size-1,message+1);
    return bytes;
}

int main(int argc, char** argv){
    if(argc < 2){
        printf("usage: benchmark num_tests [seed]\n");
        return 1;
    }
    if(argc == 3){
        srand(atoi(argv[2]));
    }else{
        srand(time(NULL)); 
    }

    int silent = 1;

    BYTE seed,tap;
    long MESSAGE_SIZE = strlen(MESSAGE);

    int num_tests = (int)atoi(argv[1]);
    int ntest;
    int nbytes;
    BYTE curr_message[MESSAGE_SIZE];

    LFSR_INFO info;

    int total_bytes = 0;
    int total_tests = 0;

    for(ntest = 0; ntest < num_tests; ntest++){
        seed = (BYTE)rand();
        tap  = taps[rand()&0x7];
        memcpy(curr_message,MESSAGE,MESSAGE_SIZE*sizeof(char));
        encrypt(seed,tap,MESSAGE_SIZE,curr_message);
        if(!silent) printf("Message %d encrypted with:(%u,%u)\n",ntest,seed,tap);

        nbytes = decrypt(&info,MESSAGE_SIZE,curr_message);
        total_bytes += nbytes;
        if(nbytes){
            if(!silent) printf("Decrypted #%d in %d bytes (%u,%u):\t%s\n",ntest,nbytes,info.seed,info.tap,curr_message);
            if(memcmp(curr_message,MESSAGE,MESSAGE_SIZE)){
                printf("Decryption Failure on #%d (%u->%u,%u->%u): %s\n",
                            ntest,
                            advance(seed,tap),info.seed,
                            tap,info.tap,
                            curr_message);
            }
            total_tests++;
        }else{
            if(!silent) printf("Failed to find tap value.\n");
        }
    }

    printf("Avg Bytes to Decrypt: %f\n",(float)total_bytes/total_tests);
}