import definitions::*;
module fetch_unit(
    input clk,
    input pc_src,
    input PROGRAM_COUNTER pc_loaded,

    output PROGRAM_COUNTER pc,
    output op_code instruction
);

PROGRAM_COUNTER pc_selected;

InstROM instruction_mem(       
    .InstAddress (pc ),		
   	.InstOut     (instruction )    	//read result
);

alu#(.width(16)) pc_alu(
	.alu_data_i	    (pc	),
	.op_i		    (1'b0	),		//always adding
	.alu_result_o   (pc_incremented)
);

two_one_mux#(.width(16)) pc_mux(
	.selector   (pc_src),
	.indata0    (pc_incremented),
	.indata1    (pc_loaded),
	.outdata    (pc_selected)
);

always_ff @ (posedge clk) begin
    pc <= pc_selected;
end

endmodule