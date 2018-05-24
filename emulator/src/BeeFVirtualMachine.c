/**
 *  Alexander Haggart, 4/11/18
 *
 *  BeeF BVM virtual machine implementation
 */
#include "BeeFVirtualMachine.h"

BVM* bvm_create(CELL_IDX initial_size,CELL* starting_mem){
  BVM* g = (BVM*)malloc(sizeof(BVM));

  g->pc = 0;
  g->steps = 0;

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
  g->num_assertions = 0;
  
  return g;
}

void bvm_dump(BVM* g,int full){
  if(!full){
    bvm_dump_live(g,10);
    return;
  }
  printf("Dumping Virtual Machine...\n");
  printf(FMT_INDENT "Data Head Position: %u\n",g->data_head);
  printf(FMT_INDENT "Program Counter: %u\n",g->pc);
  bvms_dump(g->stack);
  printf("Cells:\n");
  int i;
  CELL val;
  for(i = 0; i < g->num_cells; i++){
    val = g->cells[i];
    printf("%cc%d:\t%u\t0x%x\t%c\n",(i==g->data_head)?'>':' ',i,val,val,val);
  }
}

void bvm_dump_live(BVM* g,CELL_IDX range){

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

BVM_META* bvm_get_metadata(BVM* g,CELL_IDX index){
  BVM_META* meta = g->meta[index];
  if(!meta){
    meta = (BVM_META*)calloc(sizeof(BVM_META),1);
    g->meta[index] = meta;
  }
  return meta;
}

// void bvm_scan(BVM* g,void** data,size_t width,const char* fmt){
//   int PER_ROW = 8;
//   int SCAN_BUFSIZE = 20;
//   int i;
//   char scan_format[SCAN_BUFSIZE];
//   sprintf(scan_format,"(%%3d,%s)\t",fmt);
//   for(i=0;i<g->num_cells;i++){
//     printf(scan_format,i,data[i*width]);
//     if(!((i+1)%PER_ROW)){
//       printf("\n");
//     }
//   }
//   if(i%PER_ROW)
//     printf("\n");
// }

// void bvm_scan_metadata(BVM* g){
//   bvm_scan(g,(void**)g->meta,sizeof(BVM_META*),"%p");
// }

void* expand_array(void* array,size_t width,size_t curr_size,size_t new_size){ //size in bytes
  void* tmp = calloc(new_size,width);
  memcpy(tmp,array,width*curr_size);
  free(array);
  return tmp;
}

CELL_IDX bvm_resize(BVM* g,CELL_IDX new_size){
  if(new_size < g->num_cells){
    printf("Error: Cannot downsize VM\n");
    exit(1);
  }
  g->cells = (CELL*)      expand_array(g->cells,sizeof(CELL),g->num_cells,new_size);
  g->meta  = (BVM_META**) expand_array(g->meta,sizeof(BVM_META*),g->num_cells,new_size);
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

ASSERT* bvm_create_assertion(int type, int index, void* owner, void* data){
  ASSERT* assertion = (ASSERT*)malloc(sizeof(ASSERT));
  assertion->type = type;
  assertion->index = index;
  assertion->owner = owner;
  assertion->data = data;
  return assertion;
}

int bvm_destroy(BVM* g){ //destroy a VM, releasing its resources
  int i;
  if(g->num_cells){
    for(i=0;i<g->num_cells;i++){ //free all metadata structs
      if(g->meta[i]){
        free(g->meta[i]);
        g->meta[i] = 0;
      }
    }
    free(g->meta);
    g->meta = 0;
    free(g->cells);
    g->cells = 0;
  }
  if(g->num_assertions){
    for(i=0;i<g->num_assertions;i++){ //free all assertion structs
      if(g->assertions[i]){
        free(g->assertions[i]);
        g->assertions[i] = 0;
      }
    }
    free(g->assertions);
    g->assertions = 0;
  }
  free(g->stack);
  g->stack = 0;
  free(g);
  return 0;
}

int bvm_process(BVM* g,char insn){
  // printf("size: %u,\thead: %u\n",g->num_cells,g->data_head);
  g->steps++;
  g->pc++;
  g->instruction = insn;
  switch(insn){
    case '^':
      BVM_ASSEMBLY("PSH\n");
      return bvm_psh(g);
    case '>':
      BVM_ASSEMBLY("MVR\n");
      return bvm_mvr(g);
    case '<':
      BVM_ASSEMBLY("MVL\n");
      return bvm_mvl(g);
    case '+':
      BVM_ASSEMBLY("INC\n");
      return bvm_inc(g);
    case '-':
      BVM_ASSEMBLY("DEC\n");
      return bvm_dec(g);
    case '[':
      BVM_ASSEMBLY("CBF\n");
      return bvm_cbf(g);
    case ']':
      BVM_ASSEMBLY("CBB\n");
      return bvm_cbb(g);
    case '_':
      BVM_ASSEMBLY("POP\n");
      return bvm_pop(g);
    case '!':
      BVM_ASSEMBLY("HALT\n");
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
