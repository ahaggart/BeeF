CC = gcc

LFSR_SRC = lfsr.c
LFSR_TARGET = lfsr

INCLUDES = lfsr.h decrypt.h

ENC_SRC = encrypt.c
ENC_TARGET = encrypt

DEC_SRC = decrypt.c
DEC_TARGET = decrypt

CFLAGS = -lm

ENC_DIR = enc

MESSAGE_CONVERTER = message_to_seed.py
CODE_DIR = ../code
SEED_DIR = ${CODE_DIR}/seed

all: encrypt decrypt lfsr

lfsr: ${INCLUDES} ${LFSR_SRC}
	${CC} ${CFLAGS} ${LFSR_SRC} -o ${LFSR_TARGET}

encrypt: ${ENC_SRC} ${LFSR_SRC} ${INCLUDES}
	${CC} ${CFLAGS} ${ENC_SRC} ${LFSR_SRC} -o ${ENC_TARGET}

decrypt: ${DEC_SRC} ${LFSR_SRC} ${INCLUDES}
	${CC} ${CFLAGS} ${DEC_SRC} ${LFSR_SRC} -o ${DEC_TARGET}

seed: encrypt
	@echo "Making cell file with params: SEED=${SEED} TAP=${TAP}"
	@./encrypt ${SEED} ${TAP} '${MESSAGE_TO_ENCRYPT}' ${ENC_DIR}/${SEED}_${TAP}_encrypted.txt
	@${CODE_DIR}/${MESSAGE_CONVERTER} \
		${ENC_DIR}/${SEED}_${TAP}_encrypted.txt \
		${SEED_DIR}/${SEED}_${TAP}_enc.seed
