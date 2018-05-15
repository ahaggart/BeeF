/*
    controller for single-cycle stalls (double mem ops)
*/
import definitions::*;
module stall_control(
    input op_code instruction,
    input logic acc_zero,
    output control_bundle_f controls
);

control_bundle_s bundle;
assign controls = control_bundle_f'(bundle);

// REFERENCE
// typedef struct packed{
//   CONTROL acc_write; 
//   ACC_SRC acc_src;  
//   CONTROL stack_write;
//   CONTROL head_write;
//   CONTROL cache_write;
//   CONTROL pc_write;
//   PC_SRC pc_src;
//   MEM_OP mem_op;
//   MEM_ADDR mem_addr;
//   MEM_SRC mem_src;
//   ALU_OP alu_op;
//   ALU_SRC alu_src;
//   CONTROL loader_select;
//   STATE state;
// } control_bundle_s;

always_comb begin
    case(instruction)
        CBF: begin //write second half of pc to cache
            bundle.state            <= CORE_S;
            bundle.cache_write      <= ENABLE;
            bundle.alu_op           <= ALU_INC;
            bundle.alu_src          <= ALU_FROM_CACHE;
            bundle.pc_src           <= PC_INCREMENTED;
            bundle.loader_select    <= ENABLE;
            bundle.mem_addr         <= ADDR_FROM_ALU;
            bundle.mem_src          <= MEM_FROM_PC; //dont care
            bundle.mem_op           <= MEM_WRITE;
            
        end
        CBB: begin //read second half of pc from cache
            bundle.state            <= CORE_S; 
            bundle.cache_write      <= DISABLE;
            bundle.alu_op           <= ALU_DEC;
            bundle.alu_src          <= ALU_FROM_CACHE;
            bundle.pc_src           <= PC_LOADED;
            bundle.loader_select    <= ENABLE;
            bundle.mem_addr         <= ADDR_FROM_ALU; //use decremented cacheptr
            bundle.mem_src          <= MEM_FROM_ACC; //dont care
            bundle.mem_op           <= MEM_READ;
        end
        default: begin //POP
            bundle.state            <= CORE_S; 
            bundle.cache_write      <= DISABLE;
            bundle.alu_op           <= ALU_DEC;
            bundle.alu_src          <= ALU_FROM_STACK;
            bundle.pc_src           <= PC_INCREMENTED;
            bundle.loader_select    <= DISABLE;
            bundle.mem_addr         <= ADDR_FROM_HEAD;
            bundle.mem_src          <= MEM_FROM_ACC;
            bundle.mem_op           <= MEM_WRITE;
        end
    endcase
    bundle.pc_write     <= ENABLE; //always advance PC
    bundle.head_write   <= DISABLE;
    bundle.stack_write  <= DISABLE;
    bundle.acc_write    <= DISABLE;
    bundle.acc_src      <= ACC_FROM_ALU; //dont care
end

endmodule