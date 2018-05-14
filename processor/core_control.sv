import definitions::*;
module core_control(
    input op_code instruction,

    output control_bundle_f controls
);

control_bundle_s bundle;
assign controls = control_bundle_f'(bundle);

always_comb begin
    case(instruction)
        INC: begin
            bundle.acc_write   <= ENABLE;
            bundle.stack_write <= DISABLE;
            bundle.head_write  <= DISABLE;
            bundle.cache_write <= DISABLE;
            bundle.mem_op      <= MEM_WRITE;
            bundle.alu_op      <= ALU_INC;

            bundle.acc_src     <= ACC_FROM_ALU;
            bundle.mem_src     <= MEM_FROM_ALU;
            bundle.mem_addr    <= ADDR_FROM_HEAD;
        end
        DEC: begin
            bundle.acc_write   <= ENABLE;
            bundle.stack_write <= DISABLE;
            bundle.head_write  <= DISABLE;
            bundle.cache_write <= DISABLE;
            bundle.mem_op      <= MEM_WRITE;
            bundle.alu_op      <= ALU_DEC;

            bundle.acc_src     <= ACC_FROM_ALU;
            bundle.mem_src     <= MEM_FROM_ALU;
            bundle.mem_addr    <= ADDR_FROM_HEAD;
        end
        PSH: begin
            bundle.acc_write   <= DISABLE;
            bundle.stack_write <= ENABLE;
            bundle.head_write  <= DISABLE;
            bundle.cache_write <= DISABLE;
            bundle.mem_op      <= MEM_WRITE;
            bundle.alu_op      <= ALU_INC;

            bundle.acc_src     <= ACC_FROM_ALU;
            bundle.mem_src     <= MEM_FROM_ACC;
            bundle.mem_addr    <= ADDR_FROM_HEAD;
        end
        POP: begin
            bundle.acc_write   <= ENABLE;
            bundle.stack_write <= ENABLE;
            bundle.head_write  <= DISABLE;
            bundle.cache_write <= DISABLE;
            bundle.mem_op      <= MEM_READ;
            bundle.alu_op      <= ALU_DEC;

            bundle.acc_src     <= ACC_FROM_MEM;
            bundle.mem_src     <= MEM_FROM_ALU;
            bundle.mem_addr    <= ADDR_FROM_STACK;
        end
        MVR: begin
            bundle.acc_write   <= ENABLE;
            bundle.stack_write <= DISABLE;
            bundle.head_write  <= ENABLE;
            bundle.cache_write <= DISABLE;
            bundle.mem_op      <= MEM_READ;
            bundle.alu_op      <= ALU_INC;

            bundle.acc_src     <= ACC_FROM_MEM;
            bundle.mem_src     <= MEM_FROM_ALU; //dont care
            bundle.mem_addr    <= ADDR_FROM_ALU;
        end
        MVL: begin
            bundle.acc_write   <= ENABLE;
            bundle.stack_write <= DISABLE;
            bundle.head_write  <= ENABLE;
            bundle.cache_write <= DISABLE;
            bundle.mem_op      <= MEM_READ;
            bundle.alu_op      <= ALU_DEC;

            bundle.acc_src     <= ACC_FROM_MEM;
            bundle.mem_src     <= MEM_FROM_ALU; //dont care
            bundle.mem_addr    <= ADDR_FROM_ALU;
        end
        CBF: begin
            bundle.acc_write   <= DISABLE;
            bundle.stack_write <= DISABLE;
            bundle.head_write  <= DISABLE;
            bundle.cache_write <= ENABLE;
            bundle.mem_op      <= MEM_WRITE;
            bundle.alu_op      <= ALU_INC;

            bundle.acc_src     <= ACC_FROM_MEM; //dont care
            bundle.mem_src     <= MEM_FROM_PC; //dont care
            bundle.mem_addr    <= ADDR_FROM_CACHE;
        end
        CBB: begin
            bundle.acc_write   <= DISABLE;
            bundle.stack_write <= DISABLE;
            bundle.head_write  <= DISABLE;
            bundle.cache_write <= ENABLE;
            bundle.mem_op      <= MEM_READ;
            bundle.alu_op      <= ALU_DEC;

            bundle.acc_src     <= ACC_FROM_MEM; //dont care
            bundle.mem_src     <= MEM_FROM_PC; //dont care
            bundle.mem_addr    <= ADDR_FROM_CACHE;
        end
        default: begin //NOP
            bundle.acc_write   <= DISABLE;
            bundle.stack_write <= DISABLE;
            bundle.head_write  <= DISABLE;
            bundle.cache_write <= DISABLE;
            bundle.mem_op      <= MEM_READ;
            bundle.alu_op      <= ALU_INC;

            bundle.acc_src     <= ACC_FROM_ALU;
            bundle.mem_src     <= MEM_FROM_ACC;
            bundle.mem_addr    <= ADDR_FROM_HEAD;
        end
    endcase
    bundle.loader_select <= DISABLE; //always load the lower half of the PC
end

endmodule