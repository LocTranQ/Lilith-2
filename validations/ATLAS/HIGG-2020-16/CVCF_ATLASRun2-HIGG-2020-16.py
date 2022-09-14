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
exp_input = "validations/ATLAS/HIGG-2020-16/LatestRun2.list"

# Lilith precision mode
my_precision = "BEST-QCD"

# Higgs mass to test
hmass = 125.38

# Output files
if (not os.path.exists("results")):
    os.mkdir("results")
output = "validations/ATLAS/HIGG-2020-16/CVCF-HIGG-2020-16-cor.out"
#outputplot = "validations/ATLAS/HIGG-2020-16/CVCF-HIGG-2020-16-cor.pdf"
outputplot = "validations/ATLAS/HIGG-2020-16/CVCF-HIGG-2020-16.pdf"

# Scan ranges
CV_min = 0.85
CV_max = 1.2
CF_min = 0.6
CF_max = 1.6
# Number of grid steps in each of the two dimensions (squared grid)
grid_subdivisions = 100

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


######################################################################
# Scan routine
######################################################################

m2logLmin=10000
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

# Import Official data from csv file 
#dataload = open('validations/CMS/HIG-22-001/CMS-HIG-22-001-Run2-official.csv','r')
#dorix = []
#doriy = []
#for line in dataload:
#  fdat = line.split(',')
#  dorix.append(float(fdat[0]))
#  doriy.append(float(fdat[1]))

# Import Official data from file 
dataload = open('validations/ATLAS/HIGG-2020-16/HIGG-2020-16.csv','r')
dorix = []
doriy = []
for line in dataload:
  fdat = line.split(',')
  dorix.append(float(fdat[0]))
  doriy.append(float(fdat[1]))
   
# Plotting the 68%, 95% and 99.7% CL regions
ax.contourf(xi,yi,Z,[10**(-10),2.3,5.99],colors=['#ff3300','#ffa500'], \
              vmin=0, vmax=20, origin='lower', extent=[x.min(), x.max(), y.min(), y.max()])

ax.set_aspect((CV_max-CV_min)/(CF_max-CF_min))

# best fit point
plt.plot([CVmin],[CFmin], '*', c='w', ms=10)

# Standard Model 
plt.plot([1],[1], '+', c='k', ms=10)

# Plotting the Offical contours 
plt.scatter(dorix,doriy,s=3,c='b',marker='o',label='ATLAS official')    
plt.legend(loc='lower right', scatterpoints = 3) 

# best fit point
plt.plot([1.0183206106870228],[1.0045454545454544], 'o', c='b', ms=3)

# Title, labels, color bar...
plt.title("  Lilith-2.1, ATLAS HIGG-2020-16 validation" , fontsize=12, ha="center")
plt.xlabel(r'$C_V$',fontsize=20)
plt.ylabel(r'$C_F$',fontsize=20)
plt.text(0.86, 1.5, r'Exp. input type = vn1', fontsize=12, ha = 'left')

fig.set_tight_layout(True)

#plt.show()

# Saving figure (.pdf)
fig.savefig(outputplot)

print("results are stored in", lilith_dir + "/results")
print("***** done *****")

