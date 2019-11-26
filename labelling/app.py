import argparse
from cartool_labelling_workflow import generate_cartool_labelling_workflow
from nifti_labelling_workflow import generate_nifti_labelling_workflow

def run_worflow(subjects, atlas, cartool=True, n_cpus=1):
    name = 'FBMlab_wf'
    classifier_data_dir = '/app'
    output_path = '/mnt/output'
    subjects_dir = '/mnt/subjects_dir'
    working_dir = '/working_dir'
    # Run workflow
    print(type)
    if cartool is True:
        workflow = generate_cartool_labelling_workflow(
                                           name,
                                           subjects,
                                           atlas,
                                           subjects_dir,
                                           classifier_data_dir,
                                           output_path=output_path)
    elif cartool is False:
        workflow = generate_nifti_labelling_workflow(
                                           name,
                                           subjects,
                                           atlas,
                                           subjects_dir,
                                           classifier_data_dir,
                                           output_path=output_path)
    workflow.config['execution']['parameterize_dirs'] = False
    workflow.base_dir = working_dir
    plugin_args = {'n_procs': n_cpus,
                   'memory_gb': 60}
    workflow.run(plugin='MultiProc', plugin_args=plugin_args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--subjects', dest='subjects', action='append',
                        help='<Required> Subjects to process',
                        required=True)
    parser.add_argument('-a', '--atlas', dest='atlas', action='append',
                        help='<Required> atlas to use',
                        required=True)
    parser.add_argument('--cpus', dest='n_cpus',
                        help='Number of cpus to use',
                        required=False, type=int, default=1)
    parser.add_argument('--cartool', dest='cartool',
                        help='Number of cpus to use',
                        action='store_true',
                        required=False, default=False)
    args = parser.parse_args()
    print(args)
    run_worflow(args.subjects, args.atlas,
                cartool=args.cartool, n_cpus=args.n_cpus)
