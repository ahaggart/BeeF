#ifndef LFSR_H
#define LFSR_H
#include <stdlib.h>
#include <stdio.h>

#define BYTE    unsigned char

BYTE advance(BYTE seed, BYTE tap);

#endif //LFSR_H