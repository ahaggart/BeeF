/**
 *  Alexander Haggart, 4/11/18
 *
 *  BeeF Grinder virtual machine implementation
 */
#include "Grinder.h"

Grinder* create_grinder(CELL_IDX initial_size){
  Grinder* g = (Grinder*)malloc(sizeof(Grinder));

  g->pc = 0;

  //set up the data cells
  g->cells = (CELL*)calloc(initial_size,sizeof(CELL));
  g->num_cells = initial_size;
  g->data_head = 0;

  //set up the data stack
  g->stack = gcreate_stack(initial_size,sizeof(CELL));

  //set up the branch stack
  // g->branch_stack = (CELL_IDX*)calloc(initial_size,sizeof(CELL_IDX));
  // g->branch_mem = initial_size;
  // g->branch_stack_ptr = -1;

  return g;
}

void dump_grinder(Grinder* g){
  printf("Dumping Grinder...\n");
  printf("Data Head Position: %u\n",g->data_head);
  gsdump(g->stack);
  printf("Cells:\n");
  int i;
  for(i = 0; i < g->num_cells; i++){
    printf("%cc%d:\t%d\t0x%x\n",(i==g->data_head)?'>':' ',i,g->cells[i],g->cells[i]);
  }

}

/**
 *  push current cell value to the grinder data stack
 */
int grinder_psh(Grinder* g){
  gspush(g->stack,(GSTACK_DATA_PTR_T)(g->cells + g->data_head));
  return GRINDER_SUCCESS;
}

/**
 *  move the grinder data head right
 */
int grinder_mvr(Grinder* g){
  g->data_head++;
  if(g->data_head == g->num_cells){
    CELL* tmp = (CELL*)calloc(g->num_cells*2,sizeof(CELL));
    memcpy(tmp,g->cells,g->num_cells);
    g->cells = tmp;
    g->num_cells *= 2;
  }
  return GRINDER_SUCCESS;
}

/**
 * move the grinder data head left, error if head is at leftmost position
 */
int grinder_mvl(Grinder* g){
  if(g->data_head == 0){
    return GRINDERR_AT_LEFTMOST;
  }
  g->data_head--;
  return GRINDER_SUCCESS;
}

/**
 *  increment the cell at the data head
 */
int grinder_inc(Grinder* g){
  g->cells[g->data_head]++;
  return GRINDER_SUCCESS;
}

/**
 *  decrement the cell at the data head
 */
int grinder_dec(Grinder* g){
  g->cells[g->data_head]--;
  return GRINDER_SUCCESS;
}

/**
 * conditional branch forward to matching CBB
 */
int grinder_cbf(Grinder* g){
  if(!(g->cells[g->data_head])){
    return GRINDREQ_BRANCH;
  }
  return GRINDER_SUCCESS;
}

/**
 * conditional branch back to matching CBF
 */
int grinder_cbb(Grinder* g){
  if(g->cells[g->data_head]){
    return GRINDREQ_BRANCH;
  }
  return GRINDER_SUCCESS;
}

/**
 * pop grinder data stack into current cell
 */
int grinder_pop(Grinder* g){
  CELL* popped = (CELL*)gspop(g->stack);
  if(popped == 0){
    return GRINDERR_EMPTY_STACK;
  }
  g->cells[g->data_head] = *popped;
  return GRINDER_SUCCESS;
}


int process(Grinder* g,char insn){
  // printf("size: %u,\thead: %u\n",g->num_cells,g->data_head);
  g->pc++;
  switch(insn){
    case '^':
      DEBUG("PSH\n");
      return grinder_psh(g);
    case '>':
      DEBUG("MVR\n");
      return grinder_mvr(g);
    case '<':
      DEBUG("MVL\n");
      return grinder_mvl(g);
    case '+':
      DEBUG("INC\n");
      return grinder_inc(g);
    case '-':
      DEBUG("DEC\n");
      return grinder_dec(g);
    case '[':
      DEBUG("CBF\n");
      return grinder_cbf(g);
    case ']':
      DEBUG("CBB\n");
      return grinder_cbb(g);
    case '_':
      DEBUG("POP\n");
      return grinder_pop(g);
    default: //ignore invalid char
      return 0;
  }
}
