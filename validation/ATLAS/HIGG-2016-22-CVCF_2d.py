###############################################################
#
# Lilith routine for (CV, CF) validation plots
#
# To run from /Lilith-1.x root folder
#
# Use the libraries matplotlib (plotting) and numpy (functions)
#
###############################################################

import sys, os
from matplotlib.mlab import griddata
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

lilith_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(lilith_dir)
sys.path.append('../..')
import lilith

######################################################################
# Parameters
######################################################################

print "***** reading parameters *****"

# Experimental results
exp_input = "data4validation/validation.list"
# Lilith precision mode
my_precision = "BEST-QCD"

# Higgs mass to test
hmass = 125.09

# Output file
output = "validation/ATLAS/CVCF_2d.out"
# Output plot
outputplot = "validation/ATLAS/CVCF_2d.pdf"


# Range of the scan
CV_min = 0.6
CV_max = 2.0
CF_min = 0.
CF_max = 3.5

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

print "***** scan initialization *****"

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

print "***** running scan *****"

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

print "***** scan finalized *****"
print "minimum at CV, CF, -2logL_min = ", CVmin, CFmin, m2logLmin

######################################################################
# Plot routine
######################################################################


print "***** plotting *****"

# Preparing plot
matplotlib.rcParams['xtick.major.pad'] = 15
matplotlib.rcParams['ytick.major.pad'] = 15

fig = plt.figure()
ax = fig.add_subplot(111)

plt.minorticks_on()
plt.tick_params(labelsize=20, length=14, width=2)
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
Z = griddata(x, y, z2, xi, yi, interp="linear")

# Plotting the 68%, 95% and 99.7% CL regions

ax.contourf(xi,yi,Z,[10**(-10),2.3,5.99,11.83],colors=['#ff3300','#ffa500','#ffff00'], \
              vmin=0, vmax=20, origin='lower', extent=[x.min(), x.max(), y.min(), y.max()])


### Once more for 4d rounded values ###
#data2 = np.genfromtxt("validation/ATLAS/HIGG-2016-22-4ddata-CVCF_2d.out")

#xp = data2[:,0]
#yp = data2[:,1]
#zp = data2[:,2]

#z2p=[]
#for z_el in zp:
#  z2p.append(z_el-zp.min())

#xip = np.linspace(xp.min(), xp.max(), grid_subdivisions)
#yip = np.linspace(yp.min(), yp.max(), grid_subdivisions)

#Xp, Yp = np.meshgrid(xip, yip)
#Zp = griddata(xp, yp, z2p, xip, yip, interp="linear")

#ax.contour(xip,yip,Zp,[2.3,5.99],linewidths=[1.2,1.2],linestyles=['solid','dashed'],colors=["darkred","darkred"])
#################

ax.set_aspect((CV_max-CV_min)/(CF_max-CF_min))

plt.plot([CVmin],[CFmin], '*', c='w', ms=10)
plt.plot([1],[1], '+', c='k', ms=10)

#  official ATLAS result
dt = np.dtype([('cx', float), ('cy', float)])
expCont = np.genfromtxt('validation/ATLAS/HIGG-2016-22-CVCF-2d-Grid.txt', dtype=dt)
plt.plot(expCont['cx'],expCont['cy'], '.', c='b', label='ATLAS official')

plt.legend(loc='lower right', fontsize=12)

# Title, labels, color bar...
plt.title("  Lilith-"+str(lilith.__version__)+", DB "+str(lilithcalc.dbversion), fontsize=14.5, ha="left")
plt.xlabel(r'$C_V$',fontsize=25)
plt.ylabel(r'$C_F$',fontsize=25)
plt.text(0.7, 3.1, r'Data from ATLAS-HIGG-2016-22', fontsize=13)
plt.text(1.24, 2.8, r'ggH: Aux.Fig. 7a (Poisson)', fontsize=12)
plt.text(1.24, 2.62, r'VBF: Aux.Fig. 7b (Poisson)', fontsize=12)
#plt.text(1.24, 2.8, r'ggH: Aux.Fig. 7a (VGauss)', fontsize=12)
#plt.text(1.24, 2.62, r'VBF: Aux.Fig. 7b (VGauss)', fontsize=12)
plt.text(1.24, 2.44, r'correlation: -0.41', fontsize=12)
plt.text(1.38, 2.18, r'VH, ttH from Table 9', fontsize=12)
#plt.text(1.32, 2.8, r'Table 9 + Aux.Fig. 4c', fontsize=12)
#plt.text(1.32, 2.62, r'(ggH, VBF: 2D Poisson)', fontsize=12)
#plt.text(1.32, 2.62, r'(ggH, VBF: 2D VGauss)', fontsize=12)
#plt.text(1.32, 2.62, r'(4D var. Gaussian)', fontsize=12)

#plt.text(0.58, 1.22, r'(testing)', fontsize=13)

#plt.tight_layout()
fig.set_tight_layout(True)

# Saving figure (.pdf)
#plt.savefig(outputplot)
fig.savefig("validation/ATLAS/HIGG-2016-22-CVCF-2d-p2.pdf")


