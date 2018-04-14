
CC = gcc

TARGET = roast

INC_DIR = includes/
SRC_DIR = src/

CODE_DIR = ../code
BUILD_DIR = build

SOURCES = Interpreter.c BeeFVirtualMachine.c BVMStack.c Preprocessor.c
INCLUDES = BeeFVirtualMachine.h BVMStack.h Preprocessor.h

SRC_PATH = $(addprefix ${SRC_DIR},${SOURCES})
INC_PATH = $(addprefix ${INC_DIR},${INCLUDES})

export CPATH = ${INC_DIR}

build: ${SRC_PATH} ${INC_PATH}
	${CC} ${SRC_PATH} -o ${BUILD_DIR}/${TARGET}

hello: build
	./${BUILD_DIR}/${TARGET} ${CODE_DIR}/hello_world.beef

test: build
	./${BUILD_DIR}/${TARGET} ${CODE_DIR}/test.beef

clean:
	rm ${BUILD_DIR}/*

