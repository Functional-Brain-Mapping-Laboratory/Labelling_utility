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


def generate_nifti_labelling_workflow(name, subjects, atlas,
                                      subjects_dir,
                                      classifier_data_dir,
                                      output_path=None):
    # Initilaze workflow
    workflow = pe.Workflow(name=name)
    # Generate Classifier inputs
    classifiers = []
    for at in atlas:
        lh_gcs = 'lh.' + at + '.gcs'
        rh_gcs = 'rh.' + at + '.gcs'
        annot_command = '--annot ' + at
        lh_gcs_path = os.path.join(classifier_data_dir, 'classifiers', lh_gcs)
        rh_gcs_path = os.path.join(classifier_data_dir, 'classifiers', rh_gcs)
        classifier = [at, lh_gcs_path, rh_gcs_path, annot_command]
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

    annot_command = pe.Node(interface=util.Select(), name='annot_command')
    annot_command.inputs.index = [3]

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

    mri_greymask = pe.Node(interface=freesurfer.Binarize(),
                           name='mri_greymask')
    mri_greymask.inputs.args = '--gm'

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
    # Greymask
    workflow.connect(aparc2aseg, 'out_file',
                     mri_greymask, 'in_file')
    # Datasink
    workflow.connect(infosource, "subject_id",
                     datasink, "container")
    workflow.connect(aparc2aseg, 'out_file',
                     datasink, '@Rois')
    workflow.connect(fs_both, 'T1',
                     datasink, '@T1')
    workflow.connect(fs_both, 'brain',
                     datasink, '@brain')
    workflow.connect(mri_greymask, 'binary_file',
                     datasink, '@grey')
    return(workflow)


if __name__ == '__main__':
    name = 'workflow_nifti'
    subjects = ['bert', 'fsaverage']
    atlas = ['DKTatlas40', 'desikan_killiany']
    current_path = os.path.dirname(os.path.realpath(__file__))
    atlas_path = os.path.join(current_path,
                              'Labelling_utility',
                              'labelling',
                              'classifiers')
    subjects_dir = os.environ['SUBJECTS_DIR']
    output_path = current_path
    workflow = generate_labelling_workflow(name,
                                           subjects,
                                           atlas,
                                           atlas_path,
                                           subjects_dir,
                                           output_path=output_path)
    workflow.config['execution']['parameterize_dirs'] = False
    workflow.base_dir = output_path
    workflow.write_graph(graph2use='exec', simple_form=True)
    plugin_args = {'n_procs': 4, 'memory_gb': 8}
    workflow.run(plugin='MultiProc', plugin_args=plugin_args)
