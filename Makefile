
CC = gcc



build: Interpreter.c Grinder.c
	${CC} Interpreter.c Grinder.c -o build/run_beef

Interpreter.c: Grinder.c

Grinder.c: Grinder.h
