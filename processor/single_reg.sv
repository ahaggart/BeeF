module single_reg#(parameter width=8) (
	input clk,
	input regReadEnable,
	input regWriteEnable,
	input [width-1:0] regWriteData,
	output logic [width-1:0] regReadData
);

//declare memory/reg file array itself
logic [width-1:0] RF [1]; //RF [NUM REGS]

assign regReadData = RF[0];

always_ff @ (posedge clk)
	if (regWriteEnable)
		RF[0] <= regWriteData;
endmodule
