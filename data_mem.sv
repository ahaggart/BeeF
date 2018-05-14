
module data_mem #(parameter AW=8)(
  input              clk,                // clock
  input    [AW-1:0]  memAddress,		 // pointer
  input              ReadMem,			 // read enable	(may be tied high)
  input              WriteMem,			 // write enable
  inout       [7:0]  memDataIn,			 // data to store (write into memory)
  output logic[7:0]  memDataOut);			 //	data to load (read from memory)

  logic [7:0] my_memory [2**AW]; 		 // create array of 2**AW elements (default = 256)

// optional initialization of memory, e.g. seeding with constants
//  initial 
//    $readmemh("dataram_init.list", my_memory);

// read from memory, e.g. on load instruction
  always_comb							 // reads are immediate/combinational
    if(ReadMem) begin
      memDataOut = my_memory[memAddress];
// optional diagnostic print statement:
//	  $display("Memory read M[%d] = %d",DataAddress,DataOut);
    end else 
      memDataOut = 8'bZ;			         // z denotes high-impedance/undriven

// write to memory, e.g. on store instruction
  always_ff @ (posedge clk)	             // writes are clocked / sequential
    if(WriteMem) begin
      my_memory[memAddress] <= memDataIn;
//	  $display("Memory write M[%d] = %d",DataAddress,DataIn);
    end

endmodule
