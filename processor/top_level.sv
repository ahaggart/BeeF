
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

alu_ctrl alu_control(
	.clk(clk),
	.Instruction(Instruction),
	.alu_result(alu_result_o),
	.alu_operand(alu_i),
	.alu_op(alu_op),
	.mem_ptr(memAddress)
	
);

pc_ctrl pc_controller(
	.clk(clk),
	.instruction(Instruction),
	.write_src(pc_src),
	.write_enable(pc_enable),
	.bubble(pop_bubble)
);

two_one_mux pc_source_mux(
	.selector	(pc_src),			//what picks the source??????????????????????????????
	.indata0	(PCIncremented	),
	.indata1	(memDataOut   	),
	.outdata	(PCSelected	)
);

single_reg programCounter(
	.clk		(clk	),
	.regReadEnable	(1'b1	),		//always reading
	.regWriteEnable	(pc_enable),			//???????????????????????
	.regWriteData	(PCSelected),
	.regReadData	(PC	   )
);

alu#(.IW(16)) pc_alu(
	.alu_data_i	(PC	),
	.op_i		(1'b0	),		//always adding
	.alu_result_o	(PCIncremented)
);

alu alu_main(
	.alu_data_i 	(alu_i),
	.op_i		(alu_op),
	.alu_result_o	(alu_result_o  )
);

data_mem dm1(
        .clk            (clk        ),        
        .memAddress (memAddress ),
   	.ReadMem        (1'b1       ),   	// mem read always on		
   	.WriteMem       (Instruction[7]),	// write on or off
   	.DataIn         (memDataIn  ), 	 	//data to write		
   	.DataOut        (memDataOut )    	//read result
);

wire instruction_at_pc;

InstROM instruction_mem(       
        .InstAddress (PC ),		
   	.InstOut        (instruction_at_pc )    	//read result
);

two_one_mux#(.width(9)) inst_mux(
	.selector(bubble),
	.indata0(instruction_at_pc),
	.indata1(0),
	.outdata(Instruction)
);

wire [1:0] mem_src;

mem_ctrl mem_controller(
	.instruction(Instruction),
	.popBubble(pop_bubble),
	.write_src(mem_src)
);

four_one_mux dm_write_data_mux(	
	.selector	(mem_src),
	.indata1	(working_value),
	.indata2	(alu_result_o), 
	.indata3	(PC  ),//??
	.indata4	(	     ),//??
	.outdata	(memDataIn   )
);

endmodule