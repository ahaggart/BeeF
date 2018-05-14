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

assign load_out = {load_upper,load_lower};
assign pc_upper = pc[15:8];
assign pc_lower = pc[ 7:0];

CONTROL select_upper, select_lower;
assign select_upper = loader_select;
assign select_lower = CONTROL'(~select_upper);

control_register upper(
	.in_data(mem_out),
	.enable(select_upper),
	.out_data(pc_upper)
);

control_register lower(
	.in_data(mem_out),
	.enable(select_lower),
	.out_data(pc_lower)
);

control_register cache(
	.in_data(alu_out),
	.enable(cache_write),
	.out_data(cache_out)
);

two_one_mux save(
    .selector(loader_select),
    .indata0(pc_lower),
    .indata1(pc_upper),
    .outdata(save_out)
);

endmodule