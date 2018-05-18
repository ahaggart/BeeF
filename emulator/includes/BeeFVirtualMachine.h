#ifndef BEEFVIRTUALMACHINE_H
#define BEEFVIRTUALMACHINE_H

/**
 *  virtual machine for simulating BeeF execution
 *
 */

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#include "BVMStack.h"
#include "Common.h"

#define BVM_HALT             -2
#define BVM_REQ_BRANCH       -1
#define BVM_SUCCESS           0
#define BVM_ERR_AT_LEFTMOST   1
#define BVM_ERR_EMPTY_STACK   2

#define CELL unsigned char
#define CELL_IDX unsigned int
#define PC_t  unsigned int

#define BVM_HISTORY_SIZE      20

#define BVM BeeFVirtualMachine

#define ASSERT VM_Assertion

#define BVM_META BVM_Metadata

typedef struct{
  char locked;
  CELL value;
  CELL_IDX address;
  CELL_IDX offset;
} VM_Assertion;

typedef struct{
  int assert_index;
} BVM_Metadata;

typedef struct{
  PC_t pc;
  BVMS* stack;
  CELL* cells;
  ASSERT** assertions;
  BVM_META** meta;
  CELL_IDX num_cells; 
  CELL_IDX data_head;
  char instruction;
} BeeFVirtualMachine;

BVM* create_bvm(CELL_IDX initial_size, CELL* starting_mem);
int process(BVM* g, char insn);
void dump_bvm(BVM* g,int full);
void dump_bvm_live(BVM* g,CELL_IDX range);
CELL_IDX bvm_resize(BVM* g,CELL_IDX new_size);
int is_instruction(char insn);


#endif //BEEFVIRTUALMACHINE_H
