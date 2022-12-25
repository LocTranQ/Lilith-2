##################################################################
#
# Lilith routine example for (CV, CF)  plots
#
# To put in Lilith-2.X/examples/python/ folder 
# To execute from /Lilith-2.X root folder
#
# Use the libraries matplotlib (plotting) and numpy (functions)
#
##################################################################

import sys, os
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

lilith_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(lilith_dir)
sys.path.append('../..')
import lilith

######################################################################
# Parameters
######################################################################

print("***** reading parameters *****")

# Experimental results
exp_input = "validations/ATLAS/HIGG-2018-57/LatestRun2.list"
# Sm predictions     
smpred_input = "validations/ATLAS/HIGG-2018-57/SMPrediction-dim19.txt"
#smbin_corr_input = "validations/ATLAS/HIGG-2018-57/SMbin-corr.txt" 
#smbin_corr_input = "validations/ATLAS/HIGG-2018-57/SMbin-corr2017-scheme.txt" 
#smbin_corr_input = "validations/ATLAS/HIGG-2018-57/SMbin-corrJVE.txt" 
#smbin_corr_input = "validations/ATLAS/HIGG-2018-57/SMbin-corrSTXS.txt" 
smbin_corr_input = "validations/ATLAS/HIGG-2018-57/SMbin-corrWG1.txt" 

# Lilith precision mode
my_precision = "BEST-QCD"

# Higgs mass to test
hmass = 125.38

# Output files
if (not os.path.exists("results")):
    os.mkdir("results")
output = "validations/ATLAS/HIGG-2018-57/CVCF-HIGG-2018-57.out"
#outputplot = "validations/ATLAS/HIGG-2018-57/CVCF-HIGG-2018-57-noSMerr.pdf"
#outputplot = "validations/ATLAS/HIGG-2018-57/CVCF-HIGG-2018-57-stxs-ZZ.pdf"
outputplot = "validations/ATLAS/HIGG-2018-57/CVCF-HIGG-2018-57--stxs-Corr-WG1.pdf"

# Scan ranges
CV_min = 0.9
CV_max = 1.2
CF_min = 0.7
CF_max = 1.4
# Number of grid steps in each of the two dimensions (squared grid)
grid_subdivisions = 50

######################################################################
# * usrXMLinput: generate XML user input
######################################################################

def usrXMLinput(mass=125.09, CV=1, CF=1, precision="BEST-QCD"):
    """generate XML input from reduced couplings CV, CF"""
    
    myInputTemplate = """<?xml version="1.0"?>

<lilithinput>

<reducedcouplings>
  <mass>%(mass)s</mass>

  <C to="tt">%(CF)s</C>
  <C to="bb">%(CF)s</C>
  <C to="cc">%(CF)s</C>
  <C to="tautau">%(CF)s</C>
  <C to="ZZ">%(CV)s</C>
  <C to="WW">%(CV)s</C>

  <extraBR>
    <BR to="invisible">0.</BR>
    <BR to="undetected">0.</BR>
  </extraBR>

  <precision>%(precision)s</precision>
</reducedcouplings>

</lilithinput>
"""
    myInput = {'mass':mass, 'CV':CV, 'CF':CF, 'precision':precision}
        
    return myInputTemplate%myInput

######################################################################
# Scan initialization
######################################################################

print("***** scan initialization *****")

# Prepare output
fresults = open(output, 'w')

# Initialize a Lilith object
lilithcalc = lilith.Lilith(verbose=False,timer=False)
# Read experimental data
lilithcalc.readexpinput(exp_input)

# Read SM prediction input and correlation 

lilithcalc.readsmpred(smpred_input)
lilithcalc.readsmcorr(smbin_corr_input)
######################################################################
# Scan routine
######################################################################

m2logLmin=10000000000
max=-1

print("***** running scan *****")

