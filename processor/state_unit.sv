import definitions::*;
module state_unit(
    input clk,
    input BYTE acc_out,
    input STATE state_in,

    output STATE state_out
);

logic acc_zero;
assign acc_zero = &acc_out;

always_ff @ (posedge clk) begin
    case(state_in)
        default:    state_out <= state_in;
    endcase
end
endmodule