module TestBench();

logic clk, reset, done;

initial begin
	clk = 0;
	reset = 0;
	done = 1;
end

always begin
	#5;
	clk = !clk;
end	

endmodule
