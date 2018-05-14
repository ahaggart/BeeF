import definitions::*;
module acc_unit(
    input CONTROL acc_write,
    input ACC_SRC acc_src,
    input BYTE alu_out,
    input BYTE mem_out,

    output BYTE acc_out
);

BYTE acc_in;

two_one_mux alu_select(
    .selector(acc_src),
    .indata0(alu_out),
    .indata1(mem_out),

    .outdata(acc_in)
);

control_register acc(
    .in_data(acc_in),
    .enable(acc_write),

    .out_data(acc_out)
);

endmodule