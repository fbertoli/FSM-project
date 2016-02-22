from gurobipy import *
import numpy as np
import math

class dualModel:
	def __init__(self, data, max_vehicles, fixed_cost):
		self.day_count = len(data)
		self.v_count = len(data[0][0][0])
		self.max_vehicles = max_vehicles
		self.fixed_cost = fixed_cost
		self.data = data
		self.mod = Model('dual')
		
	def createModel(self):
		V_TYPES = range(self.v_count)
  		DAYS = range(self.day_count)
  		## CREATE VARIABLES
		p = {}
		for i in DAYS:
			p[i] = self.mod.addVar(vtype = GRB.CONTINUOUS, obj = 1, name = 'p'+str(i))

		q = {}
		for i in DAYS:
			for t in V_TYPES:
				q[t,i] = self.mod.addVar(vtype = GRB.CONTINUOUS, lb = 0, name = 'q'+str(t) + '_' + str(i))

		self.mod.update()

		## CREATE CONSTRAINTS
		for t in V_TYPES:
			self.mod.addConstr(quicksum(q[t,i] for i in DAYS) == self.fixed_cost[t], name = "f"+str(t))

		## if we have some forbidden solutions
		for i in DAYS:
			for j in range(len(self.data[i])):
				self.mod.addConstr(p[i] - quicksum([self.data[i][j][0][t] * q[t,i] for t in V_TYPES]) <= self.data[i][j][1], name = "d"+str(i) +"_"+ str(j))

		self.mod.setParam('OutputFlag',0)
		self.mod.modelSense = GRB.MAXIMIZE


	def addConstrDual(self, day_index, column, column_cost):
		self.mod.addConstr(p[day_index] - quicksum([column[t] * q[t,i] for t in V_TYPES]) <= column_cost)

	
	def getVars(self):
		p={}
		q={}
		for i in range(self.day_count):
			p[i] = self.mod.getVarByName("p"+str(i)).x
		for t in range(self.v_count):
			for i in range(self.day_count):
				q[(t,i)] = self.mod.getVarByName("q"+str(t)+"_"+str(i)).x
		return p,q

	def getDualVars(self):
		f = {}
		d = {}
		for t in range(self.v_count):
			f[t] = self.mod.getConstrByName("f"+str(t)).Pi
		for i in range(self.day_count):
			for j in range(len(self.data[i])):
				d[i,j] = self.mod.getConstrByName("d"+str(i) + "_" + str(j)).Pi
		return f,d
    
	def getInterestingDays(self):
		"""return a list divided by vehicle. For each vehicle which days have nonzero cost on that vehicle"""
		p,q = self.getVars()
		return [[i for i in range(self.day_count) if q[t,i] > 0] for t in range(self.v_count)]

	def printObj(self):
		print 'Dual Objective', self.mod.objVal



  