import sys
import os
import subprocess
import Queue
import threading
import dataTools as data
import re

def initialize(n_days):
	indigo_parameters = (50,2000)
	(input_file_list, output_file_list, seed_file_list) = ([], [], [])
	for day in range(n_days):
		input_file_list.append("./vrx_instances/new" + str(day) + ".vrx")
		output_file_list.append("./vrx_temp_files/new"+ str(day)+"_0_out")
		seed_file_list.append("")
	solveInParallel(input_file_list, output_file_list, seed_file_list, indigo_parameters)
	initial_data = readInParallel(output_file_list)
	initial_data.sort()
	data.writeData([[(item[1], item[2])] for item in initial_data], "test_data.txt")


def columnGeneratorIndigo(day_data,day_list,q):
	""" fleet has to be ordered [4,20,26,60]"""
	## parameter to be chosen
	indigo_parameters = (50,2000)
	(input_file_list, output_file_list, seed_file_list) = ([], [], [])
	for day in day_list:
		setNewCosts("./vrx_instances/base-new"+str(day)+".vrx", "./vrx_temp_files/new"+ str(day)+"_"+str(len(day_data[day]))+".vrx", [q[t,day] for t in range(len(day_data[0][0][0]))])
		input_file_list.append("./vrx_temp_files/new"+ str(day)+"_"+str(len(day_data[day]))+".vrx")
		output_file_list.append("./vrx_temp_files/new"+ str(day)+"_"+str(len(day_data[day]))+"_out")
		seed_file_list.append("./vrx_temp_files/new"+ str(day)+"_0_out")
	
	solveInParallel(input_file_list, output_file_list, seed_file_list, indigo_parameters)
	return readInParallel(output_file_list)





def setNewCosts(original_file_name, output_file_name, new_fixed_costs):
	"""create a vrx instance with the given new fixed costs and routes and all the other fields taken from input_file_name
		new_fixed_costs are in the form [4,20,26,60]
		routes are in the form [4,4P, 20, 20P, 26, 26P, 60, 60P] """ 
	line_vehicle_60 = "\t43108	39300	41666	-1	-1	-1	"
	line_vehicle_26 = "\t29371	26800	28205	-1	-1	-1	"
	line_vehicle_20 = "\t20580	18800	19871	-1	-1	-1	"
	line_vehicle_4 = "\t40800	38800	39743	-1	-1	-1	"
	line_veh = [line_vehicle_4, line_vehicle_20, line_vehicle_26, line_vehicle_60 ]
	veh = ['  veh-Cairns4', '  veh-Cairns20', '  veh-Cairns26', '  veh-Cairns60']
	
	new_file = open(output_file_name, 'w')
	new_file.write('VRX\n\n')
	#new_file.write('@base1.vrx\n\n')
	temp = open("./vrx_instances/base1.vrx",'r')
	lines = temp.readlines()
	temp.close()
	new_file.writelines(lines)
	new_file.write('\n\nVEHICLES\n')
	
	## parameter to be chosen
	vehicle_repetition = 10
	for t in range(len(new_fixed_costs)):
		for i in range(vehicle_repetition):
			new_file.write(veh[t]+"-"+str(i)+line_veh[t]+str(new_fixed_costs[t])+"\n")
	new_file.write("*END*\n\n")

	temp = open("./vrx_instances/base2.vrx",'r')
	lines = temp.readlines()
	temp.close()
	new_file.writelines(lines)
	new_file.write("\n\n")

	input_data = open(original_file_name,'r')	
	lines = input_data.readlines()
	input_data.close()
	new_file.writelines(lines)
	new_file.write("\n")
	
	temp = open("./vrx_instances/base3.vrx",'r')
	lines = temp.readlines()
	temp.close()
	new_file.writelines(lines)



