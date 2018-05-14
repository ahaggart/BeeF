// Create Date:     2017.05.05
// Latest rev date: 2017.10.26
// Created by:      J Eldon
// Design Name:     CSE141L
// Module Name:     ALU (Arithmetic Logical Unit)


//This is the ALU module of the core, op_code_e is defined in definitions.v file
// Includes new enum op_mnemonic to make instructions appear literally on waveform.
import definitions::*;

module alu (
	input  [7:0]       alu_data_i ,	 // operand 
        input op_i,			 // increment or decrement
	output logic [7:0] alu_result_o	 // result
);

//op_code    op3; 	                     // type is op_code, as defined
//assign op3 = op_code'(op_i[8:6]);        // map 3 MSBs of op_i to op3 (ALU), cast to enum
//assign op3 = op_code' (op_i);

always_comb								  // no registers, no clocks
  begin
    alu_result_o   = 'd0;                     // default or NOP result
  case (op_i)   						     
	//INC: {ov_o, result_o} = r_i + 9'b1;
	//DEC: {ov_o, result_o} = r_i - 9'b1;
	0: alu_result_o = alu_data_i + 9'b1; //INC
	1: alu_result_o = alu_data_i - 9'b1; //DEC
    endcase
  end

endmodule 
