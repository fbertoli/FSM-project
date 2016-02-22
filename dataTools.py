
def readData(name_file):
	""" read file from name_file. 
	    Output = list of solutions for each day. Solutions for a day is a list of tuples (fleet,cost) """
	## DEFINE VARIABLES AND STRUCTURES
	with open(name_file, 'r') as input_data_file:
		input_data = ''.join(input_data_file.readlines())
	lines = input_data.split('\n')
	parts = lines[0].split(" ")
	day_count = int(parts[0])
	vehicle_count = int(parts[1])
	day_data = []
	max_veh = [0]*vehicle_count
	for i in range(day_count):
		day_info = []
		parts = lines[i+1].split()
		for j in range(len(parts)/(vehicle_count+1)):
			step = j*5
			day_info.append( ([int(parts[step]), int(parts[step+1]), int(parts[step+2]), int(parts[step+3])], float(parts[step+4])) )
			for t in range(vehicle_count):
				max_veh[t] = max(max_veh[t], int(parts[step+t]) )
		day_data.append(day_info)	
	return day_data, max_veh

	

def readTechnicalData(technical_data_file):
	"""create the variables: fixed_cost, routing_coeff, time_coeff, distances"""
	global fixed_cost, routing_coeff, time_coeff, distances
	with open(technical_data_file, 'r') as input_data_file:
		lines = input_data_file.readlines()
	(fixed_cost, routing_coeff, time_coeff, distances) = ([], [], [], {})
	parts = lines[0].split()
	vehicle_types = int(parts[1])
	try:
		parts = lines[1].split()
		if parts[-1] != "fixed_cost":
			print "ERROR in techincal_data.txt FORMAT, fixed_cost"
		for t in range(vehicle_types):
			fixed_cost.append(float(parts[t]))
		parts = lines[2].split()
		if parts[-1] != "routing_coeff":
			print "ERROR in techincal_data.txt FORMAT, routing_coeff"
		for t in range(vehicle_types):
			routing_coeff.append(float(parts[t]))
		parts = lines[3].split()
		if parts[-1] != "time_coeff":
			print "ERROR in techincal_data.txt FORMAT, time_coeff"
		for t in range(vehicle_types):
			time_coeff.append(float(parts[t]))
		if 'DISTANCE' not in lines[5]:
 			print "ERROR in techincal_data.txt FORMAT, distance matrix"
 		i = 6
		while lines[i][:5] != '*END*':
			parts = lines[i].split()
			distances[parts[0], parts[1]] = (float(parts[2]), float(parts[3]))
			i += 1
	except Exception as e:
		print e
		print "ERROR IN readTechincalData WITHIN THE TRY STRUCTURE"



def writeData(day_data, output_file_name):
	"""output format: one line for each day with (cost_1, fleet_1), (cost_2, fleet_2), ..."""
	target = open(output_file_name, 'w')
	n_veh = len(day_data[0][0][0])
	target.write(str(len(day_data))+ " " + str(n_veh) + "\n")
	for i in range(len(day_data)):
		for j in range(len(day_data[i])):
			for t in range(n_veh):
				target.write(str(day_data[i][j][0][t]) + ' ')
			target.write( '  ' + str(day_data[i][j][1]) + '\t')	
		target.write('\n')
	target.close()

