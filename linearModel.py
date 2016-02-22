from gurobipy import *
import numpy as np
import math

class linearModel:
	def __init__(self, data, max_vehicles, fixed_cost):
		self.day_count = len(data)
		self.v_count = len(data[0][0][0])
		self.max_vehicles = max_vehicles
		self.fixed_cost = fixed_cost
		self.data = data
		self.mod = Model('linear')

   	def createModel(self):
  		V_TYPES = range(self.v_count)
  		DAYS = range(self.day_count)
    	## VARIABLES
		# fleet variables
		f = {}
		for t in V_TYPES:
			f[t] = self.mod.addVar(vtype = GRB.CONTINUOUS, lb = 0, ub = self.max_vehicles[t], obj = self.fixed_cost[t], name = "f"+str(t))

		# covering fleets variables. d_i_j = 1 iff the fleet F covers the fleet at the j-th solution on the i-th day
		d = {}
		for i in DAYS:
			for j in range(len(self.data[i])):
				d[i,j] = self.mod.addVar(vtype = GRB.CONTINUOUS, lb = 0, ub = 1, obj = self.data[i][j][1], name = "d"+str(i) +"_"+ str(j))

		self.mod.update()

		## CONSTRAINTS
		# we consider only one fleet to be covered (there could be more)
		for i in DAYS:
			self.mod.addConstr( quicksum( d[i,j] for j in range(len(self.data[i]))) == 1, name = "p"+str(i))

		# the overall feet cover the chosen fleet for each day
		for i in DAYS:
			for t in V_TYPES:
				self.mod.addConstr(f[t] - quicksum(self.data[i][j][0][t] * d[i,j] for j in range(len(self.data[i]))) >= 0 , name = "q"+str(t)+"_"+str(i))

		self.mod.setParam('OutputFlag',0)

	 
   	def getVars(self):
		d= {}
		f = {}
		for t in range(self.v_count):
			f[t] = self.mod.getVarByName("f"+str(t)).x
		for i in range(self.day_count):
			for j in range(len(self.data[i])):
				d[i,j] = self.mod.getVarByName("d"+str(i) +"_"+ str(j)).x
		return f,d

  	def getDuals(self):
		p={}
		q={}
		for i in range(self.day_count):
			p[i] = self.mod.getConstrByName("p"+str(i)).Pi
		
		for t in range(self.v_count):
			for i in range(self.day_count):
				q[(t,i)] = self.mod.getConstrByName("q"+str(t)+"_"+str(i)).Pi
		return p,q
	
	def printFleet(self):
		print "FLEET = ", [self.mod.getVarByName("f"+str(t)).x for t in range(self.v_count)]

	def whichOption(self):
		"""return list indexed on days. For each days I have a list with the nonzero options"""
		f,d = self.getVars()
		options = [[] for i in range(self.day_count)]
		for (i,j) in d.keys():
			if d[i,j]>0:
				options[i].append(j)
		for item in options:
			item.sort()
		return options

  	def printObj(self):
  		print 'Linear Objective', self.mod.objVal


