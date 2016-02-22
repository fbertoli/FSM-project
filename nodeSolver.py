from gurobipy import *
from dualModel import *
from integerModel import *
import dataTools as data
from time import time
import thread
import threading
import signal
from indigoTools import *

def nodeSolver(data_file, day_data = []):
	""" day_data format is in format (fleet, cost). A list for every day.
		Paramters to be chosen:	bound_vehicles - generation_step - vehicle_repetition (in set_new_costs, vrx_tools) - 
								indigo_parameters (in columnGeneratorIndigo twice) - number_threads (in solveInParallel, readInParallel, columnGenerator)"""
	## CREATE DATA
	if not day_data:
		day_data, max_veh = data.readData(data_file)
	technical_data_file = "technical_data.txt"
	data.readTechnicalData(technical_data_file)
	DAYS = range(len(day_data))
	V_TYPES = range(len(max_veh))

	##INTIALIZE
	## parameter to be chosen
	bound_vehicles = 2 
	bounds_veh = [i*bound_vehicles for i in max_veh]
	dual_mod = dualModel(day_data, bounds_veh, data.fixed_cost)
	dual_mod.createModel()
	dual_mod.mod.optimize()

	integer_mod = integerModel(day_data, bounds_veh, data.fixed_cost)
	integer_mod.createModel()
	integer_mod.mod.optimize()

	## CREATE STATISTICS AND INSPECTION VARIABLES
	previous_linear_obj = 1000000
	epsilon = 0.00001
	time_col_gen = 0
	time_simplex = 0
	time_printing = 0
	iterations = 1
	initial_cost = integer_mod.mod.objVal

	## RUN THE ALGORITHM
	while True:	
		## GET VARS
		f,d = dual_mod.getDualVars()
		p,q = dual_mod.getVars()
		int_f, inf_d = integer_mod.getVars()
		
		## PRINT STUFF
		now = time()
		print "======================ITERATION ",str(iterations),"================================="
		print "FLEETS. LP - MIP",[int(f[t]*1000)/1000.0 for t in V_TYPES], " - ", [int_f[t] for t in V_TYPES]
		print "OBJECTIVE. LP - MIP - LP decrease - GAP", int(dual_mod.mod.objVal*1000)/1000.0, " - ",int(integer_mod.mod.objVal*1000)/1000.0, " - ", int((previous_linear_obj -  dual_mod.mod.objVal)*1000)/1000.0, " - ", int(1000*(integer_mod.mod.objVal -  dual_mod.mod.objVal)/ dual_mod.mod.objVal)/1000.0,"%"
		previous_linear_obj =  dual_mod.mod.objVal
		time_printing += time() - now
		
		## RANK DAYS TO BE INSPECTED FOR COLUMN GENERATION
		now = time()
		marked_days_ranked = sorted([(i,sum([q[t,i] for t in V_TYPES])) for i in DAYS if sum([q[t,i] for t in V_TYPES]) > 0],key=lambda x: x[1], reverse = True)
		info_marked_days = {}
		reduced_costs = {}

		## COLUMNS GENERATION
		current_index = 0
		## parameter to be chosen
		generation_step= 5
		while (not reduced_costs) and current_index < len(marked_days_ranked):
			day_list = [item[0] for item in marked_days_ranked[current_index: current_index + generation_step]]
			current_index += generation_step	
			new_columns = columnGeneratorIndigo(day_data, day_list,q)
			# new_columns is a list of columns = (day_index, fleet, routing cost)
			for col in new_columns:
				if sum(col[1][t]*q[t,col[0]] for t in V_TYPES) + col[2] < p[col[0]]:
					temp_list = [day_data[col[0]][i] for i in range(len(day_data[col[0]])) if day_data[col[0]][i][0] == col[1]]
					# checking if the new found column was already there and the heurstic just performed better.
					if temp_list:
						print "FOUND AGAIN!! Day:",col[0] ,"Fleet:", col[1], "Reduced cost:", sum(col[1][t]*q[t,col[0]] for t in V_TYPES) + col[2] - p[col[0]],
						print "Delta R_Cost:",col[2] -  temp_list[0][1]
					# I don't add the new column if it was already found. Even if the new cst is better.
					else:
						day_data[col[0]].append((col[1], col[2]))
						reduced_costs[col[0]] = sum(col[1][t]*q[t,col[0]] for t in V_TYPES) + col[2] - p[col[0]]
						print "NEGATIVE RED COST. day:", col[0], "fleet:", col[1], "r_cost:",col[2], "v_costs:",[q[t,col[0]] for t in V_TYPES], "bound:", p[col[0]]
		time_col_gen += time() - now
		

		## PRINTING STUFF
		now = time()
		print "------------------------------------------------------------------------------------"
		print "MARKED DAYS - GENERATED COLUMNS - # NEW BASIS COLUMNS ",len(marked_days_ranked), '-',  min(current_index, len(marked_days_ranked)), '-', len(reduced_costs)
		print "NEGATIVE REDUCED COSTS: ", reduced_costs
		print ""
		time_printing += time() - now
		
		## GIVE A CHANCHE TO STOP
		#if TimerRawInput('To stop type something and press enter.') !=  '':
		#	break
		
		if iterations > 15 and iterations%5 == 0:
			new_step = TimerRawInput('Enter new generation_step.')
			if new_step != '':
				generation_step = new_step



		## SIMPLEX ALGORITHM
		now = time()
		if not reduced_costs:
			print "OPTIMALITY REACHED."
			print "CHECKING..."
			print "LAST MARKED DAYS: ", [item[0] for item in marked_days_ranked]
			checkOptimality(day_data,q,p)
			#data.writeData(day_data,"final"+data_file)
			break		
		dual_mod = dualModel(day_data, bounds_veh, data.fixed_cost)
		dual_mod.createModel()
		dual_mod.mod.optimize()
		integer_mod = integerModel(day_data, bounds_veh, data.fixed_cost)
		integer_mod.createModel()
		integer_mod.mod.optimize()
		iterations += 1
		time_simplex += time() - now

	print "time simplex: ", time_simplex, "time generating colum: ", time_col_gen, " -->", time_col_gen/(time_col_gen + time_simplex), "%"
	print "number of interations = ", iterations
	return day_data
	

class AlarmException(Exception):
    pass

def alarmHandler(signum, frame):
    raise AlarmException

def TimerRawInput(prompt='', timeout=1):
    signal.signal(signal.SIGALRM, alarmHandler)
    signal.alarm(timeout)
    try:
        text = raw_input(prompt)
        signal.alarm(0)
        return text
    except AlarmException:
        print 'Time up.'
    signal.signal(signal.SIGALRM, signal.SIG_IGN)
    return ''