def solveInParallel(input_file_list, output_file_list, seed_file_list, indigo_parameters):  
	## parameter to be chosen
	number_threads = 4
	## CREATE QUEUE
	new_queue = Queue.Queue()
	for j in range(len(input_file_list)):
		new_queue.put((input_file_list[j], output_file_list[j], seed_file_list[j], indigo_parameters))
	
	## DEFINE WHAT A SINGLE THREAD WILL DO
	def worker():
		while True:
			info_day= new_queue.get()
			if info_day is None:
				return
			else:
				(input_file, output_file, seed_file, indigo_parameters) = info_day
			## SOLVE DAY
			if seed_file == "":
				command_line = "indigo -i lnssa-"+str(indigo_parameters[0])+"-"+str(indigo_parameters[1])+" " + input_file + " -r "+output_file  +" -q"
			else:
				command_line = "indigo -i lnssa-"+str(indigo_parameters[0])+"-"+str(indigo_parameters[1])+" " + input_file + " -r "+output_file  +" -q -sf "+seed_file
			devnull = open(os.devnull, 'wb')
			p = subprocess.Popen(command_line, shell = True, stdout = devnull)
   			p.wait()
			
	## RUN THREADS
	threads = [ threading.Thread(target=worker) for _i in range(number_threads) ]
	for thread in threads:
	 	thread.start()
		new_queue.put(None)  # one EOF marker for each thread

	## WAIT TILL ALL THREADS ARE FINISHED
	for thread in threads:
		thread.join()



def readInParallel(output_file_list):
	## parameter to be chosen
	number_threads = 4
	
	## CREATE QUEUE
	new_queue = Queue.Queue()
	new_columns = []
	for j in range(len(output_file_list)):
		new_queue.put(output_file_list[j])
	
	## DEFINE WHAT A SINGLE THREAD WILL DO
	def worker():
		while True:
			info_day= new_queue.get()
			if info_day is None:
				return
			else:
				fleet, routing_cost = recalculateCost(info_day)
				new_columns.append([int(re.findall(r'\d+', info_day)[0]), fleet, routing_cost])
			
	## RUN THREADS
	threads = [ threading.Thread(target=worker) for _i in range(number_threads) ]
	for thread in threads:
	 	thread.start()
		new_queue.put(None)  # one EOF marker for each thread

	## WAIT TILL ALL THREADS ARE FINISHED
	for thread in threads:
		thread.join()

	return new_columns



def recalculateCost(output_file_name):
	source = open(output_file_name, 'r')
	lines= source.readlines()
	routes = []
	fleet = {"s4": 0, "s4P": 0, "20": 0, "20P": 0, "26": 0, "26P": 0, "60": 0, "60P": 0}
	for line in lines[2:]:
		if "Route-Veh" in line:
			requests = ["loc-CAIRNS"]
			parts = line.split()
			type_route = parts[2][-4:-2] + ("P" in parts[1])*"P"
			fleet[type_route] += 1
			for stop in parts[3:]:
				requests.append("loc-"+stop[4:])
			requests.append("loc-CAIRNS")
			routes.append((type_route, requests))
		elif "Unassigned" in line and len(line.split()) >2:
			print "There were unassigned requests. Check", output_file_name
			break
		else:
			break
	
	## RECALCULATE COST
	real_fleet = {"s4": max(fleet["s4"], fleet["s4P"]), "20":  max(fleet["20"], fleet["20P"]), "26": max(fleet["26"], fleet["26P"]), "60": max(fleet["60"], fleet["60P"])}
	r_cost = 0
	type_index = {"s4" : 0, "20": 1, "26": 2, "60": 3, "s4P" : 0, "20P": 1, "26P": 2, "60P": 3}
	for (type_r, stops) in routes:
		for i in range(len(stops)-1):
			r_cost += data.distances[stops[i], stops[i+1]][0] * data.routing_coeff[type_index[type_r]] + data.distances[stops[i], stops[i+1]][1] * data.time_coeff[type_index[type_r]] 
	return [real_fleet['s4'], real_fleet['20'], real_fleet['26'], real_fleet['60']], r_cost



