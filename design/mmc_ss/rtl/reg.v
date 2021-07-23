module a(  
	input 	[32-1:0]	  sys_ctrl_hw_wdata , 
	input 			  sys_ctrl_hw_wen , 
	output 	[32-1:0]	  sys_ctrl_hw_rdata , 
	input 	[32-1:0]	  ss_ctrl_hw_wdata , 
	input 			  ss_ctrl_hw_wen , 
	output 	[32-1:0]	  ss_ctrl_hw_rdata , 
	input			pclk,
	input			presetn,
	input			psel,
	input			pwrite,
	input			penable,
	input	wire	[31:0]	paddr,
	input	wire	[31:0]	pwdata,
	output	reg	[31:0]	prdata,
	output			pready
); //port end

wire [31: 0]   offset_addr;

assign offset_addr = paddr - 32'h00000000;

reg [31:0] paddr_d;
always @(posedge pclk or negedge presetn)
    if(!presetn)
        paddr_d <= 32'h0;
    else
        paddr_d <= offset_addr;

reg	[ 32-1 : 0 ]	version;

always @(posedge pclk or negedge presetn)
	if(!presetn)
		version <= 32'h2021_0721;

reg	[ 32-1 : 0 ]	sys_ctrl;

always @(posedge pclk or negedge presetn)
	if(!presetn)
		sys_ctrl <= 32'hffff_ffff;
	else if ( sys_ctrl_hw_wen )
		sys_ctrl <=  sys_ctrl_hw_wdata ;
	else if ( ( paddr_d == 32'h00000004 ) && penable && pwrite && psel )
		sys_ctrl <= pwdata;

assign	 sys_ctrl_hw_rdata 	=	sys_ctrl;

reg	[ 32-1 : 0 ]	ss_ctrl;

always @(posedge pclk or negedge presetn)
	if(!presetn)
		ss_ctrl <= 32'hffff_ffff;
	else if ( ss_ctrl_hw_wen )
		ss_ctrl <=  ss_ctrl_hw_wdata ;
	else if ( ( paddr_d == 32'h00000008 ) && penable && pwrite && psel )
		ss_ctrl <= pwdata;

assign	 ss_ctrl_hw_rdata 	=	ss_ctrl;


always @(posedge pclk or negedge presetn)
    if(!presetn)
        prdata <= 32'h00000000;
    else if( psel && (!pwrite) && (!penable) )
		prdata <=  32'h00000000
					| ( version & { 32{(offset_addr==32'h00000000)} } )
					| ( sys_ctrl & { 32{(offset_addr==32'h00000004)} } )
					| ( ss_ctrl & { 32{(offset_addr==32'h00000008)} } );

assign	pready	=	~(	( psel && (!pwrite) && (!penable) )	&& sys_ctrl_hw_wen && ss_ctrl_hw_wen 	);
endmodule
