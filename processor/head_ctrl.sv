import definitions::*;
module head_ctrl(
	input clk,
	input [8:0] instruction,
	input [7:0] alu_result,
	output wire [7:0] head_ptr
);


op_code op;
assign op = op_code'(instruction);
logic head_enable;

single_reg head(
	.clk		(clk	),
	.regReadEnable	(1'b1	),		//always reading
	.regWriteEnable	(head_enable),
	.regWriteData	(alu_result),
	.regReadData	(head_ptr)
);
 
always_comb
begin
	case(op)
		MVR: head_enable <= 1;
		MVL: head_enable <= 1;
		default: head_enable <= 0;
	endcase
end  
endmodule 