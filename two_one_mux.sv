module two_one_mux#(parameter width=8)(
	input selector,
	input [width-1:0] indata0,	
        input [width-1:0] indata1,
	output logic [width-1:0] outdata
);

assign outdata = selector ? indata1 : indata0;

endmodule
