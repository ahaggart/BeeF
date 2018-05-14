
module top_level(
	input clk,
	      reset,
	output logic done
);

logic Halt;
logic [7:0] PC;			//how big is our PC????
logic [7:0] PCIncremented;	//after incrementing PC
logic [7:0] PCSelected;		//PC after mux picks source

wire bubble;
	
logic [8:0] Instruction; 	//machine code
logic [7:0] alu_operand;
logic [7:0] alu_result_o;
logic overflow_o;

logic [7:0] memDataOut;		//data memory read output
logic [7:0] memAddress;        //data memory write access location

InstROM #(.IW(16)) im1(
	.InstAddress (PC),
	.Instruction (Instruction)
);

wire pc_enable;
wire pc_src;

wire alu_op;

wire [15:0] pc;
wire [7:0] reg_value;
wire branch_searching;

alu_ctrl register_manager(
	.clk(clk),
	.Instruction(Instruction),
	.alu_result(alu_result_o),
	.alu_operand(alu_i),
	.alu_op(alu_op),
	.reg_value(reg_value),
	.mem_ptr(memAddress),
	.searching(branch_searching)
);

pc_ctrl pc_controller(
	.clk(clk),
	.instruction(Instruction),
	.write_src(pc_src),
	.write_enable(pc_enable),
	.bubble(pop_bubble),
	.pc(pc)
);

alu alu_main(
	.alu_data_i 	(alu_i),
	.op_i		(alu_op),
	.alu_result_o	(alu_result_o  )
);

wire delay_mem_op;
wire mem_override;

instruction_fetch fetch(
	.clk(clk),
	.delay(mem_stall),
	.delayed_op(stall_type),
	.searching(branch_searching),
	.pc(pc),
	.instruction(Instruction),
	.delay_op(delay_mem_op),
	.delayed(mem_override)
);

mem_ctrl mem_controller(
	.instruction(Instruction),
	.override(mem_override),
	.force_write(delay_mem_op),
	.alu_result(alu_result_o),
	.reg_value(reg_value),
	.pc(pc)
);

endmodule