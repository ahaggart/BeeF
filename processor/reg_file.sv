// A register file with combinational read and 
//  synchronous write
module reg_file (
   input clk,
   //input [ADR_WIDTH-1:0] r_addr_i,	  // read address pointers (1)
   input [12:0] wa_i,		  // write address pointer
   input wen_i,						  // write enable
   input [7:0] write_data_i,	  // data in
   //output [DATA_WIDTH-1:0] r_val_o	  // data outs (1)
   output [7:0] PC,
   output [7:0] cacheptr,
   output [7:0] stackptr,
   output [7:0] headptr,
   output [7:0] register
   );

// declare memory/reg file array itself
logic [7:0] RF [8];	// RF [NUM_REGS] ???

// reads are combinational -- change pointer/address => change value
//assign r_val_o = RF [r_addr_i];
assign PC = RF[3'b000];
assign cacheptr = RF[3'b001];
assign stackptr = RF[3'b010];
assign headptr = RF[3'b011];
assign register = RF[3'b100];

// writes are sequential/clocked
always_ff @ (posedge clk)     // wait for next clock before writing
  if (wen_i)				  // write only if enabled to do so
    RF [wa_i] <= write_data_i;

endmodule

