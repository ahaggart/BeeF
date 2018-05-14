import definitions::*;
module cache_ctrl(
	input clk,
	input [8:0] instruction,
	input [7:0] alu_result,
	output wire [7:0] cache_ptr
);

op_code op;
assign op = op_code'(instruction);
logic cache_enable;

single_reg cache(
	.clk			(clk),
	.regReadEnable	(1'b1),		//always reading
	.regWriteEnable	(cache_enable),
	.regWriteData	(alu_result),
	.regReadData	(cache_ptr)
);

always_comb
begin
	case(op)
		CBF: cache_enable <= 1;
		CBB: cache_enable <= 1;
		default: cache_enable <= 0;
	endcase
end

endmodule
