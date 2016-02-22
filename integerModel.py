from gurobipy import *
import numpy as np
import math

class integerModel:
	def __init__(self, data, max_vehicles, fixed_cost):
		self.day_count = len(data)
		self.v_count = len(data[0][0][0])
		self.max_vehicles = max_vehicles
		self.fixed_cost = fixed_cost
		self.data = data
		self.mod = Model('integer')
		
   	def createModel(self):
  		V_TYPES = range(self.v_count)
  		DAYS = range(self.day_count)
    	## VARIABLES
		# fleet variables
		f = {}
		for t in V_TYPES:
			f[t] = self.mod.addVar(vtype = GRB.INTEGER, lb = 0, ub = self.max_vehicles[t], obj = self.fixed_cost[t], name = "f"+str(t))

		# covering fleets variables. d_i_j = 1 iff the fleet F covers the fleet at the j-th solution on the i-th day
		d = {}
		for i in DAYS:
			for j in range(len(self.data[i])):
				namevar = "d"+str(i) +"_"+ str(j)
				d[i,j] = self.mod.addVar(vtype = GRB.BINARY, obj = self.data[i][j][1], name = namevar)

		self.mod.update()

		## CONSTRAINTS
		# we consider only one fleet to be covered (there could be more)
		for i in DAYS:
			namec = "p"+str(i)
			self.mod.addConstr( quicksum( d[i,j] for j in range(len(self.data[i]))) == 1, name = namec)

		# the overall feet cover the chosen fleet for each day
		for i in DAYS:
			for t in V_TYPES:
				namec = "q"+str(t)+"_"+str(i)
				self.mod.addConstr(f[t] - quicksum(self.data[i][j][0][t] * d[i,j] for j in range(len(self.data[i]))) >= 0 , name = namec)

		self.mod.setParam('OutputFlag',0)


  	def getVars(self):
		d= {}
		f = {}
		for t in range(self.v_count):
			f[t] = int(self.mod.getVarByName("f"+str(t)).x)
		for i in range(self.day_count):
			for j in range(len(self.data[i])):
				d[i,j] = int(self.mod.getVarByName("d"+str(i) +"_"+ str(j)).x)
		return f,d

	def printFleet(self):
		print "FLEET = ", [int(self.mod.getVarByName("f"+str(t)).x) for t in range(self.v_count)]

	def whichOption(self):
		f,d = self.getVars()
		options = [k for k in d.keys() if d[k] >0]
		options.sort()
		return [item[1] for item in options]

 	def printObj(self):
 		print 'Integer Objective', self.mod.objVal

