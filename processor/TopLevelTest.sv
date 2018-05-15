import definitions::*;
module TopLevelTest();

logic clk, reset, done;

op_code instruction;
logic acc_zero;
control_bundle_f controls;
control_bundle_s signals;
assign signals = control_bundle_s'(controls);

PROGRAM_COUNTER pc, pc_loaded;
BYTE mem_out, alu_out, stack_out, cache_out, head_out, acc_out, save_out;

core_control core(
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
    .instruction(instruction)
);

control_register head(
    .clk(clk),
    .reset(reset),
	.in_data(alu_out),
	.enable(signals.head_write),
	.out_data(head_out)
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


initial begin
	clk = 0;
	reset = 1;
	done = 0;

    pc_loaded   = 16'd5;
    stack_out   = 8'b1;
    cache_out   = 8'b11;

    #10 reset = 0;
end

always begin
	#5;
	clk = !clk;
end	

endmodule
