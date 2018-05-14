import definitions::*;
module cache_ctrl(
	input [8:0] instruction,
	output logic write_enable
);

op_code op;
assign op = op_code'(instruction);
always_comb
begin

	case(op)
		CBF: write_enable <= 1;
		CBB: write_enable <= 1;
		default: write_enable <= 0;
	endcase
end

endmodule
