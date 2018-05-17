//This file defines the parameters used in the alu
package definitions;

typedef enum logic[8:0] {
  NOP = 9'b000000000,
  INC = 9'b000000001,
  DEC = 9'b000000010,	
  MVR = 9'b000000100,
  MVL = 9'b000001000,
  PSH = 9'b000010000,    
  POP = 9'b000100000,
  CBF = 9'b001000000,
  CBB = 9'b010000000,
  HLT = 9'b100000000
} op_code;

typedef enum logic[1:0]{
  ALU_FROM_ACC    = 2'b00,
  ALU_FROM_STACK  = 2'b01,
  ALU_FROM_HEAD   = 2'b10,
  ALU_FROM_CACHE  = 2'b11
} ALU_SRC;

typedef enum logic[1:0]{
  ADDR_FROM_HEAD   = 2'b00,
  ADDR_FROM_STACK  = 2'b01,
  ADDR_FROM_CACHE  = 2'b10,
  ADDR_FROM_ALU    = 2'b11
} MEM_ADDR;

typedef enum logic[1:0]{
  MEM_FROM_ACC    = 2'b00,
  MEM_FROM_ALU    = 2'b01,
  MEM_FROM_PC     = 2'b10
} MEM_SRC;

typedef enum logic[1:0]{
  ACC_ZERO        = 2'b00,
  ACC_FROM_ALU    = 2'b01,
  ACC_FROM_MEM    = 2'b10,
  ACC_ONE         = 2'b11
} ACC_SRC;

typedef enum logic{
  ALU_INC   = 1'b0,
  ALU_DEC   = 1'b1
} ALU_OP;

typedef enum logic{
  ENABLE    = 1'b1,
  DISABLE   = 0
} CONTROL;

typedef enum logic{
  MEM_READ  = 1'b0,
  MEM_WRITE = 1'b1
} MEM_OP;

typedef enum logic{
  PC_INCREMENTED  = 1'b0,
  PC_LOADED       = 1'b1
} PC_SRC;

typedef enum logic [1:0]{
  CORE_S        = 2'b00,
  BRANCH_S      = 2'b01,
  STALL_S       = 2'b10
} STATE;

typedef struct packed{
  CONTROL acc_write; 
  ACC_SRC acc_src;  
  CONTROL stack_write;
  CONTROL head_write;
  CONTROL cache_write;
  CONTROL pc_write;
  PC_SRC pc_src;
  MEM_OP mem_op;
  MEM_ADDR mem_addr;
  MEM_SRC mem_src;
  ALU_OP alu_op;
  ALU_SRC alu_src;
  CONTROL loader_select;
  CONTROL halt;
  STATE state;
} control_bundle_s;

typedef logic[$bits(control_bundle_s):0] control_bundle_f;

typedef logic[15:0] PROGRAM_COUNTER;
typedef logic[7:0] PC_HALF;

typedef logic[7:0] BYTE;

typedef logic[8:0] INSTRUCTION;
	 
endpackage // defintions