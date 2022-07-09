import sys, os
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from iminuit.minimize import minimize
import subprocess
import time
import concurrent.futures
from concurrent.futures import ProcessPoolExecutor as executor 
from multiprocessing import Pool
from math import floor, log, sqrt, sin, cos, atan
from cmath import sqrt as csqrt
from cmath import asin as casin

lilith_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))+"/"
sys.path.append(lilith_dir)
import lilith

validation_dir = lilith_dir+"validations/STU/finalanalysis/"
calc2HDM_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))+"/2HDMc/2HDMC-1.8.0/"

######################################################################
# Parameters
######################################################################

#count = 0
#precision = 120
#for a in np.linspace(-np.pi/2, 0, precision):
#	for tb in np.linspace(0.5, 10, precision):	
#		if abs(np.sin(np.arctan(tb) - a)) > 0.9:
#			count += 1

#print("counter full 80*160 = ", 80*160)
#print("counter = ", count)


######################################################################
# Parameters
######################################################################

print("***** reading parameters *****", flush=True)

# Values

# Scan ranges
mA_min = 200
mA_max = 2000
mH_min = 200
mH_max = 2000
mHpm_min = 200
mHpm_max = 2000

#mA_min = 1100
#mA_max = 1200
#mH_min = 1000
#mH_max = 1100
#mHpm = 1000

a_min = -np.pi/2
a_max = 0
tb_min = 0.5
tb_max = 10

# Precisions
#mH_precision = 80
#mA_precision = 80
#mHpm_precision = 80
#a_precision = 200
#tb_precision = 200

mH_precision = 80
mA_precision = 80
mHpm_precision = 80
a_precision = 200
tb_precision = 200

#mH_precision = 2
#mA_precision = 2
#mHpm_precision = 2
#a_precision = 20
#tb_precision = 20

# Experimental results
exptype = "CMS140fb"
#exptype = "CMS36fb"

# 2HDM type = 1, 2
yukawatype = "I"

# Fit strategy
strategy = 0

if exptype == "CMS140fb":
	exp_input = validation_dir + "thisRun2.list"
if exptype == "CMS36fb":
	exp_input = validation_dir + "latestRun2.list"

# Fixed Values

# STU
Scen = 0.06
Ssigma = 0.10
Tcen = 0.11
Tsigma = 0.12
Ucen = 0.14
Usigma = 0.09
STcorrelation = 0.9
SUcorrelation = -0.59
TUcorrelation = -0.85
CEN_STU = np.array([Scen, Tcen, Ucen])
SIG_STU = np.diag([Ssigma, Tsigma, Usigma])
COR_STU = np.array(([1, STcorrelation, SUcorrelation],
                [STcorrelation, 1 , TUcorrelation],
                [SUcorrelation, TUcorrelation, 1]))	
C_STU = SIG_STU.dot(COR_STU).dot(SIG_STU)
C_STU_inv = np.linalg.inv(C_STU)

# Lilith precision mode
my_precision = "BEST-QCD"

# Higgs mass to test
hmass = 125.09

# m2logL
m2logLmax = 100
penalty = m2logLmax/10

# Multiprocessing lists
mHlist = []
for mH in np.linspace(mH_min, mH_max, mH_precision):
	mHlist.append(mH)

iterationlist = []
for i in range(mH_precision):
	iterationlist.append(i)

# Output files
output = []
for i in range(mH_precision):
	output.append(validation_dir+"multiprocessing/mHmA_STU_minuit_mHpm_a_tb_Hpm_" + exptype + "_" + str(i) + ".out")
	
outputfinal = validation_dir+"mHmA_STU_minuit_mHpm_a_tb_" + str(mH_precision) + "_" + str(mA_precision) + "_" + str(mHpm_precision) + "_" + str(a_precision) + "_" + str(tb_precision) + "_" + yukawatype + "_Hpm_" + exptype + "_2HDMc" + ".out"
outputplot = validation_dir+"mHmA_STU_minuit_mHpm_a_tb_" + str(mH_precision) + "_" + str(mA_precision) + "_" + str(mHpm_precision) + "_" + str(a_precision) + "_" + str(tb_precision) + "_" + yukawatype + "_Hpm_" + exptype + "_2HDMc" + ".pdf"


