module TestBench();

logic clk, reset, done;

top_level processor(
	.clk(clk),
	.reset(reset),
	.done(done)
);

initial begin

end

always begin
	#5;
	clk = !clk;
end	

endmodule
