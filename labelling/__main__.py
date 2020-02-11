import sys
import os

from PyQt5.QtWidgets import QApplication
from .gui import LabelsDialog


if __name__ == '__main__':
    subject_directory = os.getcwd()
    exclude_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'exclude.txt')
    app = QApplication(sys.argv)
    LabelsDialog = LabelsDialog(subject_directory=subject_directory,
                                exclude_file=exclude_file,
                                QApplication=app)
    LabelsDialog.show()
    sys.exit(app.exec_())
