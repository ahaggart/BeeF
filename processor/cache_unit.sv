import definitions::*;
module cache_unit(
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

assign load_out = {load_upper,mem_out};
assign pc_upper = pc[15:8];
assign pc_lower = pc[ 7:0];

CONTROL select_upper, select_lower;
assign select_upper = loader_select;
assign select_lower = CONTROL'(~select_upper);

control_register upper(
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