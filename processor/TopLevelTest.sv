import definitions::*;
module TopLevelTest();

logic clk, reset, done;

MISC processor(
    .reset(reset),
    .clk(clk),

    .done(done)
);

initial begin
	clk = 0;
	reset = 1;

    #10 reset = 0;
end

always begin
	#5 clk = !clk;
end	

endmodule
