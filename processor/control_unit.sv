import definitions::*;
module control_unit(
    input clk,
    input op_code instruction,
    output CONTROL acc_write,
    output ACC_SRC acc_src,
    output CONTROL stack_write,
    output CONTROL head_write,
    output CONTROL cache_write,
    output CONTROL pc_write,
    output PC_SRC pc_src,
    output MEM_OP mem_op,
    output MEM_ADDR mem_addr,
    output MEM_SRC mem_src,
    output ALU_OP alu_op,

    output CONTROL load_pc,
    output CONTROL store_pc,
    output CONTROL bubble
);

wire stalling;
ALU_OP      stall_alu_op;
MEM_ADDR    stall_mem_addr;
MEM_OP      stall_mem_op;
MEM_SRC     stall_mem_src;

CONTROL stall_enter;
STALL_STATE stall_type;

stall_unit stall(
    .clk(clk),
    .instruction(instruction),
    .enter(stall_enter),
    .starting(stall_type),
    .alu_out(alu_out),

    .alu_in(alu_in),

    .alu_op(stall_alu_op),
    .mem_op(stall_mem_op),
    .mem_addr(stall_mem_addr),
    .mem_src(stall_mem_src),

    .stalling(stalling)
);

always @ (posedge clk) begin
    if(stalling) begin
            acc_write   <= DISABLE;
            stack_write <= DISABLE;
            head_write  <= DISABLE;
            cache_write <= DISABLE;
            acc_src     <= ACC_FROM_ALU;

            mem_op      <= stall_mem_op;
            alu_op      <= stall_alu_op;
            mem_addr    <= stall_mem_addr;
            mem_src     <= stall_mem_src;
    end
    else begin
    case(instruction)
        INC: begin
            acc_write   <= ENABLE;
            stack_write <= DISABLE;
            head_write  <= DISABLE;
            cache_write <= DISABLE;
            mem_op      <= MEM_WRITE;
            alu_op      <= ALU_INC;

            acc_src     <= ACC_FROM_ALU;
            mem_src     <= MEM_FROM_ALU;
            mem_addr    <= ADDR_FROM_HEAD;
        end
        DEC: begin
            acc_write   <= ENABLE;
            stack_write <= DISABLE;
            head_write  <= DISABLE;
            cache_write <= DISABLE;
            mem_op      <= MEM_WRITE;
            alu_op      <= ALU_DEC;

            acc_src     <= ACC_FROM_ALU;
            mem_src     <= MEM_FROM_ALU;
            mem_addr    <= ADDR_FROM_HEAD;
        end
        PSH: begin
            acc_write   <= DISABLE;
            stack_write <= ENABLE;
            head_write  <= DISABLE;
            cache_write <= DISABLE;
            mem_op      <= MEM_WRITE;
            alu_op      <= ALU_INC;

            acc_src     <= ACC_FROM_ALU;
            mem_src     <= MEM_FROM_ACC;
            mem_addr    <= ADDR_FROM_HEAD;
        end
        POP: begin
            acc_write   <= ENABLE;
            stack_write <= ENABLE;
            head_write  <= DISABLE;
            cache_write <= DISABLE;
            mem_op      <= MEM_READ;
            alu_op      <= ALU_DEC;

            acc_src     <= ACC_FROM_MEM;
            mem_src     <= MEM_FROM_ALU;
            mem_addr    <= ADDR_FROM_STACK;
        end
        MVR: begin
            acc_write   <= ENABLE;
            stack_write <= DISABLE;
            head_write  <= ENABLE;
            cache_write <= DISABLE;
            mem_op      <= MEM_READ;
            alu_op      <= ALU_INC;

            acc_src     <= ACC_FROM_MEM;
            mem_src     <= MEM_FROM_ALU; //dont care
            mem_addr    <= ADDR_FROM_ALU;
        end
        MVL: begin
            acc_write   <= ENABLE;
            stack_write <= DISABLE;
            head_write  <= ENABLE;
            cache_write <= DISABLE;
            mem_op      <= MEM_READ;
            alu_op      <= ALU_DEC;

            acc_src     <= ACC_FROM_MEM;
            mem_src     <= MEM_FROM_ALU; //dont care
            mem_addr    <= ADDR_FROM_ALU;
        end
        CBF: begin
            acc_write   <= DISABLE;
            stack_write <= DISABLE;
            head_write  <= DISABLE;
            cache_write <= ENABLE;
            mem_op      <= MEM_WRITE;
            alu_op      <= ALU_INC;

            acc_src     <= ACC_FROM_MEM; //dont care
            mem_src     <= MEM_FROM_PC; //dont care
            mem_addr    <= ADDR_FROM_CACHE;
        end
        CBB: begin
            acc_write   <= DISABLE;
            stack_write <= DISABLE;
            head_write  <= DISABLE;
            cache_write <= ENABLE;
            mem_op      <= MEM_READ;
            alu_op      <= ALU_DEC;

            acc_src     <= ACC_FROM_MEM; //dont care
            mem_src     <= MEM_FROM_PC; //dont care
            mem_addr    <= ADDR_FROM_CACHE;
        end
        default: begin //NOP
            acc_write   <= DISABLE;
            stack_write <= DISABLE;
            head_write  <= DISABLE;
            cache_write <= DISABLE;
            mem_op      <= MEM_READ;
            alu_op      <= ALU_INC;

            acc_src     <= ACC_FROM_ALU;
            mem_src     <= MEM_FROM_ACC;
            mem_addr    <= ADDR_FROM_HEAD;
        end
    endcase
    end
end

endmodule