import definitions::*;
module branch_control(
    input op_code instruction,

    output control_bundle_f controls
);

control_bundle_s bundle;
assign controls = control_bundle_f'(bundle);

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