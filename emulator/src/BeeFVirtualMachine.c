/**
 *  Alexander Haggart, 4/11/18
 *
 *  BeeF BVM virtual machine implementation
 */
#include "BeeFVirtualMachine.h"

BVM* create_bvm(CELL_IDX initial_size,CELL* starting_mem){
  BVM* g = (BVM*)malloc(sizeof(BVM));

  g->pc = 0;

  //set up the data cells
  if(!starting_mem){
    g->cells = (CELL*)calloc(initial_size,sizeof(CELL));
  }else{
    g->cells = starting_mem;
  }
  g->num_cells = initial_size;
  g->data_head = 0;

  //set up the data stack
  g->stack = bvms_create_stack(initial_size,sizeof(CELL));

  g->instruction = 0;

  g->meta = (BVM_META**)calloc(initial_size,sizeof(BVM_META*));

  g->assertions = 0;
  
  return g;
}

void dump_bvm(BVM* g,int full){
  if(!full){
    dump_bvm_live(g,10);
    return;
  }
  printf("Dumping Virtual Machine...\n");
  printf(FMT_INDENT "Data Head Position: %u\n",g->data_head);
  bvms_dump(g->stack);
  printf("Cells:\n");
  int i;
  CELL val;
  for(i = 0; i < g->num_cells; i++){
    val = g->cells[i];
    printf("%cc%d:\t%u\t0x%x\t%c\n",(i==g->data_head)?'>':' ',i,val,val,val);
  }
}

void dump_bvm_live(BVM* g,CELL_IDX range){

  //get the upper and lower cells to print
  long lower = (long)(g->data_head)-range;
  lower = (lower>0)?lower:0;
  long upper = (long)(g->data_head)+range;
  upper = (upper<g->num_cells)?upper:g->num_cells;

  int i;
  // int term_height = 80; //good enough?
  // //clear the screen (aggressively)
  // for(i = 0; i < term_height; i++){
  //   printf("\n");
  // }

  const char* hexstr = " 0x%.2x ";

  //print curr instruction
  printf("PROGRAM COUNTER: %d\n",g->pc);
  printf("INSTRUCTION: %c\n",g->instruction);
  

  //print the stack
  for(i=0;i<g->stack->top+1;i++){
    printf("======");
  }
  printf("\nSTACK:");
  for(i=0;i<g->stack->top;i++){
    printf(hexstr,g->stack->stack[i]);
  }
  printf("\n");
  for(i=0;i<g->stack->top+1;i++){
    printf("======");
  }
  printf("\nCELLS:\n");
  //print the cell addresses
  for(i = lower; i<upper; i++){
    printf("%5u ",i);
  }
  printf("\n");
  //print the data head above the cells
  for(i = lower; i<upper; i++){
    if(i == g->data_head){
      printf("  vv  ");
    } else {
      printf("      ");
    }
  }
  printf("\n");
  //print the cells in range
  for(i = lower; i<upper; i++){
    printf(hexstr,g->cells[i]);
  }
  printf("\n");
}

void* expand_array(void* array,size_t curr_size,size_t new_size){ //size in bytes
  void* tmp = calloc(new_size,1);
  memcpy(tmp,array,curr_size);
  return tmp;
}

CELL_IDX bvm_resize(BVM* g,CELL_IDX new_size){
  if(new_size < g->num_cells){
    printf("Error: Cannot downsize VM\n");
    exit(1);
  }
  g->cells = (CELL*)      expand_array(g->cells,sizeof(CELL) *g->num_cells,new_size);
  g->meta  = (BVM_META**) expand_array(g->meta,sizeof(BVM_META*)*g->num_cells,new_size);
  g->num_cells = new_size;
  return g->num_cells;
}

/**
 *  push current cell value to the bvm data stack
 */
int bvm_psh(BVM* g){
  bvms_push(g->stack,(BVMS_DATA_PTR_T)(g->cells + g->data_head));
  return BVM_SUCCESS;
}

/**
 *  move the bvm data head right
 */
int bvm_mvr(BVM* g){
  g->data_head++;
  if(g->data_head == g->num_cells){
    bvm_resize(g,g->num_cells*2);
  }
  return BVM_SUCCESS;
}

/**
 * move the bvm data head left, error if head is at leftmost position
 */
int bvm_mvl(BVM* g){
  if(g->data_head == 0){
    return BVM_ERR_AT_LEFTMOST;
  }
  g->data_head--;
  return BVM_SUCCESS;
}

/**
 *  increment the cell at the data head
 */
int bvm_inc(BVM* g){
  g->cells[g->data_head]++;
  // g->cells[g->data_head] = ((int)g->cells[g->data_head] + 1)%256;
  return BVM_SUCCESS;
}

/**
 *  decrement the cell at the data head
 */
int bvm_dec(BVM* g){
  g->cells[g->data_head]--;
  return BVM_SUCCESS;
}

/**
 * conditional branch forward to matching CBB
 */
int bvm_cbf(BVM* g){
  if(!(g->cells[g->data_head])){
    return BVM_REQ_BRANCH;
  }
  return BVM_SUCCESS;
}

/**
 * conditional branch back to matching CBF
 */
int bvm_cbb(BVM* g){
  if(g->cells[g->data_head]){
    return BVM_REQ_BRANCH;
  }
  return BVM_SUCCESS;
}

/**
 * pop bvm data stack into current cell
 */
int bvm_pop(BVM* g){
  CELL* popped = (CELL*)bvms_pop(g->stack);
  if(popped == 0){
    return BVM_ERR_EMPTY_STACK;
  }
  g->cells[g->data_head] = *popped;
  return BVM_SUCCESS;
}

int bvm_halt(BVM* g){
  return BVM_HALT;
}

int process(BVM* g,char insn){
  // printf("size: %u,\thead: %u\n",g->num_cells,g->data_head);
  g->pc++;
  g->instruction = insn;
  switch(insn){
    case '^':
      BVM_DEBUG("PSH\n");
      return bvm_psh(g);
    case '>':
      BVM_DEBUG("MVR\n");
      return bvm_mvr(g);
    case '<':
      BVM_DEBUG("MVL\n");
      return bvm_mvl(g);
    case '+':
      BVM_DEBUG("INC\n");
      return bvm_inc(g);
    case '-':
      BVM_DEBUG("DEC\n");
      return bvm_dec(g);
    case '[':
      BVM_DEBUG("CBF\n");
      return bvm_cbf(g);
    case ']':
      BVM_DEBUG("CBB\n");
      return bvm_cbb(g);
    case '_':
      BVM_DEBUG("POP\n");
      return bvm_pop(g);
    case '!':
      BVM_DEBUG("HALT\n");
      return bvm_halt(g);
    default: //ignore invalid char
      printf("Got some garbage: 0x%x\n",insn);
      return 0;
  }
}

int is_instruction(char c){
  switch(c){
    case '^':
    case '>':
    case '<':
    case '+':
    case '-':
    case '[':
    case ']':
    case '_':
    case '!':
      return 1;
    default: //ignore invalid char
      return 0;
  }
}
