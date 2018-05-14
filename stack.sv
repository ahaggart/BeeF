module stack (
	input clk,
	input push, //are we pushing
	//input pop, //are we popping
	input [7:0] pushin,
	input reset,
	output logic [7:0] popout,
	output logic empty,
	output logic full
);
        logic [6:0] ptr = 0;
	logic [7:0] stack [0:64]; 

	always @ (posedge clk)
		if (reset) begin
			ptr <= 0;
			full <= 0;
			empty <= 1;
		end
		else if(push == 1) begin
			if (ptr == 64) begin
				full <= 1;
			end
    			else begin 
				popout = stack[ptr];
    				ptr = ptr + 1;
				stack[ptr] = pushin;
			end
  		end

		else if(push == 0) begin
			if (ptr == 0) begin
				empty <= 1;
			end
			else begin
    				popout = stack[ptr]; 
    				ptr = ptr - 1;
			end
  		end
endmodule
