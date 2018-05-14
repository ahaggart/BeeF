module instruction_fetch(
    input clk,
    input delay,
    input delayed_op,
    input [15:0] pc,
    input searching,
    output wire [8:0] instruction,
    output logic delay_op,
    output logic delayed
);

wire [8:0] instruction_at_pc;
logic nop;
assign nop = delayed | searching;

InstROM instruction_mem(       
    .InstAddress (pc ),		
   	.InstOut     (instruction_at_pc )    	//read result
);

two_one_mux#(.width(9)) inst_mux(
	.selector(nop),
	.indata0(instruction_at_pc),
	.indata1(0),
	.outdata(instruction)
);

always_ff @ (posedge clk) begin
    if(delay) begin 
        delay_op <= delayed_op;
        delayed <= 1'b1;
    end
    if(delayed) begin
        delayed <= 0;
    end
end

endmodule