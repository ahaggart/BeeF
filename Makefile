
CC = gcc

TARGET = run_beef

SOURCES = Interpreter.c Grinder.c GStack.c
INCLUDES = Grinder.h GStack.h

build: ${SOURCES} ${INCLUDES}
	${CC} ${SOURCES} -o build/${TARGET}

hello: build
	./build/${TARGET} hello_world.beef

