CC = gcc

LFSR_SRC = lfsr.c
INCLUDES = lfsr.h

ENC_SRC = encrypt.c
ENC_TARGET = encrypt

DEC_SRC = decrypt.c
DEC_TARGET = decrypt

CFLAGS = -lm

all: encrypt decrypt

encrypt: ${ENC_SRC} ${LFSR_SRC} ${INCLUDES}
	${CC} ${CFLAGS} ${ENC_SRC} ${LFSR_SRC} -o ${ENC_TARGET}

decrypt: ${DEC_SRC} ${LFSR_SRC} ${INCLUDES}
	${CC} ${CFLAGS} ${DEC_SRC} ${LFSR_SRC} -o ${DEC_TARGET}
