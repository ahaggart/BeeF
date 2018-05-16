import definitions::*;
module control_unit(
    input clk,
    input reset,
    input op_code instruction,
    input logic acc_zero,

    output control_bundle_f controls
);

STATE state;

control_bundle_f    core_controls, stall_controls, branch_controls;
control_bundle_s    bundle;
assign bundle = control_bundle_s'(controls);

logic [$bits(STATE)-1:0] start_state;
logic [$bits(STATE)-1:0] next_state;
logic [$bits(STATE)-1:0] bundle_state;
assign start_state = CORE_S;
assign state = STATE'(next_state);
assign bundle_state = bundle.state;
CONTROL always_en;
assign always_en = CONTROL'(1'b1);

control_register#(.width(2)) state_register(
    .clk(clk),
    .reset(reset),
    .init(start_state),
    .in_data(bundle_state),
    .enable(always_en),
    .out_data(next_state)
);

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

stall_control stall(
    .instruction    (instruction),
    .acc_zero       (acc_zero),
    .controls       (stall_controls)
);

always_comb begin
    case(state)
        BRANCH_S:   controls    <= branch_controls;
        STALL_S:    controls    <= stall_controls;
        default:    controls    <= core_controls;
    endcase
end

endmodule