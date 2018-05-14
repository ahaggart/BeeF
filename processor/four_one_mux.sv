module four_one_mux#(parameter width=8)(
	input  logic [1:0] selector,
	input  logic [width-1:0] indata1,	
    input  logic [width-1:0] indata2,
	input  logic [width-1:0] indata3,
	input  logic [width-1:0] indata4,
	output logic [width-1:0] outdata
);

always_comb
	if (selector == 2'b00) begin
		outdata <= indata1;
	end
	else if (selector == 2'b01) begin
		outdata <= indata2;
	end
	else if (selector == 2'b10) begin
		outdata <= indata3;
	end
	else begin
		outdata <= indata4;
	end

endmodule