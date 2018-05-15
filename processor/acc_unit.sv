import definitions::*;
module acc_unit(
    input clk,
    input reset,
    input CONTROL acc_write,
    input ACC_SRC acc_src,
    input BYTE alu_out,
    input BYTE mem_out,

    output BYTE acc_out,
    output logic acc_zero
);

BYTE acc_in;
assign acc_zero = &(~acc_out);

four_one_mux acc_select(
    .selector(acc_src),
    .indata1(8'b0     ),
    .indata2(alu_out),
    .indata3(mem_out),
    .indata4(8'b1),
    .outdata(acc_in)
);

control_register acc(
    .clk(clk),
    .reset(reset),
    .in_data(acc_in),
    .enable(acc_write),
    .out_data(acc_out)
);

endmodule