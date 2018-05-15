import definitions::*;
module alu_unit(
    input ALU_OP alu_op,
    input ALU_SRC alu_src,
    input BYTE acc_out,
    input BYTE stack_out,
    input BYTE head_out,
    input BYTE cache_out,

    output BYTE alu_out
);

BYTE alu_in;

four_one_mux alu_select(
    .selector(alu_src),
    .indata1(acc_out),
    .indata2(stack_out),
    .indata3(head_out),
    .indata4(cache_out),
    .outdata(alu_in)
);

alu core(
	.alu_data_i(alu_in),
	.op_i(alu_op),
	.alu_result_o(alu_out)
);

endmodule