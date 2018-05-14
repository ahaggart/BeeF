import definitions::*;
module branch_ctrl#(parameter PCWidth=16)(
	input clk,
	input [8:0] instruction,
	input popBubble,
	input [7:0] working,
	input [PCWidth-1:0] branch_tracking_in,
	output reg [PCWidth-1:0] branch_tracking_out,
	output reg branch_tracking_op,
	output reg searching,
	output wire nop
);

op_code op;
wire [8:0] cbb;
wire cmp_result;
wire cmp_input;
assign cbb = CBB;

assign op = op_code'(instruction);
assign nop = popBubble | searching;

always_ff @ (posedge clk) begin
	case(op)
		CBF: begin
			branch_tracking_op <= 0;
			if(working) begin
				searching <= 1'b1;
				branch_tracking_out <= 0;
			end
			else begin searching <= 0; end
		end
		CBB: begin
			branch_tracking_out <= branch_tracking_in;
			if(searching) begin
				branch_tracking_op <= 1;
				if(!branch_tracking_in) searching <= 0;
				else 			searching <= 1'b1;
			end
		end
		default: branch_tracking_out <= branch_tracking_in;
	endcase
				
end

endmodule
