import definitions::*;
module branch_ctrl#(parameter PCWidth=16)(
	input clk,
	input [8:0] instruction,
	input [7:0] working,
	input [PCWidth-1:0] branch_tracking_in,
	output logic [PCWidth-1:0] branch_tracking_out,
	output logic branch_tracking_op,
	output logic searching
);

op_code op;
assign op = op_code'(instruction);

always_ff @ (posedge clk) begin
	case(op)
		CBF: begin
			branch_tracking_op <= 0;
			if(!searching) branch_tracking_out <= 0;
			else branch_tracking_out <= branch_tracking_in;
			if(working) begin
				searching <= 1'b1;
			end
		end
		CBB: begin
			branch_tracking_op <= 1;
			branch_tracking_out <= branch_tracking_in;
		end
		default: branch_tracking_out <= branch_tracking_in;
	endcase
	if(!branch_tracking_in) searching <= 0;
				
end

endmodule
