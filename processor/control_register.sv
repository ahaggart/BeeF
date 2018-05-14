import definitions::*;
module control_register(
    input clk,
    input BYTE in_data,
    input CONTROL enable,

    output BYTE out_data
);

always_ff @ (posedge clk)
    if(enable) out_data <= in_data;
endmodule