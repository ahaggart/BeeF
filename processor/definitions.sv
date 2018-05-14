//This file defines the parameters used in the alu
package definitions;

typedef enum logic[8:0] {
  NOP = 9'b000000000,
  PSH = 9'b110101101,	    // since these start at 0 and are in
  INC = 9'b110000000,		//  increment-by-1 sequence, we could
  DEC = 9'b110000001,		//  omit the 3'bxxx values, but we 
  MVR = 9'b101000010,		//  include these for clarity
  MVL = 9'b101000011,
  CBF = 9'b111110110,
  CBB = 9'b100110111,
  POP = 9'b100001101
} op_code;
	 
endpackage // defintions