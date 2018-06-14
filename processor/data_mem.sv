import definitions::*;
module data_mem #(parameter AW=8)(
  input              clk,                // clock
  input  BYTE        memAddress,		 // pointer
  input              ReadMem,			 // read enable	(may be tied high)
  input              WriteMem,			 // write enable
  input  BYTE        memDataIn,			 // data to store (write into memory)
  output BYTE        memDataOut);			 //	data to load (read from memory)

  logic [7:0] DM [2**AW]; 		 // create array of 2**AW elements (default = 256)

// optional initialization of memory, e.g. seeding with constants
//  initial 
//    $readmemh("dataram_init.list", DM);

  initial $readmemb("empty.bin", DM);

// read from memory, e.g. on load instruction
  always_comb							 // reads are immediate/combinational
    if(ReadMem) begin
      memDataOut = DM[memAddress];
// optional diagnostic print statement:
//	  $display("Memory read M[%d] = %d",DataAddress,DataOut);
    end else 
      memDataOut = 8'bZ;			         // z denotes high-impedance/undriven

// write to memory, e.g. on store instruction
  always_ff @ (posedge clk)	             // writes are clocked / sequential
    if(WriteMem) begin
      DM[memAddress] <= memDataIn;
//	  $display("Memory write M[%d] = %d",DataAddress,DataIn);
    end

endmodule
