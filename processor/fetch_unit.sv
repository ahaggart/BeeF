import definitions::*;
module fetch_unit(
    input clk,
    input pc_src,
    input bubble,
    input pc_load,
    input pc_store,
    input BYTE mem_out,

    output BYTE mem_in,
    output op_code instruction
);

PROGRAM_COUNTER pc, pc_loaded,pc_selected;
op_code at_pc;

InstROM instruction_mem(       
    .InstAddress (pc ),		
   	.InstOut     (at_pc )    	//read result
);

two_one_mux#(.width(9)) inst_mux(
	.selector   (bubble),
	.indata0    (at_pc),
	.indata1    (0),
	.outdata    (instruction)
);

alu#(.width(16)) pc_alu(
	.alu_data_i	    (pc	),
	.op_i		    (1'b0	),		//always adding
	.alu_result_o   (pc_incremented)
);

two_one_mux#(.width(16)) pc_mux(
	.selector   (pc_src),
	.indata0    (pc),
	.indata1    (pc_loaded),
	.outdata    (instruction)
);

load_unit loader(
    .clk(clk),
    .pc_load(pc_load),
    .mem_out(mem_out),
    .pc_loaded(pc_loaded)
);

store_unit storer(
    .clk(clk),
    .pc_store(pc_store),
    .pc(pc),
    
    .mem_in(mem_in)
);

always_ff @ (posedge clk) begin
    pc <= pc_selected;
end

endmodule