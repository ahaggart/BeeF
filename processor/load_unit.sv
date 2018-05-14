import definitions::*;
module load_unit(
    input clk,
    input pc_load,
    input BYTE mem_out,

    output PROGRAM_COUNTER pc_loaded
);

logic load_state;
PC_HALF upper,lower;
assign pc_loaded = {upper,lower};

always_ff @ (posedge clk) begin
    if(pc_load) begin
        if(load_state) upper <= mem_out;
        else begin 
            lower <= mem_out;
            load_state <= 1;
        end
    end else load_state <= 0;
end
endmodule