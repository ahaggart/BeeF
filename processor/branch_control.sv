import definitions::*;
module branch_control(
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
        CBF: begin
            bundle.acc_write   <= ENABLE;
            bundle.cache_write <= DISABLE;

            bundle.mem_op      <= MEM_READ;
            bundle.alu_op      <= ALU_INC;

            bundle.mem_src     <= MEM_FROM_PC; //dont care
            bundle.mem_addr    <= ADDR_FROM_CACHE;
        end
        CBB: begin
            bundle.acc_write   <= ENABLE;
            bundle.cache_write <= DISABLE;

            bundle.mem_op      <= MEM_READ;
            bundle.alu_op      <= ALU_DEC;

            bundle.mem_src     <= MEM_FROM_PC; //dont care
            bundle.mem_addr    <= ADDR_FROM_CACHE;
        end
        default: begin //NOP
            bundle.acc_write   <= DISABLE;
            bundle.cache_write <= DISABLE;

            bundle.mem_op      <= MEM_READ;
            bundle.alu_op      <= ALU_INC;

            bundle.mem_src     <= MEM_FROM_ACC;
            bundle.mem_addr    <= ADDR_FROM_HEAD;
        end
    endcase
    bundle.stack_write  <= DISABLE;
    bundle.head_write   <= DISABLE;
    bundle.acc_src      <= ACC_FROM_ALU;
    bundle.loader_select<= DISABLE;
end

endmodule