import os


def get_default_subject_dir():
    import os
    env_var = os.environ
    try:
        subject_dir = env_var['SUBJECTS_DIR']
    except Exception as e:
        subject_dir = os.getcwd()
    return (subject_dir)
