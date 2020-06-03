import sys
import os
import subprocess
from pathlib import Path, PurePosixPath

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QGridLayout, QLabel,
                             QSpinBox, QComboBox, QDialogButtonBox, QCheckBox,
                             QApplication, QFileDialog, QLineEdit, QListWidget,
                             QPushButton, QErrorMessage, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSlot

from PyQt5.QtWidgets import QApplication


class LabelsDialog(QDialog):
    def __init__(self, exclude_file=None,
                 parent=None, subject_directory=None, QApplication=None):
        super().__init__(parent)
        self.exclude = []
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
        self.QPushButton_open_subject_dir.clicked.connect(
                                                self.open_subject_directory)
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
        # edit parc
        grid.addWidget(QLabel('Exclude labels:'), 3, 0)
        self.exclude_file = exclude_file
        self.QLineEdit_exclude = QLineEdit()
        if exclude_file is not None:
            self.load_exclude(exclude_file)
        self.QLineEdit_exclude.setText(self.exclude_file)
        grid.addWidget(self.QLineEdit_exclude, 3, 1)
        self.QPushButton_exclude = QPushButton('Open')
        self.QPushButton_exclude.clicked.connect(self.open_exclude)
        grid.addWidget(self.QPushButton_exclude, 3, 3)
        # outputdir
        grid.addWidget(QLabel('Output directory:'), 4, 0)
        self.QLineEdit_output_dir = QLineEdit()
        self.output_directory = os.getcwd()
        self.QLineEdit_output_dir.setText(self.output_directory)
        grid.addWidget(self.QLineEdit_output_dir, 4, 1)
        self.QPushButton_open_output_dir = QPushButton('Open')
        self.QPushButton_open_output_dir.clicked.connect(
                                                   self.open_output_directory)
        grid.addWidget(self.QPushButton_open_output_dir, 4, 3)
        # performance
        grid.addWidget(QLabel('n_procs:'), 5, 0)
        self.max_cpus = os.cpu_count()
        self.QSpinBox_n_cpus = QSpinBox()
        self.QSpinBox_n_cpus.setMinimum(1)
        self.QSpinBox_n_cpus.setMaximum(self.max_cpus)
        self.QSpinBox_n_cpus.setValue(self.max_cpus)
        grid.addWidget(self.QSpinBox_n_cpus, 5, 1)
        # run
        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok |
                                          QDialogButtonBox.Cancel)
        grid.addWidget(self.buttonbox, 6, 1, 1, 4)
        self.buttonbox.accepted.connect(self.run_pipeline)
        self.buttonbox.rejected.connect(self.reject)
        vbox.addLayout(grid)

    def get_subjects(self):
        "Get all subject in subject_directory"
        import os
        self.subjects = [name for name in os.listdir(self.subject_directory)
                         if os.path.isdir(os.path.join(self.subject_directory,
                                                       name))]
        return ()

    def get_available_atlas(self):
        self.available_atlas = ['desikan_killiany',
                                'DKTatlas40',
                                'Schaefer2018_100Parcels_7Networks',
                                'Schaefer2018_100Parcels_17Networks',
                                'Schaefer2018_200Parcels_7Networks',
                                'Schaefer2018_200Parcels_17Networks',
                                'Schaefer2018_300Parcels_7Networks',
                                'Schaefer2018_300Parcels_17Networks',
                                'Schaefer2018_400Parcels_7Networks',
                                'Schaefer2018_400Parcels_17Networks',
                                'Schaefer2018_500Parcels_7Networks',
                                'Schaefer2018_500Parcels_17Networks',
                                'Schaefer2018_600Parcels_7Networks',
                                'Schaefer2018_600Parcels_17Networks',
                                'Schaefer2018_700Parcels_7Networks',
                                'Schaefer2018_700Parcels_17Networks',
                                'Schaefer2018_800Parcels_7Networks',
                                'Schaefer2018_800Parcels_17Networks',
                                'Schaefer2018_900Parcels_7Networks',
                                'Schaefer2018_900Parcels_17Networks',
                                'Schaefer2018_1000Parcels_7Networks',
                                'Schaefer2018_1000Parcels_17Networks',
                                'Yeo2011_7Networks',
                                'Yeo2011_17Networks']
        return()

    def open_subject_directory(self):
        self.subject_directory = QFileDialog.getExistingDirectory(self,
                                                                  'OpenDir')
        self.QLineEdit_subject_dir.setText(self.subject_directory)
        self.set_subjects()
        return()

    def open_output_directory(self):
        self.output_directory = QFileDialog.getExistingDirectory(self,
                                                                 'OpenDir')
        print(self.output_directory)
        self.QLineEdit_output_dir.setText(self.output_directory)
        return()

    def open_exclude(self):
        filter = "txt(*.txt)"
        fname, _ = QFileDialog.getOpenFileName(self,
                                               'Open exclude region file',
                                               filter=filter)
        if fname:
            self.load_exclude(fname)
        return()

    def load_exclude(self, fname):
        self.exclude_file = fname
        self.QLineEdit_exclude.setText(self.exclude_file)
        with open(self.exclude_file) as f:
            content = f.readlines()
        content = [c.strip() for c in content]
        self.exclude = content

    def set_subjects(self):
        self.get_subjects()
        self.QComboBox_subject.clear()
        self.QComboBox_subject.insertItems(0, self.subjects)

    def run_pipeline(self):
        subjects = ['-s ' + item.data(0) for item in
                    self.QComboBox_subject.selectedItems()]
        atlas = ['-a ' + item.data(0) for item in
                 self.QListWidget_atlas.selectedItems()]
        exclude = ['-e None']
        exclude.extend(['-e ' + e for e in self.exclude])
        output_path = self.output_directory
        output_path = output_path.replace('\\', '/')
        subjects_dir = self.subject_directory
        subjects_dir = subjects_dir.replace('\\', '/')
        n_cpus = self.QSpinBox_n_cpus.value()
        command = ['docker run -v',  output_path + ':' + '/mnt/output',
                   '-v ' + subjects_dir + ':' + '/mnt/subjects_dir',
                   'vferat/labelling:dev_lut', 'python', 'app/app.py']
        command.extend(subjects)
        command.extend(atlas)
        command.extend(exclude)
        command.extend(['--cpus', str(n_cpus)])
        command = ' '.join(command)
        print(command)
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            subprocess.run(command, check=True, shell=True)
            QApplication.restoreOverrideCursor()
            self.QMessageBox_finnish = QMessageBox()
            self.QMessageBox_finnish.setWindowTitle("Finished")
            self.QMessageBox_finnish.setText("Pipeline ran without errors.")
            self.QMessageBox_finnish.exec_()
        except Exception as e:
            QApplication.restoreOverrideCursor()
            self.QErrorMessage = QErrorMessage()
            self.QErrorMessage.showMessage(str(e))
