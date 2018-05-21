
CC = gcc

BCC = bcc.py

TARGET = roast

INC_DIR = includes/
SRC_DIR = src/

CODE_DIR = ../code
BUILD_DIR = build

LANG_DIR = ../lang

HELLO_NAME = hello_world_2
BEEF_EXT = .beef
COW_EXT	= .cow

SOURCES = Interpreter.c BeeFVirtualMachine.c BVMStack.c Preprocessor.c Directives.c
INCLUDES = BeeFVirtualMachine.h BVMStack.h Preprocessor.h Directives.h

SRC_PATH = $(addprefix ${SRC_DIR},${SOURCES})
INC_PATH = $(addprefix ${INC_DIR},${INCLUDES})

export CPATH = ${INC_DIR}

build: ${SRC_PATH} ${INC_PATH}
	${CC} ${CFLAGS} ${SRC_PATH} -o ${BUILD_DIR}/${TARGET}

hello: build 
	${LANG_DIR}/${BCC} ${CODE_DIR}/cow/${HELLO_NAME}${COW_EXT} ${CODE_DIR}/build/${HELLO_NAME}${BEEF_EXT}
	./${BUILD_DIR}/${TARGET} ${CODE_DIR}/build/${HELLO_NAME}${BEEF_EXT}

test: build
	./${BUILD_DIR}/${TARGET} ${CODE_DIR}/test.beef

debug:
	$(MAKE) -B build CFLAGS=-DVM_DEBUG

clean:
	rm ${BUILD_DIR}/*

