
import definitions::*;
module reg_ctrl(
	input [8:0] instruction,
	input wire popBubble,
	output logic [1:0] write_src,
	output logic write_enable
);

op_code op;
assign op = op_code'(instruction);
 
always_comb
begin
	if(popBubble) begin
		write_src <= 0;
		write_enable <= 1;
	end
	else begin
	case(op)
		PSH: write_src <= 1;
		MVL: write_src <= 1;
		default: write_src <= 0;//from working value register
	endcase
	case(op)
		POP: write_enable <= 1;
		MVR: write_enable <= 1;
		MVL: write_enable <= 1;
		INC: write_enable <= 1;
		DEC: write_enable <= 1;
		default: write_enable <= 0;
	endcase
	end
end

 

endmodule 
