import definitions::*;
module top_level(
	input clk,
	      reset,
	output logic done
);

op_code instruction;

PROGRAM_COUNTER pc;

CONTROL acc_write, stack_write, head_write, branch_write;
CONTROL mem_write, mem_read, mem_force, pc_write, load_pc, store_pc;
CONTROL loader_select, loader_action;

MEM_OP mem_op;
MEM_SRC mem_src;
MEM_ADDR mem_addr;

ALU_OP alu_op;
ALU_SRC alu_src;

ACC_SRC acc_src;

PC_SRC pc_src;

BYTE alu_out, acc_out, stack_out, head_out, cache_out;
PROGRAM_COUNTER load_out;
BYTE save_out;

BYTE mem_in, mem_out;

STATE state_request, machine_state;

control_unit control(
	.clk(clk),
	.instruction(instruction),
	.state_in(machine_state),

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

	.state_out(state_request)
);

state_unit state(
	.clk(clk),
	.acc_out(acc_out),
	.state_in(state_request),

	.state_out(machine_state)
);

cache_unit cache(
	.alu_out(alu_out),
	.cache_write(cache_write),
	.loader_select(loader_select),
	.loader_action(loader_action),
	.pc(pc),

	.load_out(load_out),
	.save_out(save_out),
	.cache_out(cache_out)
);

fetch_unit fetch(
	.clk(clk),
	.pc_src(pc_src),
	.pc_loaded(cache_loaded),

	.pc(pc),
	.instruction(instruction)
);

mem_unit data_memory(
	.clk(clk),
	.mem_op(mem_op),
	.alu_out(alu_out),
	.acc_out(acc_out),
	.stack_out(stack_out),
	.head_out(head_out),
	.cache_out(cache_out),
	.save_out(save_out),

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

acc_unit acc(
	.acc_write(acc_write),
	.acc_src(acc_src),
	.alu_out(alu_out),
	.mem_out(mem_out),

	.acc_out(acc_out)
);
endmodule