######################################################################
# Scan initialization
######################################################################

print("***** scan initialization *****", flush=True)

# Initialize a Lilith object
lilithcalc = lilith.Lilith(verbose=False,timer=False)
# Read experimental data
lilithcalc.readexpinput(exp_input)

########################################################################
# SM and H+ LO contribution to the reduced H-gamma-gamma coupling CGa
########################################################################

# Values

mW = 80.398 
v = 246
mZ = 91.1876

mt = 173.1
mb = 4.75
mc = 1.4
mtau = 1.777
sW2 = 0.23116

# New values ????

def fhiggs(t):
    if t<=1.:
        return casin(sqrt(t))**2.
    else:
        return -(log((sqrt(t)+sqrt(t-1.))/(sqrt(t)-sqrt(t-1.)))-np.pi*1j)**2./4.

def A0(tau):
    return -1./tau *(1.-1./tau * fhiggs(tau))

def A12(tau):
    return 2./tau *(1.+(1.-1./tau) * fhiggs(tau))

def A1(tau):
    return -(3.*tau+2.*tau**2. +3.*(2.*tau-1.) * fhiggs(tau))/tau**2


def get_CGa(mHpm, a, tb, b, sinba, cosba, l1, l2, l3, l4, l5):
	""" 
      Returns CGa computed from the SM particles contribution plus 
      Hpm contribution.
	"""

	if yukawatype == "I":
		CV = sinba
		CU = np.cos(a)/np.sin(b)
		CD = np.cos(a)/np.sin(b)
    
	elif yukawatype == "II":
		CV = sinba
		CU = np.cos(a)/np.sin(b)
		CD = -np.sin(a)/np.cos(b)

	Z3 = 0.25*np.sin(2*b)**2 * (l1 + l2 + -2*( l3 + l4 + l5 ) ) + l3
	Z7 = -0.5*np.sin(2*b) * ( l1*np.sin(b)**2 - l2*np.cos(b)**2 + ( l3 + l4 + l5 )*np.cos(2*b) ) 

	ChHpmHpm = -v*(Z3*sinba + Z7*cosba)

	A12t = A12((hmass/(2.*mt))**2.)
	A12c = A12((hmass/(2.*mc))**2.)
	A12b = A12((hmass/(2.*mb))**2.)
	A12tau = A12((hmass/(2.*mtau))**2.)
	A1W = A1((hmass/(2.*mW))**2.)
	A0Hpm = A0((hmass/(2.*mHpm))**2.)

	SM_amplitude = CU*4./3.*(A12t + A12c) + CD*1./3.*A12b + CD*A12tau + CV*A1W
	Hpm_amplitude = ChHpmHpm*A0Hpm
  
	CGa = sqrt( abs(SM_amplitude + Hpm_amplitude)**2./abs(SM_amplitude)**2. )

	C = [CV, CU, CD, CGa]

	return C

#####################################################################
# usrXMLinput: generate XML user input
#####################################################################

def usrXMLinput(mass=125.09, CV=1, CU=1, CD=1, CGa=1, precision="BEST-QCD"):
    """generate XML input from reduced couplings CU, CD, CV, CGa"""

    myInputTemplate = """<?xml version="1.0"?>

<lilithinput>

<reducedcouplings>
  <mass>%(mass)s</mass>

  <C to="uu">%(CU)s</C>
  <C to="dd">%(CD)s</C>
  <C to="VV">%(CV)s</C>
  <C to="gammagamma">%(CGa)s</C>
  
  <extraBR>
    <BR to="invisible">0.</BR>
    <BR to="undetected">0.</BR>
  </extraBR>

  <precision>%(precision)s</precision>
</reducedcouplings>

</lilithinput>
"""

    myInput = {'mass':mass, 'CV':CV, 'CU':CU, 'CD':CD, 'CGa':CGa, 'precision':precision}
        
    return myInputTemplate%myInput


