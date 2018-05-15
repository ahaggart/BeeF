import definitions::*;
module control_register#(parameter width=8)(
    input clk,
    input reset,
    input logic [width-1:0] in_data,
    input CONTROL enable,

    output logic [width-1:0] out_data
);

always_ff @ (posedge clk)
    if(reset) out_data <= 0;
    else if(enable) out_data <= in_data;
endmodule