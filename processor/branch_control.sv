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

            bundle.mem_op      <= MEM_READ;
            bundle.alu_op      <= ALU_INC;

            bundle.mem_src     <= MEM_FROM_PC; //dont care
            bundle.mem_addr    <= ADDR_FROM_CACHE; //dont care
        end
        CBB: begin
            bundle.acc_write   <= ENABLE;

            bundle.mem_op      <= MEM_READ;
            bundle.alu_op      <= ALU_DEC;

            bundle.mem_src     <= MEM_FROM_PC; //dont care
            bundle.mem_addr    <= ADDR_FROM_CACHE;
        end
        default: begin //NOP
            bundle.acc_write   <= DISABLE;

            bundle.mem_op      <= MEM_READ;
            bundle.alu_op      <= ALU_INC;

            bundle.mem_src     <= MEM_FROM_ACC;
            bundle.mem_addr    <= ADDR_FROM_HEAD; //dont care
        end
    endcase
    if(acc_zero) begin
        bundle.acc_src      <= ACC_ZERO; //redirect the acc source to a zeroed wire
        bundle.state        <= CORE_S;
        bundle.pc_write     <= DISABLE; //re-do this instruction
    end else begin
        bundle.acc_src      <= ACC_FROM_ALU;
        bundle.state        <= BRANCH_S;
        bundle.pc_write     <= ENABLE; //advance to next instruction
    end
    bundle.alu_src      <= ALU_FROM_ACC;
    bundle.pc_src       <= PC_INCREMENTED;
    bundle.cache_write  <= DISABLE;
    bundle.stack_write  <= DISABLE;
    bundle.head_write   <= DISABLE;
    bundle.loader_select<= DISABLE;
end

endmodule