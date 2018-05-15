import definitions::*;
module control_register#(parameter width=8)(
    input clk,
    input logic [width-1:0] in_data,
    input CONTROL enable,

    output logic [width-1:0] out_data
);

always_ff @ (posedge clk)
    if(enable) out_data <= in_data;
endmodule