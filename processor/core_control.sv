import definitions::*;
module core_control(
    input op_code instruction,
    input logic acc_zero,
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
            bundle.alu_src     <= ALU_FROM_ACC;

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
            bundle.alu_src     <= ALU_FROM_ACC;

            bundle.acc_src     <= ACC_FROM_ALU;
            bundle.mem_src     <= MEM_FROM_ALU;
            bundle.mem_addr    <= ADDR_FROM_HEAD;
        end
        PSH: begin //convention: stack pointer points to free memory
            bundle.acc_write   <= DISABLE;
            bundle.stack_write <= ENABLE;
            bundle.head_write  <= DISABLE;
            bundle.cache_write <= DISABLE;
            bundle.mem_op      <= MEM_WRITE;
            bundle.alu_op      <= ALU_INC;
            bundle.alu_src     <= ALU_FROM_STACK;

            bundle.acc_src     <= ACC_FROM_ALU;
            bundle.mem_src     <= MEM_FROM_ACC;
            bundle.mem_addr    <= ADDR_FROM_STACK;
        end
        POP: begin //we must use the decremented stack pointer to fetch value
            bundle.acc_write   <= ENABLE;
            bundle.stack_write <= ENABLE;
            bundle.head_write  <= DISABLE;
            bundle.cache_write <= DISABLE;
            bundle.mem_op      <= MEM_READ;
            bundle.alu_op      <= ALU_DEC;
            bundle.alu_src     <= ALU_FROM_STACK;

            bundle.acc_src     <= ACC_FROM_MEM;
            bundle.mem_src     <= MEM_FROM_ALU; //dont care
            bundle.mem_addr    <= ADDR_FROM_ALU;
        end
        MVR: begin
            bundle.acc_write   <= ENABLE;
            bundle.stack_write <= DISABLE;
            bundle.head_write  <= ENABLE;
            bundle.cache_write <= DISABLE;
            bundle.mem_op      <= MEM_READ;
            bundle.alu_op      <= ALU_INC;
            bundle.alu_src     <= ALU_FROM_HEAD;

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
            bundle.alu_src     <= ALU_FROM_HEAD;

            bundle.acc_src     <= ACC_FROM_MEM;
            bundle.mem_src     <= MEM_FROM_ALU; //dont care
            bundle.mem_addr    <= ADDR_FROM_ALU;
        end
        CBF: begin
            if(acc_zero) begin 
                bundle.acc_write   <= ENABLE;
            end else begin
                bundle.acc_write   <= DISABLE;
            end

            bundle.stack_write <= DISABLE;
            bundle.head_write  <= DISABLE;
            bundle.cache_write <= ENABLE;
            bundle.mem_op      <= MEM_WRITE;
            bundle.alu_op      <= ALU_INC;
            bundle.alu_src     <= ALU_FROM_CACHE;

            bundle.acc_src     <= ACC_ONE; //load a 1 directly to avoid ALU
            bundle.mem_src     <= MEM_FROM_PC; //use this cycle's MEM and ALU for cache
            bundle.mem_addr    <= ADDR_FROM_ALU;
        end
        CBB: begin
            if(acc_zero) begin 
                bundle.cache_write <= DISABLE;
            end else begin
                bundle.cache_write <= DISABLE;
            end

            bundle.acc_write   <= DISABLE;
            bundle.stack_write <= DISABLE;
            bundle.head_write  <= DISABLE;
            bundle.mem_op      <= MEM_READ;
            bundle.alu_op      <= ALU_DEC;
            bundle.alu_src     <= ALU_FROM_CACHE;

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
            bundle.alu_src     <= ALU_FROM_ACC;

            bundle.acc_src     <= ACC_FROM_ALU;
            bundle.mem_src     <= MEM_FROM_ACC;
            bundle.mem_addr    <= ADDR_FROM_HEAD;
        end
    endcase
    bundle.loader_select <= DISABLE; //always load the lower half of the PC
    bundle.pc_src <= PC_INCREMENTED; //no branch execution 
    case(instruction) //state logic
        CBF: begin
            if(acc_zero) begin //not taken
                bundle.state <= CORE_S;
                bundle.pc_write <= ENABLE;
            end else begin //taken    
                bundle.state <= STALL_S;
                bundle.pc_write <= DISABLE;
            end
        end
        CBB: begin 
            if(acc_zero) begin //not taken
                bundle.state <= CORE_S;
                bundle.pc_write <= ENABLE;
            end else begin //taken    
                bundle.state <= STALL_S;
                bundle.pc_write <= DISABLE;
            end
        end
        POP: begin
            bundle.state <= STALL_S;
            bundle.pc_write <= DISABLE;
        end
        default: begin 
            bundle.state <= CORE_S;
            bundle.pc_write <= ENABLE;
        end
    endcase
end

endmodule