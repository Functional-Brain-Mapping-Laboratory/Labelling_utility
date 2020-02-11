import os

import nipype.pipeline.engine as pe
from nipype.interfaces import freesurfer
import nipype.interfaces.io as nio
import nipype.interfaces.utility as util
from nipype.interfaces.utility import Function
from nipype import config, logging


def generate_fname(atlas, subject_id, subjects_dir):
    import os
    lh_fname = 'lh.' + atlas + '.annot'
    lh_fname = os.path.join(subjects_dir, subject_id, 'label', lh_fname)
    rh_fname = 'rh.' + atlas + '.annot'
    rh_fname = os.path.join(subjects_dir, subject_id, 'label', rh_fname)
    label_fname = subject_id + '_' + atlas + '.nii'
    return(lh_fname, rh_fname, label_fname)


def edit_parc(mri, exclude, lut):
    import os
    import nibabel as nib
    import numpy as np
    # Create output filename
    fname_edit = os.path.splitext(mri)[0] + "_edit.nii"
    # open lut
    dtype = [('id', '<i8'), ('name', 'U47'),
             ('R', '<i8'), ('G', '<i8'), ('B', '<i8'), ('A', '<i8')]
    data_lut = np.genfromtxt(lut, dtype=dtype)
    # open mri
    mri_img = nib.load(mri)
    mri_data = mri_img.get_data()
    # Get exclude indices
    exclude_indices = [data_lut['id'][p] for p in range(0, len(data_lut['id'])) if data_lut['name'][p] in exclude]
    # Set exclude rosi to 0 (unknown)
    for i in exclude_indices:
        mri_data = np.where(mri_data != i, mri_data, 0)
    img = nib.Nifti1Image(mri_data.astype('uint16'), mri_img.affine)
    img.to_filename(fname_edit)
    return(fname_edit)


