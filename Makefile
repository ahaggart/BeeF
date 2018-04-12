
CC = gcc

SOURCES = Interpreter.c Grinder.c GStack.c
INCLUDES = Grinder.h GStack.h

build: ${SOURCES} ${INCLUDES}
	${CC} ${SOURCES} -o build/run_beef

