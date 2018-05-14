module alu_ctrl#(parameter PCWidth=16)(
	input clk,
	input [8:0] Instruction,
	input [PCWidth-1:0] alu_result,
	output wire [PCWidth-1:0] alu_operand,
	output wire alu_op,
	output wire [7:0] mem_ptr
);
logic [7:0] alu_i;
logic [7:0] cacheptr, 		//out from resgister file
            stackptr,
	    headptr;

wire cache_enable;
wire branch_ctrl_op;
wire pop_bubble;
wire branch_tracking;
wire branch_searching;

two_one_mux#(.width(1)) op_mux(
	.selector(searching),
	.indata0(Instruction[0]),
	.indata1(branch_ctrl_op),
	.outdata(alu_op)
);

branch_ctrl#(.PCWidth(PCWidth)) branch_controller(
	.clk(clk),
	.instruction(Instruction),
	.working(working_value),
	.popBubble(pop_bubble),
	.branch_tracking_in(alu_result),
	.branch_tracking_out(branch_tracking),
	.branch_tracking_op(branch_ctrl_op),
	.searching(branch_searching)
);

cache_ctrl cache_controller(
	.instruction(Instruction),
	.write_enable(cache_enable)
);

single_reg cache(
	.clk		(clk	),
	.regReadEnable	(1'b1	),		//always reading
	.regWriteEnable	(cache_enable),
	.regWriteData	(alu_result_o),
	.regReadData	(cacheptr    )
);

wire stack_enable;

stack_ctrl stack_controller(
	.instruction(Instruction),
	.write_enable(stack_enable)
);

single_reg stack(
	.clk		(clk	),
	.regReadEnable	(1'b1	),		//always reading
	.regWriteEnable	(stack_enable),
	.regWriteData	(alu_result_o),
	.regReadData	(stackptr)
);

wire head_enable;

head_ctrl head_controller(
	.instruction(Instruction),
	.write_enable(head_enable)
);

single_reg head(
	.clk		(clk	),
	.regReadEnable	(1'b1	),		//always reading
	.regWriteEnable	(head_enable),
	.regWriteData	(alu_result_o),
	.regReadData	(headptr)
);

wire working_src;
wire working_enable;
wire [7:0] working_input; //no name register input data

reg_ctrl reg_controller(
	.instruction(Instruction),
	.write_src(working_src),
	.write_enable(working_enable)
);

two_one_mux working_src_mux(
	.selector	(working_src),			//what picks the source??????????????????????????????
	.indata0	(alu_result_o   ),
	.indata1	(memDataOut     ),
	.outdata	(working_input)
);

single_reg working(
	.clk		(clk	),
	.regReadEnable	(1'b1	),		//always reading
	.regWriteEnable	(working_enable),
	.regWriteData	(working_input),
	.regReadData	(working_value)
);

four_one_mux alu_mux(	
	.selector	(Instruction[2:1]),
	.indata1	(working_value ),
	.indata2	(headptr  ),
	.indata3	(stackptr ),
	.indata4	(cacheptr ),
	.outdata	(alu_i    )
);

two_one_mux#(.width(PCWidth)) alu_mux_2(
	.selector(branch_searching),
	.indata0({0,alu_i}),
	.indata1(branch_tracking),
	.outdata(alu_operand)
);

four_one_mux address_mux(	
	.selector	(Instruction[4:3]),
	.indata1	(headptr 	),
	.indata2	(stackptr	),
	.indata3	(cacheptr	),
	.indata4	(),
	.outdata	(mem_ptr)
);

endmodule
