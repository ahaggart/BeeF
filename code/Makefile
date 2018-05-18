
CC_DIR = ../lang
CC = ${CC_DIR}/bcc.py

VM_DIR = ../emulator
VM_BLD = build
VM_EXC = roast
VM_PATH = ${VM_DIR}/${VM_BLD}/${VM_EXC}

COW_DIR = ./cow
COW_EXT = .cow
BEEF_EXT = .beef

BUILD_DIR = ./build

HELLO_SRC = hello_world_2

hello: ${HELLO_COW}
	${CC} ${COW_DIR}/${HELLO_SRC}${COW_EXT} ${BUILD_DIR}/${HELLO_SRC}${BEEF_EXT}

vm: ${VM_PATH}
	$(MAKE) -C ${VM_DIR}