######################################################################
# Likelihood Calculation
######################################################################

def func(X, mH, mA, grid):
		mHpm, a, tb = X[0], X[1], X[2]

		b = np.arctan(tb)
		sinba = np.sin(b-a)
		cosba = np.sin(b-a)
		m122 = np.cos(a)**2*mH**2/tb

		if yukawatype=="I":
			p1 = subprocess.run([calc2HDM_dir+'CalcPhys', '125.00000', str(mH), str(mA), str(mHpm), str(sinba), '0.00000', '0.00000', str(m122), str(tb), "1"], capture_output=True, text=True)
		elif yukawatype=="II":
			p1 = subprocess.run([calc2HDM_dir+'CalcPhys', '125.00000', str(mH), str(mA), str(mHpm), str(sinba), '0.00000', '0.00000', str(m122), str(tb), "2"], capture_output=True, text=True)

		if m122>999999:
			if p1.stdout[765] != " ":
				S, T, U = float(p1.stdout[1059:1071]), float(p1.stdout[1086:1098]), float(p1.stdout[1113:1125])
				Treelevelunitarity, Perturbativity, Stability = int(p1.stdout[972]), int(p1.stdout[997]), int(p1.stdout[1022])
				cons = Treelevelunitarity==1 and Perturbativity==1 and Stability==1
				l1 = float(p1.stdout[729:741])
				l2 = float(p1.stdout[753:766])
				l3 = float(p1.stdout[778:790])
				l4 = float(p1.stdout[802:814])
				l5 = float(p1.stdout[826:838])
			else:
				S, T, U = float(p1.stdout[1058:1070]), float(p1.stdout[1085:1097]), float(p1.stdout[1112:1124])
				Treelevelunitarity, Perturbativity, Stability = int(p1.stdout[971]), int(p1.stdout[996]), int(p1.stdout[1021])
				cons = Treelevelunitarity==1 and Perturbativity==1 and Stability==1
				l1 = float(p1.stdout[729:741])
				l2 = float(p1.stdout[753:765])
				l3 = float(p1.stdout[777:789])
				l4 = float(p1.stdout[801:813])
				l5 = float(p1.stdout[825:837])
		else:
			S, T, U = float(p1.stdout[1056:1068]), float(p1.stdout[1083:1095]), float(p1.stdout[1110:1122])
			Treelevelunitarity, Perturbativity, Stability = int(p1.stdout[969]), int(p1.stdout[994]), int(p1.stdout[1019])
			cons = Treelevelunitarity==1 and Perturbativity==1 and Stability==1
			l1 = float(p1.stdout[727:739])
			l2 = float(p1.stdout[751:763])
			l3 = float(p1.stdout[775:787])
			l4 = float(p1.stdout[799:811])
			l5 = float(p1.stdout[823:835])

		X_STU = [S, T, U]
		L2t_STU = C_STU_inv.dot(X_STU-CEN_STU).dot((X_STU-CEN_STU).T)

		C = get_CGa(mHpm=mHpm, a=a, tb=tb, b=b, sinba=sinba, cosba=cosba, l1=l1, l2=l2, l3=l3, l4=l4, l5=l5)
		myXML_user_input = usrXMLinput(mass=hmass, CV=C[0], CU=C[1], CD=C[2], CGa=C[3], precision=my_precision)
		lilithcalc.computelikelihood(userinput=myXML_user_input)
		L2t_a_tb = lilithcalc.l

		L2t = L2t_STU + L2t_a_tb

		if cons == False and grid == True:
			L2t = m2logLmax
		if cons == False and grid == False:
			L2t = L2t + penalty

		return L2t


######################################################################
# Scan
######################################################################

#bestfit=[]

