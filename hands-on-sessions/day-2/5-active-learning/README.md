# Deep Modeling for Molecular Simulation

Hands-on sessions- Day 2- July 12, 2023

## Active learning and constructing the training dataset for the model


## Objectives

This tutorial will demonstrate the usage of the active learning protocol used to construct a suitable training dataset to obtain a converged Deep Potential (DP) model. 
The essential principles of the active learning protocol is based on ["Zhang et.al., Phys. Rev. Mater., 3, 023804"](https://journals.aps.org/prmaterials/abstract/10.1103/PhysRevMaterials.3.023804).
Using the first DP model for Si created earlier [(hands-on session 4)](https://github.com/CSIprinceton/workshop-july-2023/tree/main/hands-on-sessions/day-2/4-first-model), this tutorial will go over the iterative refinement of this model following the active learning protocol. Due to time constraints,
this tutorial only serves as a demonstration of the active learning protocol and the final DP model obtained may not be suitable for high-level production stage simulations.


## Outline

This tutorial will cover the following:
* General overview of the active learning protocol
* Necessary files and scripts for running LAMMPS DPMD calculations
* Necessary scripts and procedures for extracting configurations for Labeling
* Necessary files for training the models using DeepMD-kit



## Prerequisites
It is assumed that the participant has attended the previous hands-on sessions leading up to the development of the first DP model for Si. This tutorial will only focus on the active learning
protocol for further refinement of the developed DP model for Si.


## Active learning: General Overview
The active learning protocol involves three steps:
* Exploration
* Labeling
* Training

### Exploration

**Exploration** involves the sampling of the configuration space in an efficient manner using the current version of the DP model. This is typically done by DPMD simulations using an ensemble of trained
DP models at every iteration of the active learning process. During the course of the exploration step, an indicator is used to monitor the configurations explored on-the-fly and select those with low 
prediction accuracy. These selected configurations are sent to the **Labeling** step. In the tutorial here, we will be using the maximum deviation of atomic forces between four DP models as a reliable 
indicator to identify configurations with low prediction accuracy.

The portion of the LAMMPS input script ```input.lmp``` that specifies this is:


```pair_style      deepmd ../frozen_model_1_compressed.pb ../frozen_model_2_compressed.pb ../frozen_model_3_compressed.pb ../frozen_model_4_compressed.pb out_file md.out out_freq ${out_freq}```


The above line instructs LAMMPS to perform a DPMD simulation with ```frozen_model_1_compressed.pb``` as the DP model for representing the potential energy surface (PES), with the deviations in the virial 
and atomic forces computed with respect to all the four models. By default only the maximal, minimal and average model deviations are output to the ```md.out``` file.

A typical ```md.out``` file looks like this:


```
#       step         max_devi_v         min_devi_v         avg_devi_v         max_devi_f         min_devi_f         avg_devi_f
           0       8.427915e-03       5.381944e-04       4.014585e-03       6.426034e-02       1.066602e-02       2.992327e-02
          10       7.420156e-03       1.623721e-03       3.983475e-03       6.004617e-02       1.504808e-02       3.167037e-02
          20       1.447545e-02       2.874226e-03       8.273970e-03       9.241611e-02       2.048283e-02       3.700585e-02
          30       1.825509e-02       2.341124e-03       9.962326e-03       9.237947e-02       1.080203e-02       4.304728e-02
```

where the first column indicates the DPMD step, the next three columns provide the maximal, minimal and average model deviations of the virial and the last three columns the maximal, minimal and average 
model deviations in atomic forces.

It is standard practice to consider configurations with low prediction accuracy within a specified range of maximum deviation in atomic forces; for e.g. {0.1 to 0.8 eV/A}. This is done so that configurations
that have extremely poor representability are not included in the training dataset. In this tutorial, we instead consider all configurations explored during the DPMD simulation for **Labeling**.

A final important point to note in the **Exploration** step is the range of thermodynamic variables such as temperature and pressure which need to be considered. This is usually constrained by the
problem at hand for which the DP model is being developed. For example, if we are interested in the properties of liquid water at room temperature, then a typical range of temperatures from 273 K to 320 K and 
1 bar pressure would suffice. However, considering configurations spanning a much larger range of thermodynamic variables generally makes the DP model more robust. 

In the Si system in this tutorial, we consider liquid Si at 1700 K, at pressures corresponding to +/- 10,000 bar and 1 bar.


### Labeling
**Labeling** involves generating __ab-initio__ energies and forces for the selected configurations from the **Exploration** step. This can be done by high-level quantum chemistry, or density functional theory
(DFT) methods. The labeled configurations are then added to the existing training dataset, which is then used in the new iteration for **Training**.

### Training
**Training** fits the ever-increasing dataset to represent the PES efficiently and accurately. A collection of DP models that differ only in their initialization are used in the **Training** step. 
These models are then frozen and used to perform DPMD simulations in the next iteration where the model deviations are obtained in the **Exploration** step.


The active learning protocol is implemented over several iterations until a suitable DP model that accurately represents the PES is obtained. A common rule-of-thumb that is used to gauge the suitability 
of the DP model involves the model deviation in atomic forces falling below a pre-defined threshold over the course of a sufficiently long (e.g. 100 ps) DPMD simulation. Further discussion on performing appropriate error analysis of a trained DP model will be covered in the [next hands-on session](https://github.com/CSIprinceton/workshop-july-2023/tree/main/hands-on-sessions/day-2/6-error-analysis)


## Active learning in practice
Create directories for the different iterations of the active learning protocol by using: ``` mkdir Iteration? ``` where ``` ? ``` can be replaced with the iteration number. The first iteration
will be the data that was used for the creation of the [first model](https://github.com/CSIprinceton/workshop-july-2023/tree/main/hands-on-sessions/day-2/4-first-model). We will go over 4 rounds of
iterations in this tutorial, corresponding to ``` Iteration2 ``` to ``` Iteration5 ```.

### Exploration step
In each iteration, we will be running a LAMMPS DPMD simulation with the current version of the trained DP model to explore the configuration space of liquid Si. Within the ``` Iteration? ``` directory
create a directory called ``` run-simulations ```. Within the ``` run-simulations ``` directory create three directories corresponding to the temperature and pressure of liquid Si to be explored in 
that DPMD simulation. Name these directories with the following format: ``` liquid-64-?Temp-?Pressure ```. Replace ``` ?Temp ``` with ``` 1700K ``` (which will be the only temperature considered) and
``` ?Pressure ``` with ``` 10kbar, neg10kbar and 1bar ``` respectively.

In each of these directories, you will be performing a LAMMPS DPMD calculation following the same procedure as detailed in [hands-on session 4](https://github.com/CSIprinceton/workshop-july-2023/tree/main/hands-on-sessions/day-2/4-first-model). Make sure to change the target temperature and pressure in the sample ``` input.lmp ``` script provided.

Once the LAMMPS DPMD simulation has finished, take a look at the ``` md.out ``` file to get a gauge of the maximal deviation in atomic forces (column 5). Typically, this should reduce as you go 
along the active learning process through different iterations indicating the convergence of the DP model.

Next, we will extract the configurations for Labeling. In this tutorial, we are considering all configurations obtained from the DPMD simulation for Labeling, with the __ab-initio__ energies and forces obtained at the DFT level using the Quantum Espresso software package. In order to get the required input files of the different configurations to be able to perform DFT calculations, use the 
``` get_configurations.py ``` script available at ``` $TUTORIAL_PATH/hands-on-sessions/day-2/5-active-learning/scripts/ ```. In each of the directories, run the script as ``` python get_configurations.py ```. This will create a directory called ``` extracted-confs ``` which will have the following Quantum Espresso input files ``` pw-si-?.in ``` where the ``` ? ``` corresponds to the indices of the different configurations.

### Labeling step
In the ``` extracted-confs ``` directory perform DFT calculations of the Labeled configurations using the Quantum Espresso software package [(see hands-on session 2)](https://github.com/CSIprinceton/workshop-july-2023/tree/main/hands-on-sessions/day-1/2-quantum-espresso). To run these calculations use the slurm shell script ``` job.sh ``` available at  ``` $TUTORIAL_PATH/hands-on-sessions/day-2/5-active-learning/scripts/ ```. Once the calculations are complete, you should see the Quantum Espresso output files ``` pw-si-?.out ``` generated.

### Training step
In this step, we will first extract the coordinates, energies, and atomic forces from the ``` pw-si-?.out ``` files to obtain the corresponding ``` .raw ``` files. To do this, follow the same steps as outlined in [hands-on session 4](https://github.com/CSIprinceton/workshop-july-2023/tree/main/hands-on-sessions/day-2/4-first-model) using the ``` get_raw.py ``` and ``` raw_to_set.sh ``` scripts to get the training data in the prescribed format for DeepMD kit. Once you have this for all of the different systems explored, you are all set to begin the training by adding this new training data to the ``` input.json ``` script. 

To do this simply add the following lines to the ``` input.json ``` script used in [hands-on session 4](https://github.com/CSIprinceton/workshop-july-2023/tree/main/hands-on-sessions/day-2/4-first-model):
```json
"training_data": {
            "systems": [
		"<SOME_FOLDER>/perturbations-si-64/0.01A-1p",
		"<SOME_FOLDER>/perturbations-si-64/0.1A-3p",
		"<SOME_FOLDER>/perturbations-si-64/0.2A-5p",
		"<SOME_FOLDER>/liquid-si-64/trajectory-lammps-1700K-1bar/extracted-confs",
                "<SOME_FOLDER>/liquid-si-64/trajectory-lammps-1700K-10000bar/extracted-confs",
		"<SOME_FOLDER>/liquid-si-64/trajectory-lammps-1700K-neg10000bar/extracted-confs",
		"<SOME_FOLDER>/Iteration2/run-simulations/liquid-64-1700K-10kbar/extracted-confs",
		"<SOME_FOLDER>/Iteration2/run-simulations/liquid-64-1700K-neg10kbar/extracted-confs",
		"<SOME_FOLDER>/Iteration2/run-simulations/liquid-64-1700K-1bar/extracted-confs"
                        ]
```

For successive iterations, make sure to add the training data corresponding to that iteration. Once you have the required edits to the ``` input.json ``` script, start the training by executing ``` dp train input.json ```. Once the training is complete, freeze and compress the model using ``` dp freeze ``` and ``` dp compress -t input.json -i frozen_model.pb -o frozen_model_compressed.pb ```. Now you have a refined DP model that is ready for a new round of Exploration of the configuration space. Repeat the Exploration, Labeling and Training steps for the next iteration.






















