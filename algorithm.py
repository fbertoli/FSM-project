from integerModel import *
import dataTools as data
from linearModel import *
from dualModel import *
from indigoTools import *
import math
import subprocess
import Queue
import threading
import re
import Tkinter, tkMessageBox
from data_tools import *
from nodeSolver import *


def alertMe():
	root = Tkinter.Tk()
	root.withdraw()
	tkMessageBox.showinfo("VERYVERY IMPORTANT MESSAGE", "SIMULATOION IS OVER")

def main():
	print "========================================="
	#data.readTechnicalData("technical_data.txt")
	day_data = nodeSolver("test_data_final_30.txt")
	#day_data_2 = nodeSolver("finaltest_data.txt")
	#print tuneIndigo()





if __name__ == '__main__':
    main()