print("***** running scan *****", flush=True)

def funcmulti(iteration):

	# Prepare output
	fresults = open(output[iteration], 'w')
	i=0
	mH = mHlist[iteration]

	for mA in np.linspace(mA_min, mA_max, mA_precision):

		if i==1 and iteration == 0:
			print("mA = ", mA, flush=True)
			print("time = ", time.perf_counter()-start, flush=True)
		if i%(mA_precision/10)==0 and iteration == 0:
			print("mA = ", mA, flush=True)
		i+=1
		m2logLmingrid=m2logLmax

		if ( 200 <= mH <= 600 and mA > 900 ) or ( 600 < mH <= 700 and mA > 1000 ) or ( 700 < mH <= 800 and 500 < mA < 1100 == False) or ( 800 < mH <= 900 and mH - 100 < mA < mH + 300 == False ) or ( 900 < mH <= 2000 and mH - 100 < mA < mH + 200 == False ):
			fresults.write('%.2f    '%mH + '%.2f    '%mA + 'nan    ' + 'nan    ' + 'nan    ' + 'nan    ' + 'nan    ')
			fresults.write('\n')
			continue

		for mHpm_cons in np.linspace(mHpm_min, mHpm_max, mHpm_precision):

			if ( 200 <= mH < 800 and mHpm_cons > mH + 100 or mHpm_cons > mA + 100) or ( 800 <= mH <= 2000 and mH - 100 < mHpm_cons < mH + 100 == False or mA - 200 < mHpm_cons < mA + 100 == False ):
				continue

			for a_cons in np.linspace(a_min, a_max, a_precision):
				for tb_cons in np.linspace(tb_min, tb_max, tb_precision):

					if ( abs(np.sin(np.arctan(tb_cons) - a_cons)) <= 0.9 ) or ( mHpm_cons >= 400 and abs(np.sin(np.arctan(tb_cons) - a_cons)) <= 0.95 ):
						continue

					m2logL = func(X=[mHpm_cons, a_cons, tb_cons], mH=mH, mA=mA, grid=True)
					if m2logL < m2logLmingrid:
						m2logLmingrid = m2logL
						mHpm0 = mHpm_cons
						a0 = a_cons
						tb0 = tb_cons

		if m2logLmingrid==m2logLmax:
			fresults.write('%.2f    '%mH + '%.2f    '%mA + 'nan    ' + 'nan    ' + 'nan    ' + 'nan    ' + 'nan    ')
			fresults.write('\n')
			continue

		grid = False
		funcminimized = minimize(func, [mHpm0,a0,tb0], args=(mH, mA, grid), method='migrad', bounds=((mHpm_min,mHpm_max),(a_min,a_max),(tb_min,tb_max)), options={'stra': strategy})
		m2logL = funcminimized.fun
		fit = funcminimized.x
		sinbafit = np.sin(np.arctan(fit[2]) - fit[1])
		fresults.write('%.2f    '%mH + '%.2f    '%mA + '%.5f    '%m2logL + '%.3f    '%fit[0] + '%.3f    '%fit[1] + '%.3f    '%fit[2] + '%.3f    '%sinbafit)
		fresults.write('\n')	

		if iteration == 0 and mA is not mA_max:
			print("time = ", time.perf_counter()-start, flush=True)

	if iteration == 0:
		print("mA = ", mA, flush=True)
		print("time = ", time.perf_counter()-start, flush=True)

	print("mH = ", mH, " : done")

	fresults.close()

######################################################################
# Multiprocessing
######################################################################

start = time.perf_counter()

if __name__ == '__main__':
	pool = Pool()
	pool.map(funcmulti, iterationlist)

stop = time.perf_counter()

print("***** scan finalized *****", flush=True)

print("time = ", stop-start, flush=True)

fresultsfinal = open(outputfinal, 'w')
for i in iterationlist:
	fresults = open(output[i])
	content = fresults.read()
	fresultsfinal.write(content+"\n")
	fresults.close()

