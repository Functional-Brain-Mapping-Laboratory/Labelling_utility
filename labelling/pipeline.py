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



def get_output_path(output_path=None):
    if output_path is None:
        output_path = os.getcwd()
    return (output_path)


def convert_for_cartool(img, LUT):
    import os
    import csv
    import nibabel
    import numpy as np
    # Loads Files
    dtype = [('id', '<i8'), ('name', 'U47'),
             ('R', '<i8'), ('G', '<i8'), ('B', '<i8'), ('A', '<i8')]
    LUT = np.genfromtxt(LUT, dtype=dtype)

    mri = nibabel.load(img)
    data = mri.get_data()
    # Assign each labels to a new indice.
    new_data = np.zeros(data.shape)
    uniques = np.unique(data)
    if len(uniques) > 255:
        raise ValueError(f'Found {len(uniques)} uniques labels '
                         f'but Cartool can only handle 255.')
    Table = []
    for i, num in enumerate(uniques):
        try:
            indix_name = str(LUT[np.where(LUT['id'] == num)[0]]['name'][0])
            new_data[data == num] = i
            Table.append([i, indix_name])
        except Exception as e:
            pass
    new_img = nibabel.Nifti1Image(new_data.astype('uint8'), mri.affine)
    table_name = os.path.splitext(img)[0] + '-table.csv'
    new_img_name = os.path.splitext(img)[0] + '-ROIs.img'
    # Save Table
    with open(table_name, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(Table)
    nibabel.save(new_img, new_img_name)
    return (new_img_name, table_name)


def run_classifier_pipeline(subjects, atlas,
                            subjects_dir,
                            output_path=None,
                            n_procs=8,
                            memory_gb=8):
    # Constant
    script_path = os.path.dirname(os.path.realpath(__file__))
    workflow = pe.Workflow(name='MRI_to_Cartool')
    # Generate Classifier tuples
    classifiers = []
    for at in atlas:
        lh_gcs = 'lh.' + at + '.gcs'
        rh_gcs = 'rh.' + at + '.gcs'
        lut = at + '_LUT.txt'
        annot_command = '--annot ' + at
        lh_gcs_path = os.path.join(script_path,  'classifiers', lh_gcs)
        rh_gcs_path = os.path.join(script_path,  'classifiers', rh_gcs)
        lut_path = os.path.join(script_path,  'LUTs', lut)
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

    # Inputs
    subject_list = list(subjects)
    infosource = pe.Node(util.IdentityInterface(fields=['subject_id']),
                         name='infosource')
    infosource.iterables = [('subject_id', subject_list)]
    # naming Files
    gen_fname = pe.Node(interface=Function(
                                 input_names=['atlas', 'subject_id', 'subjects_dir'],
                                 output_names=['lh_fname', 'rh_fname', 'label_fname'],
                                 function=generate_fname),
                        name='gen_fname')
    gen_fname.inputs.subjects_dir = subjects_dir
    # processing
    fs_both = pe.Node(interface=nio.FreeSurferSource(), name='fs_both')
    fs_both.inputs.subjects_dir = subjects_dir
    fs_both.inputs.hemi = 'both'

    select_ribbon = pe.Node(interface=util.Select(), name='select_ribbon')
    select_ribbon.inputs.index = [-1]

    select_aparc_aseg = pe.Node(interface=util.Select(),
                                name='select_aparc_aseg')
    select_aparc_aseg.inputs.index = [0]

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

    mri_greymask = pe.Node(interface=freesurfer.Binarize(),
                           name='mri_greymask')
    mri_greymask.inputs.args = '--gm'

    mri_convert_greymask = pe.Node(interface=freesurfer.MRIConvert(),
                                   name='mri_convert_greymask')
    mri_convert_greymask.inputs.out_file = 'grey_mask.img'
    mri_convert_greymask.inputs.out_orientation = 'RAS'
    mri_convert_greymask.inputs.args = '-odt uchar'

    mri_convert_T1 = pe.Node(interface=freesurfer.MRIConvert(),
                             name='mri_convert_T1')
    mri_convert_T1.inputs.out_file = 'T1.img'
    mri_convert_T1.inputs.out_orientation = 'RAS'

    mri_convert_brain = pe.Node(interface=freesurfer.MRIConvert(),
                                name='mri_convert_brain')
    mri_convert_brain.inputs.out_file = 'brain.img'
    mri_convert_brain.inputs.out_orientation = 'RAS'

    conver2cartool = pe.Node(interface=Function(
                                 input_names=['img', 'LUT'],
                                 output_names=['new_img_name', 'table_name'],
                                 function=convert_for_cartool),
                             name='conver2cartool')

    mri_convert_Rois = pe.Node(interface=freesurfer.MRIConvert(),
                               name='mri_convert_Rois')
    mri_convert_Rois.inputs.out_orientation = 'RAS'
    mri_convert_Rois.inputs.out_type = 'analyze4d'

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
                     select_lut, 'inlist')
    workflow.connect(classifiersource, 'classifier',
                     annot_command, 'inlist')
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
    workflow.connect(fs_both, 'aparc_aseg',
                     select_aparc_aseg, 'inlist')
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

    workflow.connect(select_lut, 'out',
                     conver2cartool, 'LUT')
    workflow.connect(aparc2aseg, 'out_file',
                     conver2cartool, 'img')

    workflow.connect(conver2cartool, 'new_img_name',
                     mri_convert_Rois, 'in_file')

    workflow.connect(fs_both, 'T1',
                     mri_convert_T1, 'in_file')
    workflow.connect(fs_both, 'brain',
                     mri_convert_brain, 'in_file')

    workflow.connect(select_aparc_aseg, 'out',
                     mri_greymask, 'in_file')
    workflow.connect(mri_greymask, 'binary_file',
                     mri_convert_greymask, 'in_file')

    workflow.connect(mri_convert_T1, 'out_file',
                     datasink, '@T1')
    workflow.connect(mri_convert_brain, 'out_file',
                     datasink, '@brain')
    workflow.connect(mri_convert_greymask, 'out_file',
                     datasink, '@greymask')
    workflow.connect(mri_convert_Rois, 'out_file',
                     datasink, '@label')
    workflow.connect(conver2cartool, 'table_name',
                     datasink, '@table')

    # Run
    #workflow.write_graph(graph2use='exec')
    workflow.config['execution']['parameterize_dirs'] = False
    workflow.base_dir = output_path
    plugin_args = {'n_procs': n_procs, 'memory_gb': memory_gb}
    workflow.run(plugin='MultiProc', plugin_args=plugin_args)
    return()
