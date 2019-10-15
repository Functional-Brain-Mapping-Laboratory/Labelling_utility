from importlib import import_module
import sys
import os

from PyQt5.QtWidgets import QApplication

from .gui import LabelsDialog
from .utils import get_default_subject_dir

if __name__ == '__main__':
    subject_directory = get_default_subject_dir()
    classifier_data_dir = os.path.dirname(os.path.abspath(__file__))
    modern = False
    try:
        import_module('qtmodern')
        modern = True
    except ModuleNotFoundError as e:
        pass
    app = QApplication(sys.argv)
    if modern is True:
        import qtmodern.styles
        qtmodern.styles.dark(app)
    app = QApplication(sys.argv)
    LabelsDialog = LabelsDialog(classifier_data_dir,
                                subject_directory=subject_directory,
                                QApplication=app)
    LabelsDialog.show()
    sys.exit(app.exec_())