fresultsfinal.close()

######################################################################
# Plot routine
######################################################################

#print("***** plotting *****", flush=True)

## Preparing plot
#matplotlib.rcParams['xtick.major.pad'] = 8
#matplotlib.rcParams['ytick.major.pad'] = 8

#fig = plt.figure( figsize=(5,5) )
#ax = fig.add_subplot(111)

#ax.yaxis.set_ticks_position('both')
#ax.yaxis.set_label_position('left')

#ax.xaxis.set_ticks_position('both')
#ax.xaxis.set_label_position('bottom')

#plt.minorticks_on()
#plt.tick_params(direction='in', labelsize=14, length=10, width=2)
#plt.tick_params(which='minor', direction='in', length=7, width=1.2)


## Getting the data
#data = np.genfromtxt(outputfinal)

#x = data[:,0]
#y = data[:,1]
#z = data[:,2]


## Substracting the -2LogL minimum to form Delta(-2LogL)
#z2=[]
#for z_el in z:
#  z2.append(z_el-np.nanmin(z))

## Interpolating the grid
#xi = np.linspace(x.min(), x.max(), mH_precision)
#yi = np.linspace(y.min(), y.max(), mA_precision)

#X, Y = np.meshgrid(xi, yi)
#Z = griddata((x, y), z2, (X, Y), method="linear")

## Plotting
#sc = ax.scatter(x, y, c=z2, vmin=0, vmax=1000000, cmap="jet_r")
#cbar = fig.colorbar(sc,fraction=0.046, pad=0.04)
#cbar.set_label("$\Delta (-2\log L)$", fontsize=10)

#ax.set_aspect((mH_max-mH_min)/(mA_max-mA_min))

## best fit point
##plt.plot([data[-1,0]],[data[-1,1]], '+', markersize=8, color = 'black', label = 'best fit')
##plt.legend(loc='upper right')

## Title, labels, color bar...
#plt.xlabel(r'$m_H$[GeV]',fontsize=16)
#plt.ylabel(r'$m_A$[GeV]',fontsize=16)
##plt.text(mH_min + 100, mA_max - 150, r'Values from 2HDMc with unit, pert and stab conditions', fontsize=7)
##plt.text(mH_min + 100, mA_max - 250, r'Contour plot in the $m_H$, $m_A$ plane with $m_{H^{\pm}}$ minimized at each point', fontsize=7)
##plt.text(mH_min + 100, mA_max - 350, fr"Range of $m_{{H^{{\pm}}}}$ = ({mHpm_min},{mHpm_max}), with $\cos(\beta - \alpha) = 0$", fontsize=7)
##plt.text(mH_min + 100, mA_max - 450, fr"Best point ($m_H, m_A$) = ({data[-1,0]:.0f}, {data[-1,1]:.0f}) with $\chi^{2}$ = {data[-1,2]:.3f} and $m_{{H^{{\pm}}}}$ = {data[-1,3]:.0f}", fontsize=7) 
##plt.text(-360, 255, f"with $\chi^{2}$ = {m2logLmin:.3f}, S = {calc.Scalc(mh = 125, mH = mHmin + my_mHpm, mA = mAmin + my_mHpm, mHpm = my_mHpm, sinba = 1):.3f}, T = {calc.Tcalc(mh = 125, mH = mHmin + my_mHpm, mA = mAmin + my_mHpm, mHpm = my_mHpm, sinba = 1):.3f}", fontsize=9)
##plt.text(-360, 205, f"CDF Best points ($\Delta m_H, \Delta m_A$) = (396, 24)", fontsize=9)
##plt.text(-360, 175, f"with $\chi^{2}$ = 3.04, S = 0.01, T = 0.173", fontsize=9)

#fig.set_tight_layout(True)

## Saving figure (.pdf)
#fig.savefig(outputplot)

#print("results are stored in", validation_dir, flush=True)
#print("***** done *****", flush=True)
