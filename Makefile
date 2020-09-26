verdi:
	verdi -sv -top tb_top -f filelist.f tb_top.v &

sim:
	vcs -full64 -sverilog -kdb -debug_access+all -f filelist.f tb_top.v -R

debug:
	verdi -dbdir simv.daidir -ssf tb_top.fsdb&

#execute this in scripts
env:
	@pwd
	@mkdir ../rtl
	@mkdir ../sim
	@ln -s ../scripts/Makefile ../sim/Makefile
	@mkdir ../rtlqa
	@mkdir ../rtlqa/lint
	@ln -s ../../scripts/Makefile ../rtlqa/lint/Makefile
	@mkdir ../rtlqa/cdc
	@ln -s ../../scripts/Makefile ../rtlqa/cdc/Makefile
	@cp gen_tb.py ../sim
	@cp test_temp.v ../sim
	@cp simulation.temp ../sim

env_clean:
	@pwd
	@rm ../rtl -rf
	@rm ../sim -rf
	@rm ../rtlqa -rf
