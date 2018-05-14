import definitions::*;
module TestBench();

logic clk, reset, done;

op_code instruction;

logic [7:0] alu_result;
wire [15:0] pc;

// module pc_ctrl#(parameter PCWidth=16)(
// 	input clk,
// 	input [8:0] instruction,
// 	input [7:0] mem_read,
// 	output logic write_src,
// 	output [PCWidth-1:0] pc
// );

pc_ctrl pc_test(
	.clk(clk),
	.instruction(instruction),
	.mem_read(alu_result),
	.pc(pc)
);

initial begin
	clk = 0;
	reset = 0;
	done = 0;

	instruction = NOP;
	alu_result = 8'hBF;

	#10 instruction = CBF;
	#10 alu_result = 8'hEF;
	#10 instruction = NOP;
	#10 instruction = CBB;
	#10 instruction = NOP;
	#10 instruction = CBF;

end

always begin
	#5;
	clk = !clk;
end	

endmodule
