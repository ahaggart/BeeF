
import definitions::*;
module mem_unit(
	input clk,
	input MEM_OP mem_op,
	input BYTE alu_out,
	input BYTE acc_out,
	input BYTE stack_out,
	input BYTE head_out,
	input BYTE cache_out,
	input BYTE save_out,

	input MEM_SRC mem_src,
	input MEM_ADDR mem_addr,

	output BYTE mem_out
);

CONTROL read_enable, write_enable;
assign read_enable = CONTROL'(~write_enable);
assign write_enable = CONTROL'(mem_op);

BYTE mem_in, address;

four_one_mux value_select(	
	.selector	(mem_src	),
	.indata1	(acc_out	),
	.indata2	(alu_out	), 
	.indata3	(save_out	),
	.indata4	(	     	),
	.outdata	(mem_in		)
);

four_one_mux address_select(
	.selector	(mem_addr	),
	.indata1	(head_out	),
	.indata2	(stack_out	),
	.indata3	(cache_out	),
	.indata4	(alu_out	),
	.outdata	(address	)
);

data_mem dm1(
    .clk        (clk     		),        
    .memAddress (address 		),
   	.ReadMem    (read_enable	),   	// mem read always on		
   	.WriteMem   (write_enable	),	// write on or off
   	.memDataIn  (mem_in 		), 	 	//data to write		
   	.memDataOut (mem_out		)    	//read result
);
endmodule 
