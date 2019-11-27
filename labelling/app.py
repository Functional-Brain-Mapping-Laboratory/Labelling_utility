import argparse
from nifti_labelling_workflow import generate_nifti_labelling_workflow


def run_worflow(subjects, atlas, exclude=[], n_cpus=1):
    name = 'FBMlab_wf'
    classifier_data_dir = '/app'
    output_path = '/mnt/output'
    subjects_dir = '/mnt/subjects_dir'
    working_dir = '/working_dir'
    # Run workflow
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
    parser.add_argument('-e', '--exclude', dest='exclude', action='append',
                        help='Regions to exclude',
                        required=True)
    parser.add_argument('--cpus', dest='n_cpus',
                        help='Number of cpus to use',
                        required=False, type=int, default=1)

    args = parser.parse_args()
    print(args)
    run_worflow(args.subjects, args.atlas,
                exclude=args.exclude, n_cpus=args.n_cpus)
