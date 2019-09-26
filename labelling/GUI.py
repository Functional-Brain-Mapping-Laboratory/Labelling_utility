
import sys
import os

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QGridLayout, QLabel,
                             QSpinBox, QComboBox, QDialogButtonBox, QCheckBox,
                             QApplication, QFileDialog, QLineEdit, QListWidget,
                             QPushButton, QErrorMessage)
from PyQt5.QtCore import Qt, pyqtSlot

from pipeline import run_classifier_pipeline


def get_default_subject_dir():
    import os
    env_var = os.environ
    try:
        subject_dir = env_var['SUBJECTS_DIR']
    except Exception as e:
        print(e)
        subject_dir = os.getcwd()
    return (subject_dir)


class LabelsDialog(QDialog):
    def __init__(self, parent=None, subject_directory=None, QApplication=None):
        super().__init__(parent)
        self.setWindowTitle('Label Toolbox')
        vbox = QVBoxLayout(self)
        grid = QGridLayout()
        # Subject dir
        grid.addWidget(QLabel('Subject directory:'), 0, 0)
        self.QLineEdit_subject_dir = QLineEdit()
        self.subject_directory = subject_directory
        self.QLineEdit_subject_dir.setText(subject_directory)
        grid.addWidget(self.QLineEdit_subject_dir, 0, 1)
        self.QPushButton_open_subject_dir = QPushButton('Open')
        self.QPushButton_open_subject_dir.clicked.connect(self.open_subject_directory)
        grid.addWidget(self.QPushButton_open_subject_dir, 0, 3)
        # subject
        grid.addWidget(QLabel('Subject:'), 1, 0)
        self.QComboBox_subject = QListWidget()
        self.set_subjects()
        self.QComboBox_subject.setSelectionMode(QListWidget.ExtendedSelection)
        grid.addWidget(self.QComboBox_subject, 1, 1, 1, 3)
        # atlas
        grid.addWidget(QLabel('Atlas:'), 2, 0)
        self.QListWidget_atlas = QListWidget()
        self.get_available_atlas()
        self.QListWidget_atlas.insertItems(0, self.available_atlas)
        self.QListWidget_atlas.setSelectionMode(QListWidget.ExtendedSelection)
        grid.addWidget(self.QListWidget_atlas, 2, 1, 1, 3)
        # outputdir
        grid.addWidget(QLabel('Output directory:'), 3, 0)
        self.QLineEdit_output_dir = QLineEdit()
        self.output_directory = os.getcwd()
        self.QLineEdit_output_dir.setText(self.output_directory)
        grid.addWidget(self.QLineEdit_output_dir, 3, 1)
        self.QPushButton_open_output_dir = QPushButton('Open')
        self.QPushButton_open_output_dir.clicked.connect(self.open_output_directory)
        grid.addWidget(self.QPushButton_open_output_dir, 3, 3)
        # performance
        grid.addWidget(QLabel('n_procs:'), 4, 0)
        self.QLineEdit_output_dir = QLineEdit()
        self.max_cpus = os.cpu_count()
        self.QSpinBox_n_cpus = QSpinBox()
        self.QSpinBox_n_cpus.setMinimum(1)
        self.QSpinBox_n_cpus.setMaximum(self.max_cpus)
        self.QSpinBox_n_cpus.setValue(self.max_cpus)
        grid.addWidget(self.QSpinBox_n_cpus, 4, 1)
        # run
        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok |
                                          QDialogButtonBox.Cancel)
        grid.addWidget(self.buttonbox, 5, 1, 1, 4)
        self.buttonbox.accepted.connect(self.run_pipeline)
        self.buttonbox.rejected.connect(self.reject)
        vbox.addLayout(grid)

    def get_subjects(self):
        "Get all subject in subject_directory"
        import os
        self.subjects = [name for name in os.listdir(self.subject_directory) if os.path.isdir(os.path.join(self.subject_directory, name))]
        return ()

    def get_available_atlas(self):
        script_path = os.path.dirname(os.path.abspath(__file__))
        luts_dir = os.path.join(script_path, 'LUTs')
        atlas = []
        for file in os.listdir(luts_dir):
            print(file)
            if file.endswith('_LUT.txt'):
                base_atlas_name = file[:-8]
                lh_gcs = 'lh.' + base_atlas_name + '.gcs'
                rh_gcs = 'rh.' + base_atlas_name + '.gcs'
                lh_gcs_path = os.path.join(script_path,  'classifiers', lh_gcs)
                rh_gcs_path = os.path.join(script_path,  'classifiers', rh_gcs)
                if os.path.exists(lh_gcs_path) and os.path.exists(rh_gcs_path):
                    atlas.append(base_atlas_name)
        self.available_atlas = atlas
        return()

    def open_subject_directory(self):
        self.subject_directory = QFileDialog.getExistingDirectory(self, 'OpenDir')
        self.QLineEdit_subject_dir.setText(self.subject_directory)
        self.set_subjects()
        return()

    def open_output_directory(self):
        self.output_directory = QFileDialog.getExistingDirectory(self, 'OpenDir')
        self.QLineEdit_output_dir.setText(self.output_directory)
        return()

    def set_subjects(self):
        self.get_subjects()
        self.QComboBox_subject.clear()
        self.QComboBox_subject.insertItems(0, self.subjects)

    def run_pipeline(self):
        subjects = [item.data(0) for item in self.QComboBox_subject.selectedItems()]
        atlas = [item.data(0) for item in self.QListWidget_atlas.selectedItems()]
        output_path = self.output_directory
        subject_directory = self.subject_directory
        n_cpus = self.QSpinBox_n_cpus.value()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            run_classifier_pipeline(subjects, atlas,
                                    subject_directory, output_path,
                                    n_procs=n_cpus)
            QApplication.restoreOverrideCursor()
            self.QMessageBox_finnish = QMessageBox()
            self.QMessageBox_finnish.showMessage('Finnished')
        except Exception as e:
            QApplication.restoreOverrideCursor()
            self.QErrorMessage = QErrorMessage()
            self.QErrorMessage.showMessage(str(e))



if __name__ == '__main__':
    subject_directory = get_default_subject_dir()
    app = QApplication(sys.argv)
    LabelsDialog = LabelsDialog(subject_directory=subject_directory,
                                QApplication=app)
    LabelsDialog.show()
    sys.exit(app.exec_())
