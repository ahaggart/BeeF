#ifndef DECRYPT_H
#define DECRYPT_H

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "lfsr.h"

typedef struct{
    BYTE seed;
    BYTE tap; 
} LFSR_INFO;

#endif //DECRYPT_H