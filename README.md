![License](https://img.shields.io/badge/license-BSD-green.svg)

# Labelling Toolbox
Parallel processing toolbox designed to create individual brain atlases using FREESURFER. It relies on Nipype and Python multiprocessing library to parallelize jobs.

![alt text]( img/label_toolbox.PNG "Label Toolbox")

This could outpout files either to Nifti file format or convert it to analyze (uint8) file format. Last can be use as input into [Cartool](https://sites.google.com/site/cartoolcommunity/) to perform EEG source reconstruction
and Region of interest computation.

## Installation

The toolbox is written in python and therefore could be run in most common platforms. However, as processing relies on Freesurfer, the toolbox can only run on LINUX/OSX platforms.
For WINDOWS users, you can consider using the Windows Subsystem for Linux.

### Installing FREESURFER
 This utility relies on [Freesurfer](https://surfer.nmr.mgh.harvard.edu/) to
 create individual brain atlases. To install and setup freesurfer, please refer to
 the [freesurfer wiki](https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall)

 ### Installing the labelling toolbox

 To install the toolbox, clone this repository:

 `git clone https://github.com/vferat/ParcEdit.git`

 Then go to the repository main folder and install dependencies:

 ```
 cd Labelling_utility
 pip install -r requirements.txt
 ```


## Run

To run the utility, simply go to the repository folder, open a terminal and type:

`python -m labelling.py`

## References

### Nipype

Gorgolewski, Krzysztof J. ; Esteban, Oscar ; Burns, Christopher ; Ziegler, Erik ; Pinsard, Basile ; Madison, Cindee ; Waskom, Michael ; Ellis, David Gage ; Clark, Dav ; Dayan, Michael ; Manhães-Savio, Alexandre ; Notter, Michael Philipp ; Johnson, Hans ; Dewey, Blake E ; Halchenko, Yaroslav O. ; Hamalainen, Carlo ; Keshavan, Anisha ; Clark, Daniel ; Huntenburg, Julia M. ; Hanke, Michael ; Nichols, B. Nolan ; Wassermann , Demian ; Eshaghi, Arman ; Markiewicz, Christopher ; Varoquaux, Gael ; Acland, Benjamin ; Forbes, Jessica ; Rokem, Ariel ; Kong, Xiang-Zhen ; Gramfort, Alexandre ; Kleesiek, Jens ; Schaefer, Alexander ; Sikka, Sharad ; Perez-Guevara, Martin Felipe ; Glatard, Tristan ; Iqbal, Shariq ; Liu, Siqi ; Welch, David ; Sharp, Paul ; Warner, Joshua ; Kastman, Erik ; Lampe, Leonie ; Perkins, L. Nathan ; Craddock, R. Cameron ; Küttner, René ; Bielievtsov, Dmytro ; Geisler, Daniel ; Gerhard, Stephan ; Liem, Franziskus ; Linkersdörfer, Janosch ; Margulies, Daniel S. ; Andberg, Sami Kristian ; Stadler, Jörg ; Steele, Christopher John ; Broderick, William ; Cooper, Gavin ; Floren, Andrew ; Huang, Lijie ; Gonzalez, Ivan ; McNamee, Daniel ; Papadopoulos Orfanos, Dimitri ; Pellman, John ; Triplett, William ; Ghosh, Satrajit (2016). Nipype: a flexible, lightweight and extensible neuroimaging data processing framework in Python. 0.12.0-rc1. Zenodo. [10.5281/zenodo.50186](https://zenodo.org/record/50186#.XbgIrdXjKUk)

### Freesufer

Cortical reconstruction and volumetric segmentation was performed with the Freesurfer image analysis suite, which is documented and freely available for download online (http://surfer.nmr.mgh.harvard.edu/).

### Atlases

#### DTK40
DKT40 classifier atlas: FreeSurfer atlas (.gcs) from 40 of the Mindboggle-101 participants (2012)

#### Desikan killiany
An automated labeling system for subdividing the human cerebral cortex on MRI scans into gyral based regions of interest, Desikan et al., (2006). NeuroImage, 31(3):968-80.

#### Yeo 2011
"The organization of the human cerebral cortex estimated by intrinsic functional connectivity" https://www.physiology.org/doi/full/10.1152/jn.00338.2011

#### Schaefer 2018
"Local-Global parcellation of the human cerebral cortex from intrinsic functional connectivity MRI" https://academic.oup.com/cercor/article/28/9/3095/3978804
