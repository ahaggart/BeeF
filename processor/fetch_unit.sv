import definitions::*;
module fetch_unit(
    input clk,
    input reset,
    input pc_src,
    input CONTROL pc_write,
    input PROGRAM_COUNTER pc_loaded,

    output PROGRAM_COUNTER pc,
    output op_code instruction
);

PROGRAM_COUNTER pc_incremented,pc_selected,new_pc;
op_code at_pc;

INSTRUCTION _instruction;
assign instruction = op_code'(_instruction);

InstROM instruction_mem(       
    .InstAddress (pc    ),		
   	.InstOut     (at_pc )    	//read result
);

two_one_mux#(.width($bits(op_code))) instr_mux(
	.selector   (pc_write),
	.indata0    (9'b0),
	.indata1    (at_pc),
	.outdata    (_instruction)
);

alu#(.width($bits(PROGRAM_COUNTER))) pc_alu(
	.alu_data_i	    (pc	),
	.op_i		    (ALU_INC),		//always adding
	.alu_result_o   (pc_incremented)
);

two_one_mux#(.width($bits(PROGRAM_COUNTER))) pc_mux(
	.selector   (pc_src),
	.indata0    (pc_incremented),
	.indata1    (pc_loaded),
	.outdata    (pc_selected)
);

control_register#(.width($bits(PROGRAM_COUNTER))) program_counter(
    .clk(clk),
    .reset(reset),
    .in_data(pc_selected),
    .enable(pc_write),
    .out_data(pc)
);

// two_one_mux#(.width($bits(PROGRAM_COUNTER))) reset_mux(
// 	.selector   (reset),
// 	.indata0    (pc_selected),
// 	.indata1    (16'b0),
// 	.outdata    (new_pc)
// );

endmodule