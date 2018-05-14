import definitions::*;
module instruction_decode(
    input [8:0] instruction,
    output logic [2:0] address_select,
    output logic [2:0] alu_select
);

op_code op;
assign op = op_code'(instruction);

always_comb begin
    case(op)
        INC: begin
            address_select <= 0;
            alu_select <= 0;
        end
        DEC: begin
            address_select <= 0;
            alu_select <= 0;
        end
        PSH: begin
            address_select <= 2'b01;
            alu_select <= 2'b10;
        end
        POP: begin
            address_select <= 2'b01;
            alu_select <= 2'b10;
        end
        MVR: begin
            address_select <= 0;
            alu_select <= 2'b01;
        end
        MVL: begin
            address_select <= 0;
            alu_select <= 2'b01;
        end
        CBF: begin
            address_select <= 2'b10;
            alu_select <= 2'b11;
        end
        NOP: begin
            address_select <= 2'b10;
            alu_select <= 2'b11;
        end
        default: begin //NOP
            address_select <= 0;
            alu_select <= 0;
        end
    endcase
end

endmodule