import numpy as np
import ase.io
from ase.calculators.espresso import Espresso
import os

################################
# QE options
################################

pseudopotentials = {'Si': 'Si_ONCV_PBE-1.0.upf'}

input_qe = {
            'calculation':'scf',
            'outdir': './',             
            'pseudo_dir': './',         
            'tprnfor': '.true.',        
            'tstress': '.true.',        
            'disk_io':'none',
            'system':{
              'ecutwfc': 30,
              'input_dft': 'PBE',
             },
            'electrons':{
               'mixing_beta': 0.5,
               'electron_maxstep':1000,
             },
}


os.system('mkdir extracted-confs')

#################################
# Load trajectory
#################################

traj=ase.io.read('si.lammps-dump-text',format='lammps-dump-text',index=':')
step=1
counter1=0 # Number of configurations written
counter2=0 # Frame number
for conf in traj:
   if ((counter2%step)==0):
      species=np.array(conf.get_chemical_symbols())
      species=np.full(shape=species.shape,fill_value="Si")
      conf.set_chemical_symbols(species)
      ase.io.write('extracted-confs/pw-si-' + str(counter1) + '.in',conf, format='espresso-in',input_data=input_qe, pseudopotentials=pseudopotentials)
      counter1 += 1
   counter2 += 1
