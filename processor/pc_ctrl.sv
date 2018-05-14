import definitions::*;
module pc_ctrl#(parameter PCWidth=16)(
	input clk,
	input [8:0] instruction,
	input [7:0] mem_read,
	output logic [PCWidth-1:0] pc
);

op_code op;
assign op = op_code'(instruction);
assign pc_enable = 1'b1;

logic pc_src;
wire [PCWidth-1:0] pc_value;
wire [PCWidth-1:0] pc_incremented;

single_reg#(.width(PCWidth)) programCounter(
	.clk		    (clk	),
	.regReadEnable	(1'b1	), 		//always reading
	.regWriteEnable	(pc_enable),
	.regWriteData	(pc_value),
	.regReadData	(pc	   )
);

two_one_mux#(.width(PCWidth)) pc_source_mux(
	.selector	(pc_src),
	.indata0	(pc_incremented	),
	.indata1	({{PCWidth-8{1'b0}},mem_read}),
	.outdata	(pc_value	)
);

alu#(.width(PCWidth)) pc_alu(
	.alu_data_i	(pc	),
	.op_i		(1'b0	),		//always adding
	.alu_result_o	(pc_incremented)
);

initial begin
	pc <= 0;
end

always_comb
begin
	case(op)
		CBB: pc_src <= 1;
		default: pc_src <= 0;
	endcase
end

// always_ff @ (posedge clk)
// begin
// 	if(bubble) 	bubble <= 0;
// 	else		bubble <= 1;
// end

endmodule 