import definitions::*;
module store_unit(
    input clk,
    input pc_store,
    input PROGRAM_COUNTER pc,

    output BYTE mem_in
);

logic store_state;
PC_HALF upper,lower;
assign upper = pc[15:8];
assign lower = pc[7:0];

always_ff @ (posedge clk) begin
    if(pc_store) begin
        if(store_state) mem_in <= upper;
        else begin 
            mem_in <= lower;
            store_state <= 1;
        end
    end else store_state <= 0;
end
endmodule