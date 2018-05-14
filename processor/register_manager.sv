module register_manager#(parameter PCWidth=16)(
	input clk,
	input [8:0] Instruction,
	input [PCWidth-1:0] alu_result,
	output wire [PCWidth-1:0] alu_operand,
	output wire alu_op,
	output wire reg_value,
	output wire branch_searching,
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
logic [7:0] working_value;

assign reg_value = working_value;

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
	.clk(clk),
	.instruction(Instruction),
	.alu_result(alu_result),
	.cache_ptr(cacheptr)
);

wire stack_enable;

stack_ctrl stack_controller(
	.clk(clk),
	.instruction(Instruction),
	.alu_result(alu_result),
	.stack_ptr(stackptr)
);

wire head_enable;

head_ctrl head_controller(
	.clk(clk),
	.instruction(Instruction),
	.alu_result(alu_result),
	.head_ptr(headptr)
);

reg_ctrl reg_controller(
	.clk(clk),
	.instruction(Instruction),
	.alu_result(alu_result),
	.mem_value(mem_read),
	.reg_value(working_value)
);

wire alu_src, address_src;

instruction_decode decode(
	.instruction(Instruction),
	.address_select(address_src),
	.alu_select(alu_src)
);

four_one_mux alu_mux(	
	.selector	(alu_src),
	.indata1	(working_value ),
	.indata2	(headptr  ),
	.indata3	(stackptr ),
	.indata4	(cacheptr ),
	.outdata	(alu_i    )
);

two_one_mux#(.width(PCWidth)) alu_mux_2(
	.selector(branch_searching),
	.indata0({{PCWidth-1{1'b0}},alu_i}),
	.indata1(branch_tracking),
	.outdata(alu_operand)
);

four_one_mux address_mux(	
	.selector	(address_src),
	.indata1	(headptr 	),
	.indata2	(stackptr	),
	.indata3	(cacheptr	),
	.indata4	(),
	.outdata	(mem_ptr)
);

endmodule
