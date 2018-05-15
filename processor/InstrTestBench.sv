import definitions::*;
module InstrTestBench();

logic clk, reset, done;

op_code instruction;
PROGRAM_COUNTER pc, pc_loaded;

PC_SRC pc_src;
CONTROL pc_write;

// module fetch_unit(
//     input clk,
//     input pc_src,
//     input CONTROL pc_write,
//     input PROGRAM_COUNTER pc_loaded,

//     output PROGRAM_COUNTER pc,
//     output op_code instruction
// );

fetch_unit fetch_test(
    .clk(clk),
    .reset(reset),
    .pc_src(pc_src),
    .pc_write(pc_write),
    .pc_loaded(pc_loaded),
    .pc(pc),
    .instruction(instruction)
);

initial begin
	clk = 0;
	reset = 1;
	done = 0;

	pc_src = PC_INCREMENTED;
    pc_loaded = 16'hBEEF;
    pc_write = ENABLE;

    #10 reset = 0;
    #50;
    #15 pc_src = PC_LOADED;
    #50 pc_write = DISABLE;
    #50 pc_write = ENABLE;
    #15 pc_src = PC_INCREMENTED;
end

always begin
	#5;
	clk = !clk;
end	

endmodule
