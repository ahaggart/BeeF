import definitions::*;
module top_level(
	input clk,
	      reset,
	output logic done
);

op_code instruction;

CONTROL acc_write, stack_write, head_write, branch_write;
CONTROL mem_write, mem_read, mem_force, pc_write, load_pc, store_pc;
CONTROL bubble;

MEM_OP mem_op;
MEM_SRC mem_src;
MEM_ADDR mem_addr;

ALU_OP alu_op;
ALU_SRC alu_src;

ACC_SRC acc_src;

PC_SRC pc_src;

BYTE alu_out, acc_out, stack_out, head_out, cache_out, loader_out;

BYTE mem_in, mem_out;

control_unit control(
	.clk(clk),
	.instruction(instruction),

	.acc_write(acc_write),
	.acc_src(acc_src),
	.stack_write(stack_write),
	.head_write(head_write),
	.cache_write(cache_write),
	.pc_write(pc_write),
	.pc_src(pc_src),
	.mem_op(mem_op),
	.mem_addr(mem_addr),
	.mem_src(mem_src),
	.alu_op(alu_op),

	.mem_force(mem_force),
	.load_pc(load_pc),
	.store_pc(store_pc),
	.bubble(bubble)
);

fetch_unit fetch(
	.clk(clk),
	.pc_src(pc_src),
	.bubble(bubble),
	.pc_load(load_pc),
	.pc_store(store_pc),
	.mem_out(mem_out),

	.mem_in(loader_out),
	.instruction(instruction)
);

mem_unit data_memory(
	.mem_op(mem_op),
	.mem_force(mem_force),
	.alu_out(alu_out),
	.acc_out(acc_out),
	.stack_out(stack_out),
	.head_out(head_out),
	.cache_out(cache_out),
	.loader_out(loader_out),

	.mem_out(mem_out)
);

alu_unit alu(
	.alu_op(alu_op),
	.alu_src(alu_src),
	.acc_out(acc_out),
	.stack_out(stack_out),
	.head_out(head_out),
	.cache_out(cache_out),

	.alu_out(alu_out)
);

control_register stack(
	.in_data(alu_out),
	.enable(stack_write),
	.out_data(stack_out)
);

control_register head(
	.in_data(alu_out),
	.enable(head_write),
	.out_data(head_out)
);

control_register cache(
	.in_data(alu_out),
	.enable(cache_write),
	.out_data(cache_out)
);

acc_unit acc(
	.acc_write(acc_write),
	.acc_src(acc_src),
	.alu_out(alu_out),
	.mem_out(mem_out),

	.acc_out(acc_out)
);
endmodule