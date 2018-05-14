
import definitions::*;
module reg_ctrl(
	input [8:0] instruction,
	output logic write_src,
	output logic write_enable
);

op_code op;
assign op = op_code'(instruction);
 
always_comb
begin
	case(op)
		POP: write_src <= 1;
		MVR: write_src <= 1;
		MVL: write_src <= 1;
		default: write_src <= 0;
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

 

endmodule 
