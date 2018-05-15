import definitions::*;
module cache_unit(
    input clk,
    input reset,
	input BYTE alu_out,
	input CONTROL cache_write,
    input CONTROL loader_select,
    input PROGRAM_COUNTER pc,
    input BYTE mem_out,

    output PROGRAM_COUNTER load_out,
    output BYTE save_out,
	output BYTE cache_out
);

BYTE pc_upper, pc_lower;
BYTE load_upper, load_lower;

assign load_out = {mem_out,load_upper};
assign pc_upper = pc[15:8];
assign pc_lower = pc[ 7:0];

CONTROL select_upper, select_lower;
assign select_upper = CONTROL'(~loader_select);
// assign select_lower = CONTROL'(~select_upper);

BYTE byte_zero, cache_start;

assign byte_zero = BYTE'(0);
assign cache_start = BYTE'(8'd192);

BYTE cached_lower;

control_register upper(
    .clk(clk),
    .reset(reset),
    .init(byte_zero),
	.in_data(mem_out),
	.enable(select_upper),
	.out_data(load_upper)
);

// control_register lower(
// 	.in_data(mem_out),
// 	.enable(select_lower),
// 	.out_data(load_lower)
// );

control_register cache(
    .clk(clk),
    .reset(reset),
    .init(cache_start),
	.in_data(alu_out),
	.enable(cache_write),
	.out_data(cache_out)
);

// control_register save_upper(
//     .in_data(pc_upper),
//     .enable(cache_write), 
//     .out_data(cached_upper)
// );

control_register save_lower(
    .clk(clk),
    .reset(reset),
    .init(byte_zero),
    .in_data(pc_lower),
    .enable(cache_write), //save half of current pc whenever the cache unit is used
    .out_data(cached_lower)
);

two_one_mux save(
    .selector(loader_select),
    .indata0(pc_upper),
    .indata1(cached_lower),
    .outdata(save_out)
);

endmodule