def generate_nifti_labelling_workflow(name, subjects, atlas,
                                      subjects_dir,
                                      classifier_data_dir,
                                      exclude=[],
                                      output_path=None):
    # Constant
    workflow = pe.Workflow(name=name)
    # Generate Classifier tuples
    classifiers = []
    for at in atlas:
        lh_gcs = 'lh.' + at + '.gcs'
        rh_gcs = 'rh.' + at + '.gcs'
        lut = at + '_LUT.txt'
        annot_command = '--annot ' + at
        lh_gcs_path = os.path.join(classifier_data_dir,  'classifiers', lh_gcs)
        rh_gcs_path = os.path.join(classifier_data_dir,  'classifiers', rh_gcs)
        lut_path = os.path.join(classifier_data_dir,  'LUTs', lut)
        classifier = [at, lh_gcs_path, rh_gcs_path, lut_path, annot_command]
        classifiers.append(classifier)

    classifiersource = pe.Node(util.IdentityInterface(fields=['classifier']),
                               name='classifiersource')
    classifiersource.iterables = [('classifier', classifiers)]

    select_classifier_name = pe.Node(interface=util.Select(),
                                     name='select_classifier_name')
    select_classifier_name.inputs.index = [0]

    select_lh_gcs = pe.Node(interface=util.Select(), name='select_lh_gcs')
    select_lh_gcs.inputs.index = [1]

    select_rh_gcs = pe.Node(interface=util.Select(), name='select_rh_gcs')
    select_rh_gcs.inputs.index = [2]

    select_lut = pe.Node(interface=util.Select(), name='select_lut')
    select_lut.inputs.index = [3]

    annot_command = pe.Node(interface=util.Select(), name='annot_command')
    annot_command.inputs.index = [4]

    # Iterate over subjects
    subject_list = list(subjects)
    infosource = pe.Node(util.IdentityInterface(fields=['subject_id']),
                         name='infosource')
    infosource.iterables = [('subject_id', subject_list)]

    # Generate annotation file names
    gen_fname = pe.Node(interface=Function(
                                 input_names=['atlas',
                                              'subject_id',
                                              'subjects_dir'],
                                 output_names=['lh_fname',
                                               'rh_fname',
                                               'label_fname'],
                                 function=generate_fname),
                        name='gen_fname')
    gen_fname.inputs.subjects_dir = subjects_dir

    # processing
    fs_both = pe.Node(interface=nio.FreeSurferSource(), name='fs_both')
    fs_both.inputs.subjects_dir = subjects_dir
    fs_both.inputs.hemi = 'both'

    select_ribbon = pe.Node(interface=util.Select(), name='select_ribbon')
    select_ribbon.inputs.index = [-1]

    fs_rh = pe.Node(interface=nio.FreeSurferSource(), name='fs_rh')
    fs_rh.inputs.subjects_dir = subjects_dir
    fs_rh.inputs.hemi = 'rh'

    fs_lh = pe.Node(interface=nio.FreeSurferSource(), name='fs_lh')
    fs_lh.inputs.subjects_dir = subjects_dir
    fs_lh.inputs.hemi = 'lh'

    ca_label_lh = pe.Node(interface=freesurfer.MRIsCALabel(),
                          name='ca_label_lh')
    ca_label_lh.inputs.subjects_dir = subjects_dir
    ca_label_lh.inputs.hemisphere = 'lh'

    ca_label_rh = pe.Node(interface=freesurfer.MRIsCALabel(),
                          name='ca_label_rh')
    ca_label_rh.inputs.subjects_dir = subjects_dir
    ca_label_rh.inputs.hemisphere = 'rh'

    aparc2aseg = pe.Node(interface=freesurfer.Aparc2Aseg(),
                         name='aparc2aseg')
    aparc2aseg.inputs.subjects_dir = subjects_dir
    aparc2aseg.inputs.label_wm = False
    aparc2aseg.inputs.rip_unknown = True

    edit = pe.Node(interface=Function(
                                 input_names=['mri', 'exclude', 'lut'],
                                 output_names=['fname_edit'],
                                 function=edit_parc),
                   name='edit')
    edit.inputs.exclude = exclude

    mri_convert_Rois = pe.Node(interface=freesurfer.MRIConvert(),
                               name='mri_convert_Rois')
    mri_convert_Rois.inputs.out_orientation = 'RAS'
    mri_convert_Rois.inputs.out_type = 'nii'

    mri_convert_edit = pe.Node(interface=freesurfer.MRIConvert(),
                               name='mri_convert_edit')
    mri_convert_edit.inputs.out_orientation = 'RAS'
    mri_convert_edit.inputs.out_type = 'nii'

    mri_greymask = pe.Node(interface=freesurfer.Binarize(),
                           name='mri_greymask')
    mri_greymask.inputs.args = '--gm'

    mri_convert_greymask = pe.Node(interface=freesurfer.MRIConvert(),
                                   name='mri_convert_greymask')
    mri_convert_greymask.inputs.out_file = 'grey_mask.nii'
    mri_convert_greymask.inputs.out_orientation = 'RAS'
    mri_convert_greymask.inputs.out_datatype = 'uchar'

    mri_greymask_edit = pe.Node(interface=freesurfer.Binarize(),
                           name='mri_greymask_edit')
    mri_greymask_edit.inputs.args = '--gm'

    mri_convert_greymask_edit = pe.Node(interface=freesurfer.MRIConvert(),
                                   name='mri_convert_greymask_edit')
    mri_convert_greymask_edit.inputs.out_file = 'grey_mask_edit.nii'
    mri_convert_greymask_edit.inputs.out_orientation = 'RAS'
    mri_convert_greymask_edit.inputs.out_datatype = 'uchar'


    mri_convert_T1 = pe.Node(interface=freesurfer.MRIConvert(),
                             name='mri_convert_T1')
    mri_convert_T1.inputs.out_file = 'T1.nii'
    mri_convert_T1.inputs.out_orientation = 'RAS'

    mri_convert_brain = pe.Node(interface=freesurfer.MRIConvert(),
                                name='mri_convert_brain')
    mri_convert_brain.inputs.out_file = 'brain.nii'
    mri_convert_brain.inputs.out_orientation = 'RAS'

    datasink = pe.Node(nio.DataSink(), name='sinker')
    datasink.inputs.base_directory = os.path.abspath(output_path)

    # Workflow
    # Iterate over classifiers
    workflow.connect(classifiersource, 'classifier',
                     select_classifier_name, 'inlist')
    workflow.connect(classifiersource, 'classifier',
                     select_lh_gcs, 'inlist')
    workflow.connect(classifiersource, 'classifier',
                     select_rh_gcs, 'inlist')
    workflow.connect(classifiersource, 'classifier',
                     annot_command, 'inlist')
    workflow.connect(classifiersource, 'classifier',
                     select_lut, 'inlist')
    # Iterate over subjects
    workflow.connect(infosource, 'subject_id',
                     fs_both, 'subject_id')
    workflow.connect(infosource, 'subject_id',
                     fs_rh, 'subject_id')
    workflow.connect(infosource, 'subject_id',
                     fs_lh, 'subject_id')
    workflow.connect(infosource, 'subject_id',
                     ca_label_lh, 'subject_id')
    workflow.connect(infosource, 'subject_id',
                     ca_label_rh, 'subject_id')
    workflow.connect(infosource, 'subject_id',
                     aparc2aseg, 'subject_id')
    # Naming files
    workflow.connect(select_classifier_name, 'out',
                     gen_fname, 'atlas')
    workflow.connect(infosource, 'subject_id',
                     gen_fname, 'subject_id')
    # Connect Existing files
    workflow.connect(fs_both, 'ribbon',
                     select_ribbon, 'inlist')
    # ca_label_rh
    workflow.connect(fs_rh, 'pial',
                     ca_label_rh, 'canonsurf')
    workflow.connect(fs_rh, 'smoothwm',
                     ca_label_rh, 'smoothwm')
    workflow.connect(fs_rh, 'sulc',
                     ca_label_rh, 'sulc')
    workflow.connect(fs_rh, 'curv',
                     ca_label_rh, 'curv')
    workflow.connect(select_rh_gcs, 'out',
                     ca_label_rh, 'classifier')
    workflow.connect(gen_fname, 'rh_fname',
                     ca_label_rh, 'out_file')
    # ca_label_lh
    workflow.connect(fs_lh, 'pial',
                     ca_label_lh, 'canonsurf')
    workflow.connect(fs_lh, 'smoothwm',
                     ca_label_lh, 'smoothwm')
    workflow.connect(fs_lh, 'sulc',
                     ca_label_lh, 'sulc')
    workflow.connect(fs_lh, 'curv',
                     ca_label_lh, 'curv')
    workflow.connect(select_lh_gcs, 'out',
                     ca_label_lh, 'classifier')
    workflow.connect(gen_fname, 'lh_fname',
                     ca_label_lh, 'out_file')
    # aparc2aseg
    workflow.connect(annot_command, 'out',
                     aparc2aseg, 'args')
    workflow.connect(select_ribbon, 'out',
                     aparc2aseg, 'ribbon')
    workflow.connect(fs_rh, 'white',
                     aparc2aseg, 'rh_white')
    workflow.connect(fs_rh, 'pial',
                     aparc2aseg, 'rh_pial')
    workflow.connect(fs_rh, 'ribbon',
                     aparc2aseg, 'rh_ribbon')
    workflow.connect(fs_lh, 'white',
                     aparc2aseg, 'lh_white')
    workflow.connect(fs_lh, 'pial',
                     aparc2aseg, 'lh_pial')
    workflow.connect(fs_lh, 'ribbon',
                     aparc2aseg, 'lh_ribbon')
    workflow.connect(ca_label_lh, 'out_file',
                     aparc2aseg, 'lh_annotation')
    workflow.connect(ca_label_rh, 'out_file',
                     aparc2aseg, 'rh_annotation')
    workflow.connect(gen_fname, 'label_fname',
                     aparc2aseg, 'out_file')
    # Edit parc
    workflow.connect(aparc2aseg, 'out_file',
                     edit, 'mri')
    workflow.connect(select_lut, 'out',
                     edit, 'lut')
    # Greymask
    workflow.connect(aparc2aseg, 'out_file',
                     mri_greymask, 'in_file')
    workflow.connect(edit, 'fname_edit',
                     mri_greymask_edit, 'in_file')
    # Convert
    workflow.connect(fs_both, 'T1',
                     mri_convert_T1, 'in_file')
    workflow.connect(fs_both, 'brain',
                     mri_convert_brain, 'in_file')
    workflow.connect(mri_greymask, 'binary_file',
                     mri_convert_greymask, 'in_file')
    workflow.connect(mri_greymask_edit, 'binary_file',
                     mri_convert_greymask_edit, 'in_file')
    workflow.connect(aparc2aseg, 'out_file',
                     mri_convert_Rois, 'in_file')
    workflow.connect(edit, 'fname_edit',
                     mri_convert_edit, 'in_file')
    # Datasink
    workflow.connect(mri_convert_brain, 'out_file',
                     datasink, '@brain')
    workflow.connect(mri_convert_greymask, 'out_file',
                     datasink, '@greymask')
    workflow.connect(mri_convert_Rois, 'out_file',
                     datasink, '@label')
    workflow.connect(mri_convert_T1, 'out_file',
                     datasink, '@T1')
    workflow.connect(mri_convert_edit, 'out_file',
                     datasink, '@edit')
    workflow.connect(mri_convert_greymask_edit, 'out_file',
                     datasink, '@greymask_edit')
    return(workflow)
