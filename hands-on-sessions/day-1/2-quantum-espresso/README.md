# Basics of DFT Calculations with Quantum-ESPRESSO

Designed and written by Zachary K. Goldsmith and Taehun Lee, Princeton University

Hands-on sessions - Day 1 - July 11, 2023

Fundamentals of using Quantum-ESPRESSO for plane-wave DFT calculations of extended systems.

## Aims
This tutorial will demonstrate basic usage of the PW module of Quantum-ESPRESSO (QE), a leading open-source software for electronic structure, focusing on the practical significances of key computational parameters and using crystalline Si as an example. This is intended as a practical tutorial for those who have not performed DFT calculations with QE in the past and will not cover the underlying physics and chemistry concepts. This exercise will cover how to benchmark and conduct ground state DFT simulations of periodic systems and extract results of relevance to the training of deep neural network potentials.

## Objectives

This tutorial will cover the following:
- Necessary files and scripts for running QE calculations
- Anatomy of the QE input file 
- Submitting QE jobs
- Parsing and understanding QE output
- Exercises:
  - Benchmarking DFT parameters
  - Geometry relaxation

## Prerequisites

It is assumed that the participant has a general understanding of quantum mechanical calculations, proficiency with the linux command line, and basic level python scripting. Additional experience with plane-wave basis sets, crystal structure, and other solid-state physics concepts will also be helpful. This tutorial is furthermore written for Workshop participants who will have access to virtual machines which have QE v7.1. with GPU acceleration compiled. Instructions for downloading and compiling QE can be found at https://github.com/QEF/q-e.

The QE input and output files will be generated, maintained and parsed using [Atomic Simulation Environment (ASE)](https://wiki.fysik.dtu.dk/ase/index.html) which is written in the Python programming language with the aim of setting up, steering, and analyzing atomistic simulations.

## Running a DFT Calculation with QE

Running jobs with the PWSCF module of QE requires at minimum: 

1) The `pw.x` executable and its corresponding environment
2) Pseudopotentials in UPF format 
3) An input file

As mentioned previously, the `pw.x` executable and environment are readily available to participants with access to the VM. You will learn how to execute QE in the VM later. Otherwise, follow the instructions for downloading and compiling QE on your machine.

