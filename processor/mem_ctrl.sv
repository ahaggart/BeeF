
import definitions::*;
module mem_ctrl(
	input [8:0] Instruction,
	input override,
	input force_write,
	input [7:0] alu_result,
	input [7:0] reg_value,
	input [16:0] pc,
	input [7:0] memAddress,
	output logic [7:0] read_data
);

op_code op;
assign op = op_code'(Instruction);

wire [7:0] write_data;
logic [7:0] mem_src;
logic write_enable;

four_one_mux dm_write_data_mux(	
	.selector	(mem_src	),
	.indata1	(reg_value	),
	.indata2	(alu_result	), 
	.indata3	(pc[7:0]	),
	.indata4	(	     	),
	.outdata	(write_data )
);

data_mem dm1(
    .clk            (clk        ),        
    .memAddress 	(memAddress ),
   	.ReadMem        (1'b1       ),   	// mem read always on		
   	.WriteMem       (write_enable),	// write on or off
   	.DataIn         (write_data ), 	 	//data to write		
   	.DataOut        (read_data  )    	//read result
);
 
always_comb
begin
	if(override) begin
		mem_src <= 0;
		write_enable <= force_write;
	end
	else begin
	case(op)
		PSH: mem_src <= 1;
		MVL: mem_src <= 1;
		default: mem_src <= 0;//from working value register
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
