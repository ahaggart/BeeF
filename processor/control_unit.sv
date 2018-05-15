import definitions::*;
module control_unit(
    input clk,
    input op_code instruction,
    input STATE state_in,
    input logic acc_zero,

    output CONTROL acc_write,
    output ACC_SRC acc_src,
    output CONTROL stack_write,
    output CONTROL head_write,
    output CONTROL cache_write,
    output CONTROL pc_write,
    output PC_SRC pc_src,
    output MEM_OP mem_op,
    output MEM_ADDR mem_addr,
    output MEM_SRC mem_src,
    output ALU_OP alu_op,
    output CONTROL loader_select,

    output STATE state_out
);

control_bundle_s bundle;
control_bundle_f flat;
assign bundle = control_bundle_s'(flat);

assign acc_write    = bundle.acc_write;
assign acc_src      = bundle.acc_src;
assign stack_write  = bundle.stack_write;
assign head_write   = bundle.head_write;
assign cache_write  = bundle.cache_write;
assign pc_write     = bundle.pc_write;
assign pc_src       = bundle.pc_src;
assign mem_op       = bundle.mem_op;
assign mem_addr     = bundle.mem_addr;
assign mem_src      = bundle.mem_src;
assign alu_op       = bundle.alu_op;
assign alu_src      = alu_src;
assign state_out    = bundle.state;
assign loader_select= bundle.loader_select;

control_bundle_f    core_controls, branch_controls,
                    load_controls, save_controls, 
                    pop_controls;

core_control core(
    .instruction    (instruction),
    .acc_zero       (acc_zero),
    .controls       (core_controls)    
);

branch_control branch(
    .instruction    (instruction),
    .acc_zero       (acc_zero),
    .controls       (branch_controls)
);

// load_control load(

// );

// save_control save(

// );

// pop_control pop(

// );

always_comb begin
    case(state_in)
        BRANCH_S:       flat    <= branch_controls;
        CACHE_LOAD_S:   flat    <= load_controls;
        CACHE_SAVE_S:   flat    <= save_controls;
        POP_WRITE_S:    flat    <= pop_controls;
        default:        flat    <= core_controls;
    endcase
end

endmodule