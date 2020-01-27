
import sys
import os

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QGridLayout, QLabel,
                             QSpinBox, QComboBox, QDialogButtonBox, QCheckBox,
                             QApplication, QFileDialog, QLineEdit, QListWidget,
                             QPushButton, QErrorMessage, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSlot

from .cartool_labelling_workflow import generate_cartool_labelling_workflow
from .nifti_labelling_workflow import generate_nifti_labelling_workflow


class LabelsDialog(QDialog):
    def __init__(self, classifier_data_dir,
                 parent=None, subject_directory=None, QApplication=None):
        super().__init__(parent)
        self.classifier_data_dir = classifier_data_dir
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
        self.QLineEdit_exclude = QLineEdit()
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
        luts_dir = os.path.join(self.classifier_data_dir, 'LUTs')
        atlas = []
        for file in os.listdir(luts_dir):
            if file.endswith('_LUT.txt'):
                base_atlas_name = file[:-8]
                print(base_atlas_name)
                lh_gcs = 'lh.' + base_atlas_name + '.gcs'
                rh_gcs = 'rh.' + base_atlas_name + '.gcs'
                lh_gcs_path = os.path.join(self.classifier_data_dir,
                                           'classifiers', lh_gcs)
                rh_gcs_path = os.path.join(self.classifier_data_dir,
                                           'classifiers', rh_gcs)
                if os.path.exists(lh_gcs_path) and os.path.exists(rh_gcs_path):
                    print(base_atlas_name)
                    atlas.append(base_atlas_name)
        self.available_atlas = atlas
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
        self.QLineEdit_output_dir.setText(self.output_directory)
        return()

    def open_exclude(self):
        filter = "txt(*.txt)"
        fname, _ = QFileDialog.getOpenFileName(self,
                                               'Open exclude region file',
                                               filter=filter)
        if fname:
            self.fname_exclude = fname
            self.QLineEdit_exclude.setText(self.fname_exclude)
            with open(self.fname_exclude) as f:
                content = f.readlines()
            content = [c.strip() for c in content]
            print(content)
            self.exclude = content
        return()

    def set_subjects(self):
        self.get_subjects()
        self.QComboBox_subject.clear()
        self.QComboBox_subject.insertItems(0, self.subjects)

    def run_pipeline(self):
        # Get parameters
        name = 'FBMlab_wf'
        subjects = [item.data(0) for item in
                    self.QComboBox_subject.selectedItems()]
        atlas = [item.data(0) for item in
                 self.QListWidget_atlas.selectedItems()]
        exclude = self.exclude
        classifier_data_dir = self.classifier_data_dir
        output_path = self.output_directory
        subjects_dir = self.subject_directory
        n_cpus = self.QSpinBox_n_cpus.value()
        workflow = generate_nifti_labelling_workflow(
                                           name,
                                           subjects,
                                           atlas,
                                           subjects_dir,
                                           classifier_data_dir,
                                           exclude=exclude,
                                           output_path=output_path)
        workflow.config['execution']['parameterize_dirs'] = False
        plugin_args = {'n_procs': n_cpus}
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            workflow.run(plugin='MultiProc', plugin_args=plugin_args)
            QApplication.restoreOverrideCursor()
            self.QMessageBox_finnish = QMessageBox()
            self.QMessageBox_finnish.setWindowTitle("Finished")
            self.QMessageBox_finnish.setText("Pipeline ran without errors.")
            self.QMessageBox_finnish.exec_()
        except Exception as e:
            QApplication.restoreOverrideCursor()
            self.QErrorMessage = QErrorMessage()
            self.QErrorMessage.showMessage(str(e))
