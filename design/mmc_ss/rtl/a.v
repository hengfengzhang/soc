module a(/*autoarg*/
    pad,
    //Inputs
    clk, rst_n, b2a_0, b2a_1, 

    //Outputs
    a2b_0, a2b_1
);

input                                   clk;
input                                   rst_n;

input                                   b2a_0;
input        [7:0]                      b2a_1;
output                                  a2b_0;
output       [7:0]                      a2b_1;
inout                                   pad;




endmodule


