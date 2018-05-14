import definitions::*;
module pc_ctrl(
	input clk,
	input [8:0] instruction,
	output logic write_src,
	output logic write_enable,
	output reg bubble
);

op_code op;
assign op = op_code'(instruction);
assign write_enable = ~bubble;


always_comb
begin
	case(op)
		CBB: write_src <= 1;
		default: write_src <= 0;
	endcase
end

always_ff @ (posedge clk)
begin
	if(bubble) 	bubble <= 0;
	else		bubble <= 1;
end

endmodule 