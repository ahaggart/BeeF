#ifndef GRINDER_H
#define GRINDER_H

/**
 *  virtual machine for simulating BeeF execution
 *
 */

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#define GRINDREQ_BRANCH_FWD  -1
#define GRINDER_SUCCESS       0
#define GRINDERR_AT_LEFTMOST  1
#define GRINDERR_EMPTY_STACK  2

#define CELL unsigned char
#define CELL_IDX unsigned int
#define PC_t  unsigned int

#define DEBUG(str) printf(str)

typedef struct{
  PC_t pc;
  CELL* cells;             CELL_IDX num_cells; CELL_IDX data_head; 
  CELL* stack;             CELL_IDX stack_mem; CELL_IDX stack_ptr;
  CELL_IDX* branch_stack; CELL_IDX branch_mem; CELL_IDX branch_stack_ptr;
} Grinder;

Grinder* create_grinder(CELL_IDX initial_size);
int process(Grinder* g, char insn);
void dump_grinder(Grinder* g);


#endif
