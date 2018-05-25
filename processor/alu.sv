// Create Date:     2017.05.05
// Latest rev date: 2017.10.26
// Created by:      J Eldon
// Design Name:     CSE141L
// Module Name:     ALU (Arithmetic Logical Unit)


//This is the ALU module of the core, op_code_e is defined in definitions.v file
// Includes new enum op_mnemonic to make instructions appear literally on waveform.
import definitions::*;

module alu#(parameter width=8) (
  input  [width-1:0]       alu_data_i ,	 // operand 
  input ALU_OP op_i,			 // increment or decrement
  output logic [width-1:0] alu_result_o	 // result
);

//op_code    op3; 	                     // type is op_code, as defined
//assign op3 = op_code'(op_i[8:6]);        // map 3 MSBs of op_i to op3 (ALU), cast to enum
//assign op3 = op_code' (op_i);

always_comb	begin
  case (op_i)   						     
    ALU_DEC: alu_result_o <= alu_data_i - {{(width-1){1'b0}} ,1'b1}; //DEC
    default: alu_result_o <= alu_data_i + {{(width-1){1'b0}} ,1'b1}; //INC
  endcase
end

endmodule 
