import definitions::*;
module cache_control(
    input op_code instruction,

    output control_bundle_f controls
);

control_bundle_s bundle;
assign controls = control_bundle_f'(bundle);

always_comb begin
    case(instruction)

    endcase
end

endmodule