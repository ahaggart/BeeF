module branch_logic_ctrl #(parameter width = 9)(
	input [width-1:0] op1,
	input [width-1:0] op2,
	output wire not_equal
);

assign not_equal = !(op1^op2);

endmodule
