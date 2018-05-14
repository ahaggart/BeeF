module single_reg (
	input clk,
	input regReadEnable,
	input regWriteEnable,
	input [7:0] regWriteData,
	output logic [7:0] regReadData
);

//declare memory/reg file array itself
logic [7:0] RF [1]; //RF [NUM REGS]

assign regReadData = RF[0];

always_ff @ (posedge clk)
	if (regWriteEnable)
		RF[0] <= regWriteData;
endmodule
