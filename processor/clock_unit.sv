import definitions::*;
module clock_unit(
    input CONTROL halt,
    output logic clk
);

initial begin
    clk = 0;
end

always begin
    if(!halt) begin
        #5 clk = 0;
        #5 clk = 1;
    end
end

endmodule