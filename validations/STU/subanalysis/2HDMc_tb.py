import sys, os
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import subprocess

lilith_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))+"/"

validation_dir = lilith_dir+"validations/STU/subanalysis/"

calc2HDM_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))+"/2HDMc/2HDMC-1.8.0/"

# Values
mA0 = 500
mH0 = 550
mHpm0 = 780
cba0 = 0.1
sba0 = np.sqrt(1-cba0**2)

# Scan ranges
tb_min = 0.1
tb_max = 10

# Precision
precision = 100

# 2HDM type
yukawatype = 1

# Output files
output = validation_dir+"2HDMc_tb_" + str(mA0) + "_" + str(mH0) + "-" + str(mHpm0) + "-" + str(cba0) + "-" + str(yukawatype) + ".out"
outputplot = validation_dir+"2HDMc_tb_" + str(mA0) + "_" + str(mH0) + "-" + str(mHpm0) + "-" + str(cba0) + "-" + str(yukawatype) + ".pdf"

fresults = open(output, 'w')

i=1

for tb in np.linspace(tb_min, tb_max, precision):
		if i==1:
				print("tb = ", tb, flush=True)
		if i%10==0:
				print("tb = ", tb, flush=True)
		i+=1
		cons = False
		m12 = np.cos( np.arctan(tb) - np.arccos(cba0) ) * (mH0/np.sqrt(tb))

		p1 = subprocess.run([calc2HDM_dir+'CalcPhys', '125.00000', str(mH0), str(mA0), str(mHpm0), str(sba0), '0.00000', '0.00000', str(m12), str(tb), str(yukawatype)], capture_output=True, text=True)
		Treelevelunitarity, Perturbativity, Stability = int(p1.stdout[969]), int(p1.stdout[994]), int(p1.stdout[1019])

		cons = Treelevelunitarity == 1 and Perturbativity == 1 and Stability == 1
		fresults.write('%.5f    '%tb + '%.1f    '%Treelevelunitarity + '%.1f    '%Perturbativity + '%.1f    '%Stability + '%.1f    '%cons + '\n')
