import definitions::*;
module MemTestBench();

logic clk, reset, done;

op_code instruction;

MEM_OP mem_op;
BYTE alu_out, acc_out, stack_out, head_out, cache_out, save_out;
MEM_SRC mem_src;
MEM_ADDR mem_addr;
BYTE mem_out;

// module mem_unit(
// 	input clk,
// 	input MEM_OP mem_op,
// 	input BYTE alu_out,
// 	input BYTE acc_out,
// 	input BYTE stack_out,
// 	input BYTE head_out,
// 	input BYTE cache_out,
// 	input BYTE save_out,

// 	input MEM_SRC mem_src,
// 	input MEM_ADDR mem_addr,

// 	output BYTE mem_out
// );

mem_unit mem_test(
	.clk(clk),
	.mem_op(mem_op),
	.alu_out(alu_out),
	.acc_out(acc_out),
	.stack_out(stack_out),
	.head_out(head_out),
	.cache_out(cache_out),
	.save_out(save_out),

	.mem_src(mem_src),
	.mem_addr(mem_addr),

	.mem_out(mem_out)
);

initial begin
	clk = 0;
	reset = 0;
	done = 0;

	instruction = NOP;
	acc_out		= 8'hA0;
	alu_out 	= 8'hA1;
	stack_out 	= 8'hA2;
	head_out 	= 8'hA3;
	cache_out 	= 8'hA4;
	save_out 	= 8'hA5;

	mem_op		= MEM_WRITE;
	mem_src 	= MEM_FROM_ACC;
	mem_addr 	= ADDR_FROM_HEAD;

	#15 mem_op = MEM_READ;
	#15 mem_op = MEM_WRITE;
		mem_src = MEM_FROM_ALU;
	#15 mem_op = MEM_READ;
	#15 mem_addr= ADDR_FROM_STACK;
	#15 mem_op  = MEM_WRITE;
		mem_src = MEM_FROM_PC;
	#15 mem_op  = MEM_READ;
	#15 mem_addr= ADDR_FROM_HEAD;
end

always begin
	#5;
	clk = !clk;
end	

endmodule