Different types of pseudopotentials and their underlying physics are beyond the scope of this tutorial, but there are many publically available pseudopotential libraries. This tutorial will utilize an [ONCV pseudopotential](http://quantum-simulation.org/potentials/sg15_oncv/upf/ "ONCV psp library") for Si optimized for PBE calcultions. To retrieve this pseudopotential do the following:

```
wget http://quantum-simulation.org/potentials/sg15_oncv/upf/Si_ONCV_PBE-1.0.upf
```

Now we will begin by dissecting the QE input file using bulk Si as an example.

### Input file anatomy

The all-in-one guide for PWscf keywords is [here](https://www.quantum-espresso.org/Doc/INPUT_PW.html). This tutorial will address many of the most basic specifications.

Let's take a look at the file `si.in` located in this head directory, starting with the `&control` namelist:

```
 &control
   restart_mode = 'from_scratch',
   calculation  = 'scf',
   prefix       = 'si',
   outdir       = './',
   pseudo_dir = './',
   tprnfor = .true.,
 /
```
Start by noting the formatting of namelists; the `&` starts the namelist and the `/` terminates it. Keywords are separated by commas (and for our convenience but not necessarily, line breaks). `restart_mode = 'from_scratch',` implies that we are starting a calcualtion from scratch rather than restarting. `calculation  = 'scf',` entails that we are running a single-point self-consistent field (SCF) energy calculation. The prefix keyword sets the nomenclature for all output files. The `outdir` and `pseudo_dir` keywords specify the desired location of the outputs and pseudopotentials, respectively. In both cases, that will be the present directory `./`. Lastly, and importantly for DPMD applications `tprnfor = .true.,` will ensure that the atom-centered forces will be printed in the QE output.

Next, let's look at the `&system` namelist:

```
 &system
    ibrav=2,
    celldm(1) = 10.20,
    nat=2,
    ntyp=1,
    ecutwfc=24.0
    input_dft='pbe'
 /
```
`ibrav=2` indicates that our system has cubic FCC structure and symmetry, with `celldm(1)` defining the relevant lattice vector in au (bohr). QE's algorithms exploit crystal symmetries to accelerate calculations. 

`Xcrysden` can be used to visualize QE input and output files directly. With the corresponding symmetry, you can visualize both the conventional and primitive unit cells. On a machine with `Xcrysden` loaded, go to the directory of `si.in` and do: 

```
xcrysden --pwi si.in
```

![image](https://user-images.githubusercontent.com/59068990/176943208-9a82fdb4-4c79-4393-872e-769a85220924.png)

There are several programs available for visualizing atomic structures. Here are some available options: [VESTA](vesta), [Ovito](vesta), [ASE gui-view](vesta) or python-based [ngl viewer](test). However, those programs cannot directly visualize the QE input and output files calculations. To visualize the structures, you need to convert the QE input/output files to relevant structure file formats such as CIF, POSCAR (VASP), or XYZ.

NB: Crystal structure is beyond the scope of this tutorial, however, it is worth mentioning that non-crystalline (i.e. liquid, gaseous, interfacial) systems will use the `ibrav=0` option, in which the 3 x 3 lattice parameters must be specified explicitly. For an orthorhombic cell, all the off-diagonal elements would be zero. 

Straightforwardly, `nat` refers to the number of atoms and `ntyp` is the number of types of atoms. `ecutwfc` refers to the cutoff energy of the basis set planewaves. The higher this value, the more planewaves that are used, resulting in a slower, but more accurate calculation. We will explore the benchmarking of this value shortly. Lastly, `input_dft` indicates the DFT functional to be used in the calculation. The default value of this is the functional associated with the pseudopotential, so we wouldn't need to explicitly state this value in our case since we are using PBE, but it is included here to demonstrate where one would indicate the usage of e.g. SCAN functional.

Next is `&electrons`:

```
 &electrons
    conv_thr    = 1.D-6,
    mixing_beta = 0.5D0,
    startingwfc = 'atomic+random',
    startingpot = 'atomic',
 /
```

`conv_thr` is the energy convergence threshold for the SCF calculation. For the purposes of this tutorial we will leave it at the default. Lower values may be justifiable for larger systems further from equilibrium and/or to have an initial converged solution on which to improve. The `mixing_beta` parameter is an internal one related to the step-to-step perturbation of the trial wavefunction. We will not modify it in this tutorial but it is worth mentioning that smaller values typically yield slower but more stable paths to convergence. The `startingwfc` and `startingpot` are the initial wavefuncitons and potentials, respectively. We will not be modifying these keywords in this tutorial.

Lastly we come to the cards (note that these are not namelists and have different syntax) associated with the structure and k-points:

```
ATOMIC_SPECIES
 Si  28.086  Si_ONCV_PBE-1.0.upf
ATOMIC_POSITIONS (crystal)
 Si 0.00 0.00 0.00
 Si 0.25 0.25 0.25
K_POINTS automatic
 4 4 4 1 1 1
```
`ATOMIC_SPECIES` indicates the only species, Si, along with its atomic mass and the name of the corresponding pseudopotential file.

`ATOMIC_POSITIONS` is formatted in a familiar way: the type of atom and its 3D coordinates. In this input file we are exploiting the cubic symmetry so the positions are in units of the lattice vector, denoted by `alat`. This can be modified to `Angstrom` for non-symmetric systems. The two Si atoms form the basis of the cubic diamond crystal structure.

Last, `K_POINTS` refers to the sampling of the Brillouin Zone performed in the calculation. The technical details here are beyond the scope of this tutorial but we will investigate the need to benchmark this value. 

### Input file generation using ASE-calculator
To generate the QE input file using the ASE calculator module, you need to load the relevant module. You can see more examples [here](https://wiki.fysik.dtu.dk/ase/ase/calculators/espresso.html#module-ase.calculators.espresso).

```
from ase.io import read, write
from ase.calculators.espresso import Espresso
```

```
pseudopotentials = {'Si': 'Si_ONCV_PBE_sr.upf'}

# Define the input parameters for the QE calculation
input_qe = {
    'calculation': 'scf',             # Type of calculation (self-consistent field)
    'outdir': './',                   # Output directory
    'pseudo_dir': './',               # Directory for pseudopotential files
    'tprnfor': True,                  # Print forces in output
    'tstress': True,                  # Print stress tensor in output
    'disk_io': 'none',                # Disable disk I/O
    'system': {
        'ecutwfc': 40,                # Cutoff energy for wavefunctions (40 Ry)
        'input_dft': 'PBE',           # Exchange-correlation functional (PBE)
    },
    'electrons': {
        'mixing_beta': 0.5,           # Mixing parameter for electron density (0.5)
        'electron_maxstep': 1000      # Maximum number of electron iterations (1000)
    },
}

kpoints = (4, 4, 4)                    # K-point mesh size
offset = (1, 1, 1)                     # Offset for the k-point mesh
```
The given code defines two dictionaries, `pseudopotentials` and `input_qe`, which are used to set up parameters for a QE calculation, as explained previously. These dictionaries provide the necessary input parameters for configuring a QE calculation using the specified pseudopotentials and system parameters. It's important to note that the code does not explicitly define variables for the default settings. The variables `kpoints` and `offset` are used to define the k-points grid in the calculations.

Instead of manually setting the crystal structure, you can utilize the ASE Atoms object, which stores information about the chemical and crystal structure of a system. By defining the ASE Atoms object, you can automatically set QE flags related to the chemical and crystal structure, such as `nat`, `ntyp`, `ibrav`, and generate the necessary `ATOMIC_SPECIES` and `ATOMIC_POSITIONS` cards in the QE input file. 

You can define an ASE Atoms object for bulk Si by either manually setting the structure or loading a CIF file or relevant structure files. In this case, we will load a CIF file obtained from the [Materials Project](https://next-gen.materialsproject.org) or other relevant materials database.

```
from ase.io import read

# Load the CIF file using ASE's read() function
bulk_si = read('Si.cif')

# Print the ASE Atoms object
print(bulk_si)
```

Now, you can generate the QE input file using the provided dictionary and variables:
```
ase.io.write('pw-si.in', bulk_si, format='espresso-in',input_data=input_qe, pseudopotentials=pseudopotentials, kpts=kpoints, koffset=offset)
```
This code will generate the QE input file named `pw-si.in` based on the ASE Atoms object `bulk_si`, using the specified input parameters, pseudopotentials, k-points, and offset values. You can find the compiled Python script named `bulk_si.py` in the tutorial folder. You can run the script by typing `python bulk_si.py`.

### Running QE jobs

With all of our necessary components ready, we can now proceed to run a simple QE job. In the VM, we will execute this job on computing cluster at Princeton University, utilizing the scheduler, Slurm. The sample job script is placed in the tutorial folder as named job.sh. The compiled QE version in the VM is v7.1. with GPU acceleration which is installed using container, [singularilty](https://sylabs.io). Containers store the software and all of its dependencies, making it easy to install and run the software.

```
#!/bin/bash
#SBATCH --job-name=si            # Create a short name for your job
#SBATCH --nodes=1                # Number of nodes
#SBATCH --ntasks-per-node=4      # Number of tasks per node
#SBATCH --cpus-per-task=1        # Number of CPU cores per task (>1 if multi-threaded tasks)
#SBATCH --mem=32G                # Total memory per node
#SBATCH --gres=gpu:1             # Number of GPUs per node
#SBATCH --time=00:15:00          # Total run time limit (HH:MM:SS)

module purge
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

srun --mpi=pmi2 \
singularity run --nv \
     /scratch/gpfs/taehunl/program_della/qe_gpu/quantum_espresso_qe-7.0.sif \
     pw.x -input pw-si.in > pw-si.out
```

Let's start by running the calculation using the following command line:

```
sbatch job.sh
```
Once the calculation is executed, you will find the output written to the file `pw-si.out`.

### Parsing QE output

So, what happened when we ran the job? In summary, QE iteratively converged the eigenvectors and eigenvalues of the Si system starting from an initial guess. Before looking at details of the output file, let's check if the calculation has completed successfully. You can determine this by checking the end of the output file (`pw-si.out`) for the following completion message.

```
=------------------------------------------------------------------------------=
   JOB DONE.
=------------------------------------------------------------------------------=
```

To see the total energy of the self-consistent field (SCF) calculation, you can open the output file and locate the character `!`. The lines following this total energy will provide information about its constituent terms, the number of iterations required for convergence, and the forces acting on each atom. In the case of Si at equilibrium, the forces should be zero. Note the structure is not at equilibrium since it was taken from the database, and not obtained with DFT structural optimization calculation.

```
!    total energy              =     -63.05588407 Ry
     estimated scf accuracy    <       0.00000033 Ry

     The total energy is the sum of the following terms:
     one-electron contribution =      18.77796821 Ry
     hartree contribution      =       4.42769964 Ry
     xc contribution           =     -19.23491580 Ry
     ewald contribution        =     -67.02663612 Ry

     convergence has been achieved in   5 iterations

     Forces acting on atoms (cartesian axes, Ry/au):

     atom    1 type  1   force =    -0.00000573   -0.00000573    0.00000573
     atom    2 type  1   force =     0.00000000    0.00000000    0.00000000
     atom    3 type  1   force =    -0.00000573    0.00000573   -0.00000573
     atom    4 type  1   force =     0.00000000    0.00000000    0.00000000
     atom    5 type  1   force =     0.00000573   -0.00000573   -0.00000573
     atom    6 type  1   force =     0.00000000    0.00000000    0.00000000
     atom    7 type  1   force =     0.00000573    0.00000573    0.00000573
     atom    8 type  1   force =     0.00000000    0.00000000    0.00000000

     Total force =     0.000020     Total SCF correction =     0.000467
     SCF correction compared to forces is large: reduce conv_thr to get better values
```

Let's also look at the progression of the calculation to convergence with:

```
grep "total energy              =" pw-si.out
```

You should see the energy decrease monotonically to the final energy. 

### Parsing QE output using ASE-calculator

You can also parse important physical and chemical quantities of QE output using the ASE module as follows:


```
## read QE output file
bulk_si_out = read('pw-si.out', format='espresso-out')  # Returns an Atoms object

## Print physical and chemical quantities
print('Atomic positions:   in angstrom')
print(bulk_si_out.get_positions())
print('Lattice vector  :   ', bulk_si_out.get_cell())
print('Total energy    :   ', round(bulk_si_out.get_potential_energy(),5), 'eV')
```
You can run the script by typing `python bulk_si.py`. ASE atoms object returns the total energy of the system in electron volts (eV), not Ry. Using the ASE module, you can access various physical quantities and chemical properties stored in the ASE calculator, such as volume, magnetic moment, eigenvalues, and occupations. Please explore the ASE documentation for a comprehensive list of available methods to access different physical and chemical properties stored in the ASE calculator.

## Exercises: Benchmarking and Geometry

### Benchmarking DFT protocol

It is critical that one benchmarks their DFT protocol, especially given that the accuracy of the DFT calculation is ultimately what a machine-learned potential will achieve with sufficient training. Here we will demonstrate how to benchmark two of the most important aspects of QE DFT: `ecutwfc` and the number of k-points.

1. `Ecutwfc`:

In plane-wave DFT calculations, one should use a plane-wave energy cutoff that is sufficiently high such that the computed energy for a sample system is stable with respect to this cutoff. In other words, we are exploring how the number of plane-waves (basis set size) affects the energy and time to solution. Move to the directory `ecut`. Therein you will find a Python script, `ecut.py`. Then, run the script to generate QE input files with different plane-wave energy cutoff values ranging from 10 to 60 Ry. The script sets up a range of cutoff energies for wavefunctions using the range() function and then loops over the cutoff energies and generates QE input files with different plane-wave energy cutoff values. Following is the highlight of the important part.

```
# Set up the range of cutoff energies for wavefunctions
wfcs = range(10, 70, 10)

# Loop over the cutoff energies and generate QE input files
for wfc in wfcs:
    input_qe = {
 	...
        'system': {
            'ecutwfc': wfc,         
        },
 	...
    }
    write('pw-si-' + str(wfc) + '.in', bulk_si, format='espresso-in', input_data=input_qe,
          pseudopotentials=pseudopotentials, kpts=kpoints, koffset=offset, tstress=True, tprnfor=True)
```
Accordingly, we should make a change in the job script file as well:

```
for i in `seq 10 10 60`
do
    srun --mpi=pmi2 \
    singularity run --nv \
        /scratch/gpfs/taehunl/program_della/qe_gpu/quantum_espresso_qe-7.0.sif \
        pw.x -input pw-si-$i.in -npool 2 > pw-si-$i.out
done
```

After the completion of calculations, let's examine the computed energies and their convergence. It is important to note that the energy decreases with increasing `ecutwfc` in the QE input file (or `wfc` variable in the Python file), but with diminishing returns at higher values. A properly benchmarked calculation would involve using an `ecutwfc` value beyond the point where the energy doesn't change significantly. To visualize this trend, you can plot `ecutwfc` versus `total energy` using a simple IPython script (`plot.ipython`). The ipython script For each cutoff energy, it reads the output file (`pw-si-<wfc>.out`) using ASE's read() function, returning the total energy. It will plot the energies versus the cutoff energies and save the plot as an image file (`ecut.png`).
Following is the image file:

<p float="left">
  <img src="https://github.com/CSIprinceton/workshop-july-2023/blob/6ed432411c4285a8dea9a77ce027c485d3e09b71/hands-on-sessions/day-1/2-quantum-espresso/ecut.png" width="250"> 
</p>

2. K-points:

Similarly, one should converge the energy with respect to the number of k-points sampled in a periodic system. This may not be applicable to liquid systems with large system sizes. But, for an extended solid it is critical.

Move to the directory `kpoints`. Therein you will find a shell script, `run_kp.sh`. This script will write copies of `../si.in` here with modified values of in the `K_POINTS` card and run the calculations. Run this script doing `./run_kp.sh`.

Let's first look at what our input files look like with 
```
grep -A 1 K_POINTS si???.in
```
We have computed the energy using a range of k-point meshes from 1x1x1 to 6x6x6. For partially periodic systems (e.g. solid interfaces) one may use higher k-point samplings in the periodic dimensions. Now, look at the computed energies with

```
grep ! si???.log
```

Notice that the energy decreases a lot initially with larger k-point samplings and then seems to converge beyond 3x3x3. As with `ecutwfc`, we would want to use a k-point sampling within the converged region. If you can, try modifying the parsing and plotting instructions from the `ecutwfc` section to plot the energy vs. k-point grid size.

![image](https://user-images.githubusercontent.com/59068990/176946171-a06cdcdb-c34d-4718-a096-965bf16a94d3.png)

Once again, the more accurage/stable calculations will take a bit longer. Look at the computation times with:

```
grep "PWSCF        :" si???.log
```

### Geometry relaxation

Let's see what happens when we perturb the structure of our Si unit cell. Go to the `geom` directory and run the shell script `run_geom.sh`. This will write a new `si.in` file with the position of the 2nd Si atom moved out of equilibrium. Grep out the total energy from `si.log` and compare it to that from `../si.log`. It should be much higher.

There should also now be non-zero forces on our atoms. Look directly in the output or do

```
grep -B 5 "Total force" si.log
```

and you will see the forces on each atom and the total force.

Now let's relax the structure back to equilibrium. First open up `si-relax.in`. You will notice a few differences between this input file and the SCF input file. First, in the `&control` namelist,

```
calculation  = 'relax',
```

5.431020511
indicates that this is a relax calculation, not simply an SCF. Also,

```
forc_conv_thr = 1.0D-4
```
is added to the `&control` namelist. This is the force convergence threshold for the calculation. Finally, a relax calculation requires the inclusion of a `&ions` namelist. 

```
 &ions
    ion_dynamics = 'bfgs'
 /
```
Various other parameters in this namelist are beyond the scope of this tutorial. BFGS is the default relaxation algorithm. Otherwise note the non-equilibrium position of the Si atoms as we had in the SCF calculation.

To run the relax calculation, do:

```
mpirun -np 4 ~/QE/q-e-qe-6.4.1/bin/pw.x < si-relax.in > si-relax.log
```

In a relax calculation, an electronic SCF is converged for every ionic step towards lowering the forces below the threshold. Let's look at the convergence of the electronic energies and reduction of theforces over the course of the relax calculation. 

Energies:

```
grep ! si-relax.log
```

Forces:

```
grep "Total force" si-relax.log
```

Feel free to plot the progressions of the total energy and force as done below (left and right, respectively):

![image](https://user-images.githubusercontent.com/59068990/177489923-ac148e5d-7864-484f-9cb2-c63f36a794eb.png)

Now, look at the final coordinates for the two Si atoms. Open the `si-relax.log` file and find the last instance of `ATOMIC_POSITIONS`. You will notice that both Si moved according to the forces on them, so one Si atom is no longer at (0,0,0). Nonetheless, the forces are relaxed below the threshold and we can consider this the equilibrium structure for our computational protocol. 

You can use `Xcrysden` to visualize the relaxation as an animation. On a machine with `xcrysden` loaded and the log file:

```
xcrysden --pwo si-relax.log
```

Select to display all coordinates as an animation. You can also measure the Si-Si distance at the beginning of the calculation vs. at the end by using the `Distance` tool on the bottom of the `xcrysden` GUI, selecting the two atoms, then clicking `Done`.

### Additional considerations and links

- [LibXC](https://gitlab.com/libxc/libxc/-/releases) is the library QE uses for meta-GGA, hybrid, etc. functionals. Much of the pioneering DPMD work on water was trained with the SCAN functional, which requires LibXC to run in QE.
- Materials cloud for maining and convergence test resutsl.