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

//      VM EXCEPTION CODES
#define BVM_BREAK            -3
#define BVM_HALT             -2
#define BVM_REQ_BRANCH       -1
#define BVM_SUCCESS           0
#define BVM_ERR_AT_LEFTMOST   1
#define BVM_ERR_EMPTY_STACK   2

//      ASSERTION TYPES
#define BVM_ASSERT_NONE       0
#define BVM_ASSERT_VALUE      1 
#define BVM_ASSERT_POS        2 

#define BVM_ASSERTION_PASS    0
#define BVM_ASSERTION_FAIL    1

//    INTERNAL DATA TYPES
#define CELL        unsigned char
#define CELL_IDX    unsigned int
#define CELL_OFFSET int
#define PC_t        unsigned int
#define CELL_SIZE   256

//    CONVENIENCE 
#define BVM BeeFVirtualMachine
#define ASSERT VM_Assertion
#define BVM_META BVM_Metadata

#define ASSERT_CV CellValueAssertion

typedef struct{
  char locked;
  PC_t pc;
  CELL value;
  CELL_IDX address;
  CELL_IDX offset;
} CellValueAssertion;

#define ASSERT_DH DataHeadAssertion

typedef struct{
  char locked;
  PC_t pc;
  CELL_IDX address;
} DataHeadAssertion;

typedef struct{  //assertion data, probably will be moved
  int index;
  void* owner;
  int type;
  void* data;
} VM_Assertion;

typedef struct{     //additional cell metadata, such as active assertions
  ASSERT* assert_ptr;
} BVM_Metadata;

typedef struct{
  PC_t pc;
  PC_t steps;
  BVMS* stack;
  CELL* cells;
  ASSERT** assertions;
  BVM_META** meta;
  CELL_IDX num_cells; 
  int num_assertions;
  CELL_IDX data_head;
  char instruction;
} BeeFVirtualMachine;

BVM*        bvm_create(CELL_IDX initial_size, CELL* starting_mem);
int         bvm_destroy(BVM* g);
int         bvm_process(BVM* g, char insn);
void        bvm_dump(BVM* g,int full);
void        bvm_dump_live(BVM* g,CELL_IDX range);
CELL_IDX    bvm_resize(BVM* g,CELL_IDX new_size);
BVM_META*   bvm_get_metadata(BVM* g,CELL_IDX index);
ASSERT*     bvm_create_assertion(int type,int index,void* owner,void* data);
int         is_instruction(char insn);

// void bvm_scan_metadata(BVM* g); //not working, need to research printf

#endif //BEEFVIRTUALMACHINE_H