def checkOptimality(day_data,q,p):  
	## parameter to be chosen
	indigo_parameters = (50,2000)

	## CREATE QUEUE
	new_queue = Queue.Queue()
	problems = []
	summary = []
	for day in range(len(p)):
		new_queue.put((day,"./vrx_instances/base-new"+str(day)+".vrx","./vrx_temp_files/new"+ str(day)+"_check.vrx",[q[t,day] for t in range(len(data.fixed_cost))], "./vrx_temp_files/new"+str(day)+"_check_out" ,"./vrx_temp_files/new"+str(day)+"_0_out", p[day]))		
	
	## DEFINE WHAT A SINGLE THREAD WILL DO
	def worker():
		while True:
			info_day= new_queue.get()
			if info_day is None:
				return
			else:
				(day_index, base_file, new_file, new_costs, output_file, seed_file, bound) = info_day
			setNewCosts(base_file, new_file, new_costs)
			## SOLVE DAY
			command_line = "indigo -i lnssa-"+str(indigo_parameters[0])+"-"+str(indigo_parameters[1])+" " + new_file + " -r "+output_file  +" -q -sf "+seed_file
			devnull = open(os.devnull, 'wb')
			p = subprocess.Popen(command_line, shell = True, stdout = devnull)
   			p.wait()
   			fleet, routing_cost = recalculateCost(output_file)
   			summary.append((day_index, fleet, routing_cost))
   			if sum(fleet[t]*new_costs[t] for t in range(len(new_costs))) + routing_cost < bound and fleet not in [item[0] for item in day_data[day_index]]:
				if sum(new_costs) >0:
					problems.append("SHIT! DAY" + str(day_index) + " (marked), I FOUND A NEGATIVE REDUCED COST. FLEET =" +str(fleet)+ "r_cost = " +str(routing_cost) + "reduce cost =" + str(sum(fleet[t]*new_costs[t] for t in range(len(new_costs))) + routing_cost - bound))
				else:
					problems.append("SHIT! DAY" + str(day_index) + " (NOT marked), I FOUND A NEGATIVE REDUCED COST. FLEET =" +str(fleet)+ "r_cost = " +str(routing_cost) + "reduce cost =" + str(sum(fleet[t]*new_costs[t] for t in range(len(new_costs))) + routing_cost - bound))
				#sys.exit()
			
	## RUN THREADS
	threads = [ threading.Thread(target=worker) for _i in range(4) ]
	for thread in threads:
	 	thread.start()
		new_queue.put(None)  # one EOF marker for each thread

	## WAIT TILL ALL THREADS ARE FINISHED
	for thread in threads:
		thread.join()

	
	if problems:
		print "PROBLEMS:"
		for line in problems:
			print line
	else:
		print "no negative reduced costs found"

	print "SUMMARY"
	summary.sort()
	for line in summary:
		print "Day:", line[0], "fleet:", line[1], "r_cost:", line[2], "v_cost:", [q[t,line[0]] for t in range(len(day_data[0][0][0]))], "bound:", p[line[0]]


def tuneIndigo():
	limit = 10
	fixed_cost = [2615, 2863, 2615, 3290]
	input_file_list = []
	for day in range(limit):
		setNewCosts("./vrx_instances/base-new"+str(day)+".vrx", "./vrx_tune_Indigo/file"+ str(day)+ ".vrx", fixed_cost)
		input_file_list.append("./vrx_tune_Indigo/file"+ str(day)+ ".vrx")
	return tuner(input_file_list)



def tuner(input_file_list):
	n_runs = 1
	parameter1 = [10, 20, 40, 60, 100]
	parameter2 = [1000, 1500, 2000]
	fixed_cost = [2615, 2863, 2615, 3290]
	results = {}

	## CREATE QUEUE
	new_queue = Queue.Queue()
	for p1 in parameter1:
		for p2 in parameter2:
			for i in range(n_runs):
				for f in range(len(input_file_list)):
					new_queue.put((f,i,input_file_list[f], "./vrx_tune_indigo/file"+str(f)+"out_"+str(p1)+str(p2)+".txt", p1, p2))

	## DEFINE WHAT A SINGLE THREAD WILL DO
	def worker():
		while True:
			info_day= new_queue.get()
			if info_day is None:
				return
			else:
				(file_index, run_number, input_file, output_file, p1, p2) = info_day
			## SOLVE DAY
			command_line = "indigo -i lnssa-"+str(p1)+"-"+str(p2)+" " + input_file + " -r "+output_file  +" -q"
			devnull = open(os.devnull, 'wb')
			p = subprocess.Popen(command_line, shell = True, stdout = devnull)
   			p.wait()
   			fleet, routing_cost = recalculateCost(output_file)
   			results[p1,p2, file_index, run_number] = routing_cost + sum(fleet[t]*fixed_cost[t] for t in range(len(fixed_cost)))

   	## RUN THREADS
	threads = [ threading.Thread(target=worker) for _i in range(4) ]
	for thread in threads:
	 	thread.start()
		new_queue.put(None)  # one EOF marker for each thread

	## WAIT TILL ALL THREADS ARE FINISHED
	for thread in threads:
		thread.join()

	## AVERAGE
	results_2 = {}
	for p1 in parameter1:
		for p2 in parameter2:
			results_2[p1,p2] = sum(results[p1,p2,f,i] for i in range(n_runs) for f in range(len(input_file_list)))/(n_runs +len(input_file_list))
	list_res = [(results_2[k], k) for k in results_2.keys()]
	list_res.sort()
	return list_res[0][1], results_2








   

