import definitions::*;
module stack_ctrl(
	input clk,
	input [8:0] instruction,
	input [7:0] alu_result,
	output wire[8:0] stack_ptr
);

op_code op;
assign op = op_code'(instruction);
logic stack_enable;

single_reg stack(
	.clk		(clk	),
	.regReadEnable	(1'b1	),		//always reading
	.regWriteEnable	(stack_enable),
	.regWriteData	(alu_result),
	.regReadData	(stack_ptr)
);
 
always_comb
begin
	case(op)
		POP: stack_enable <= 1;
		PSH: stack_enable <= 1;
		default: stack_enable <= 0;
	endcase
end

endmodule 