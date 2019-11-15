import fire
from cartool_labelling_workflow import generate_cartool_labelling_workflow
from nifti_labelling_workflow import generate_nifti_labelling_workflow

def run_worflow(subjects, atlas, cartool=True, n_cpus=1):
    name = 'FBMlab_wf'
    classifier_data_dir = '/app'
    output_path = '/mnt/output'
    subjects_dir = '/mnt/subjects_dir'
    working_dir = '/working_dir'
    # Run workflow
    if cartool is True:
        workflow = generate_cartool_labelling_workflow(
                                           name,
                                           subjects,
                                           atlas,
                                           subjects_dir,
                                           classifier_data_dir,
                                           output_path=output_path)
    else:
        workflow = generate_nifti_labelling_workflow(
                                           name,
                                           subjects,
                                           atlas,
                                           subjects_dir,
                                           classifier_data_dir,
                                           output_path=output_path)
    workflow.config['execution']['parameterize_dirs'] = False
    workflow.base_dir = working_dir
    plugin_args = {'n_procs': n_cpus}
    workflow.run(plugin='MultiProc', plugin_args=plugin_args)

if __name__ == '__main__':
    fire.Fire(run_worflow)
