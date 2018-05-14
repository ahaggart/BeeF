import definitions::*;
module stall_unit(
    input clk,
    input op_code instruction,
    input CONTROL enter,
    input STALL_STATE starting,
    input BYTE alu_out,

    output BYTE alu_in,

    output ALU_OP alu_op,
    output MEM_OP mem_op,
    output MEM_ADDR mem_addr,
    output MEM_SRC mem_src,

    output CONTROL stalling
);

STALL_STATE stall_state;

BYTE counter_value,counter_select;
CONTROL counter_write, counter_reset;

two_one_mux nest_select(
    .selector(counter_reset),
    .indata0(alu_out),
    .indata1(0),
    .outdata(counter_select)
);

control_register nest_counter(
    .in_data(counter_select),
    .enable(1'b1),
    .out_data(counter_value)
);

assign alu_in = counter_value;

always_ff @ (posedge clk) begin
    if(enter) begin 
        stall_state <= starting;
        stalling <= ENABLE;
        counter_write <= ENABLE;
        counter_reset <= ENABLE;
    end
    else begin
        counter_reset <= DISABLE;
        case(stall_state)
            WRITE_PC: begin
                stalling <= DISABLE;
            end
            READ_PC: begin
                stalling <= DISABLE;
            end
            WRITE_POP:begin
                stalling <= DISABLE;
            end
            default: begin
                if(counter_value)   stalling <= ENABLE;
                else                stalling <= DISABLE;
            end
        endcase
        case(stall_state)
            SEARCH_PC: begin
                case(instruction)
                    CBF: begin 
                        alu_op <= ALU_INC; 
                        counter_write <= ENABLE;
                    end
                    CBB: begin 
                        alu_op <= ALU_DEC; 
                        counter_write <= ENABLE;
                    end
                    default: begin
                        alu_op <= ALU_INC;
                        counter_write <= DISABLE;
                    end
                endcase
            end
            default: begin
                alu_op <= ALU_INC;
                counter_write <= DISABLE;
            end
        endcase
    end
end

endmodule