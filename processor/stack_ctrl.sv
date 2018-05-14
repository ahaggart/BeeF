import definitions::*;
module stack_ctrl(
	input [8:0] instruction,
	output logic write_enable
);

op_code op;
assign op = op_code'(instruction);
 
always_comb
begin
	case(op)
		POP: write_enable <= 1;
		PSH: write_enable <= 1;
		default: write_enable <= 0;
	endcase
end

endmodule 