for CV in np.linspace(CV_min, CV_max, grid_subdivisions):
    fresults.write('\n')
    for CF in np.linspace(CF_min, CF_max, grid_subdivisions):
        myXML_user_input = usrXMLinput(hmass, CV=CV, CF=CF, precision=my_precision)
        lilithcalc.computelikelihood(userinput=myXML_user_input)
        m2logL = lilithcalc.l
        if m2logL < m2logLmin:
            m2logLmin = m2logL
            CVmin = CV
            CFmin = CF
        fresults.write('%.5f    '%CV +'%.5f    '%CF + '%.5f     '%m2logL + '\n')

fresults.close()

print("***** scan finalized *****")
print("minimum at CV, CF, -2logL_min = ", CVmin, CFmin, m2logLmin)

######################################################################
# Plot routine
######################################################################


print("***** plotting *****")

# Preparing plot
matplotlib.rcParams['xtick.major.pad'] = 15
matplotlib.rcParams['ytick.major.pad'] = 15

fig = plt.figure()
ax = fig.add_subplot(111)

plt.minorticks_on()
plt.tick_params(labelsize=15, length=14, width=2)
plt.tick_params(which='minor', length=7, width=1.2)


# Getting the data
data = np.genfromtxt(output)

x = data[:,0]
y = data[:,1]
z = data[:,2]

# Substracting the -2LogL minimum to form Delta(-2LogL)
z2=[]
for z_el in z:
  z2.append(z_el-z.min())

# Interpolating the grid
xi = np.linspace(x.min(), x.max(), grid_subdivisions)
yi = np.linspace(y.min(), y.max(), grid_subdivisions)

X, Y = np.meshgrid(xi, yi)
Z = griddata((x, y), z2, (X, Y), method="linear")

# Import Official data from file 
dataload = open('validations/ATLAS/HIGG-2018-57/HIGG-2018-57-official.csv','r')
dorix = []
doriy = []
for line in dataload:
  fdat = line.split(',')
  dorix.append(float(fdat[0]))
  doriy.append(float(fdat[1]))
   

   
# Plotting the 68%, 95% and 99.7% CL regions
ax.contourf(xi,yi,Z,[10**(-10),2.3,5.99,11.83],colors=['#ff3300','#ffa500','#ffff00'], \
              vmin=0, vmax=20, origin='lower', extent=[x.min(), x.max(), y.min(), y.max()])

ax.set_aspect((CV_max-CV_min)/(CF_max-CF_min))

# best fit point
plt.plot([CVmin],[CFmin], '*', c='w', ms=10)

# Standard Model 
plt.plot([1],[1], '+', c='k', ms=10)

# Plotting the Offical contours 
plt.scatter(dorix,doriy,s=4,c='b',marker='o',label='ATLAS official ')    
plt.legend(loc='lower right', scatterpoints = 3) 
# best fit point
plt.plot([1.053485254691689],[1.0492700729927007], 'o', c='b', ms=3)

# Title, labels, color bar...
plt.title("  Lilith-2.1, ATLAS HIGG-2018-57 STXS" , fontsize=12, ha="center")
plt.xlabel(r'$C_V$',fontsize=20)
plt.ylabel(r'$C_F$',fontsize=20)
plt.text(0.91, 1.30, r'Exp. input type = vn', fontsize=9, ha = 'left')
#plt.text(0.91, 1.30, r'No SM error', fontsize=9, ha = 'left')
plt.text(0.91, 1.35, r'WG1-ggF theo. corr.', fontsize=9, ha = 'left')
#plt.text(0.91, 1.30, r'approx 2 of correlation, gamma = 5.0', fontsize=9, ha = 'left')

fig.set_tight_layout(True)

#set aspect ratio to 0.618
ratio = 0.85
x_left, x_right = ax.get_xlim()
y_low, y_high = ax.get_ylim()
ax.set_aspect(abs((x_right-x_left)/(y_low-y_high))*ratio)

#plt.show()

# Saving figure (.pdf)
fig.savefig(outputplot)

print("results are stored in", lilith_dir + "/results")
print("***** done *****")

