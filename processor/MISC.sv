// MISC -- TOP LEVEL MODULE
// Minimal Instruction Set Computer
import definitions::*;
module MISC(
    input logic reset,
    input logic clk,
    output logic done
);

op_code instruction;
logic acc_zero;
control_bundle_f controls;
control_bundle_s signals;
assign signals = control_bundle_s'(controls);

PROGRAM_COUNTER pc, pc_loaded, pc_incremented;
BYTE mem_out, alu_out, stack_out, cache_out, head_out, acc_out, save_out;

assign done = signals.halt & ~reset;

control_unit control(
    .clk(clk),
    .reset(reset),
    .instruction(instruction),
    .acc_zero(acc_zero),
    .controls(controls)
);

acc_unit accumulator(
    .clk(clk),
    .reset(reset),
    .acc_write(signals.acc_write),
    .acc_src(signals.acc_src),
    .alu_out(alu_out),
    .mem_out(mem_out),

    .acc_out(acc_out),
    .acc_zero(acc_zero)
);

alu_unit alu(
    .alu_op(signals.alu_op),
    .alu_src(signals.alu_src),
    .acc_out(acc_out),
    .stack_out(stack_out),
    .head_out(head_out),
    .cache_out(cache_out),

    .alu_out(alu_out)
);

fetch_unit fetch(
    .clk(clk),
    .reset(reset),
    .pc_src(signals.pc_src),
    .pc_write(signals.pc_write),
    .pc_loaded(pc_loaded),
    .pc(pc),
    .pc_incremented(pc_incremented),
    .instruction(instruction)
);

control_register head(
    .clk(clk),
    .reset(reset),
    .init(8'h0),
	.in_data(alu_out),
	.enable(signals.head_write),
	.out_data(head_out)
);

control_register stack(
    .clk(clk),
    .reset(reset),
    .init(8'd130),
	.in_data(alu_out),
	.enable(signals.stack_write),
	.out_data(stack_out)
);

mem_unit data_mem(
	.clk(clk),
	.mem_op(signals.mem_op),
	.alu_out(alu_out),
	.acc_out(acc_out),
	.stack_out(stack_out),
	.head_out(head_out),
	.cache_out(cache_out),
	.save_out(save_out),

	.mem_src(signals.mem_src),
	.mem_addr(signals.mem_addr),

	.mem_out(mem_out)
);

cache_unit cache(
    .clk(clk),
    .reset(reset),
    .alu_out(alu_out),
    .cache_write(signals.cache_write),
    .loader_select(signals.loader_select),
    .pc(pc_incremented),
    .mem_out(mem_out),

    .load_out(pc_loaded),
    .save_out(save_out),
    .cache_out(cache_out)
);


endmodule