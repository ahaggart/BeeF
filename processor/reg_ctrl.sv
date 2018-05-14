
import definitions::*;
module reg_ctrl(
	input clk,
	input [8:0] instruction,
	input [7:0] alu_result,
	input [7:0] mem_value,
	output [7:0] reg_value
);

op_code op;
assign op = op_code'(instruction);

logic reg_enable;
logic reg_src;
wire [7:0] reg_input;

two_one_mux working_src_mux(
	.selector	(reg_src),
	.indata0	(alu_result_o),
	.indata1	(mem_value),
	.outdata	(reg_input)
);

single_reg working(
	.clk		(clk	),
	.regReadEnable	(1'b1	),		//always reading
	.regWriteEnable	(reg_enable),
	.regWriteData	(reg_input),
	.regReadData	(reg_value)
);
 
always_comb
begin
	case(op)
		POP: reg_src <= 1;
		MVR: reg_src <= 1;
		MVL: reg_src <= 1;
		default: reg_src <= 0;
	endcase
	case(op)
		POP: reg_enable <= 1;
		MVR: reg_enable <= 1;
		MVL: reg_enable <= 1;
		INC: reg_enable <= 1;
		DEC: reg_enable <= 1;
		default: reg_enable <= 0;
	endcase
end

 

endmodule 
