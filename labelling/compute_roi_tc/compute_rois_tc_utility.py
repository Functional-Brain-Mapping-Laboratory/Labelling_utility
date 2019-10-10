
import sys
import os

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QGridLayout, QLabel,
                             QSpinBox, QComboBox, QDialogButtonBox, QCheckBox,
                             QApplication, QFileDialog, QLineEdit, QListWidget,
                             QPushButton, QErrorMessage, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSlot

import numpy as np
import pycartool


def create_rois(spi, ROIs, ris):
    rois_sources_tc = []
    rois_names = []
    rois_sources_pos = []
    rois_sources_names = []
    rois_names = ROIs['names']
    for r, _ in enumerate(rois_names):
        indices = [int(x)-1 for x in ROIs['elements'][r]]
        roi_sources_tc = ris['data'].T[indices, :, :]
        roi_sources_pos = SPI['coordinates'][indices]
        roi_sources_names = np.array(SPI['names'])[indices]
        rois_sources_tc.append(roi_sources_tc)
        rois_sources_pos.append(roi_sources_pos)
        rois_sources_names.append(roi_sources_names)
    rois_pos = np.array([np.mean(pos, axis=0) for pos in rois_sources_pos])
    rois_info = {'rois_names': rois_names,
                 'rois_pos': rois_pos,
                 'rois_sources_tc': rois_sources_tc,
                 'rois_sources_names': rois_sources_names,
                 'rois_sources_pos': rois_sources_pos,
                 'sfreq': ris['sfreq']}
    return(rois_info)


def compute_rois_tc(rois_info):
    rois_tc = []
    sources_weights = []
    for r, _ in enumerate(rois_info['rois_names']):
        rois_sources_tc = rois_info['rois_sources_tc'][r]
        rois_sources_tc_flat = rois_sources_tc.reshape(-1, rois_sources_tc.shape[-1])
        U, s, V = np.linalg.svd(rois_sources_tc_flat, full_matrices=False)
        # determine sign-flip
        # sign = np.sign(np.dot(U[:, 0], flip))
        # use average power in label for scaling
        scale = np.linalg.norm(s) / np.sqrt(len(rois_sources_tc_flat))
        roi_tc = [scale * V[0]]
        sources_weights.append(np.dot(U, s).reshape(-1, 3))
        rois_tc.append(roi_tc)
    rois_info['rois_tc'] = np.array(rois_tc)
    rois_info['sources_weights'] = sources_weights
    return(rois_info)


class Labels_Tc_Dialog(QDialog):
    def __init__(self, parent=None, QApplication=None):
        super().__init__(parent)
        self.setWindowTitle('Compute Label Time Course Toolbox')
        vbox = QVBoxLayout(self)
        grid = QGridLayout()
        # Ris file
        grid.addWidget(QLabel('Result of inverse solution:'), 0, 0)
        self.QLineEdit_ris = QLineEdit()
        grid.addWidget(self.QLineEdit_ris, 0, 1)
        self.QPushButton_open_ris = QPushButton('Open')
        self.QPushButton_open_ris.clicked.connect(self.open_ris)
        grid.addWidget(self.QPushButton_open_ris, 0, 3)
        # SPI file
        grid.addWidget(QLabel('Solution Points:'), 1, 0)
        self.QLineEdit_spi = QLineEdit()
        grid.addWidget(self.QLineEdit_spi, 1, 1)
        self.QPushButton_open_spi = QPushButton('Open')
        self.QPushButton_open_spi.clicked.connect(self.open_spi)
        grid.addWidget(self.QPushButton_open_spi, 1, 3)
        # ROIs
        grid.addWidget(QLabel('Regions of interest:'), 2, 0)
        self.QLineEdit_roi = QLineEdit()
        grid.addWidget(self.QLineEdit_roi, 2, 1)
        self.QPushButton_open_roi = QPushButton('Open')
        self.QPushButton_open_roi.clicked.connect(self.open_roi)
        grid.addWidget(self.QPushButton_open_roi, 2, 3)
        # outputdir
        grid.addWidget(QLabel('Output directory:'), 3, 0)
        self.QLineEdit_output_dir = QLineEdit()
        self.output_directory = os.getcwd()
        self.QLineEdit_output_dir.setText(self.output_directory)
        grid.addWidget(self.QLineEdit_output_dir, 3, 1)
        self.QPushButton_open_output_dir = QPushButton('Open')
        self.QPushButton_open_output_dir.clicked.connect(self.open_output_directory)
        grid.addWidget(self.QPushButton_open_output_dir, 3, 3)
        # run
        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok |
                                          QDialogButtonBox.Cancel)
        grid.addWidget(self.buttonbox, 5, 1, 1, 4)
        self.buttonbox.accepted.connect(self.compute)
        self.buttonbox.rejected.connect(self.reject)
        vbox.addLayout(grid)

    def open_ris(self):
        self.ris = QFileDialog.getExistingDirectory(self, 'OpenDir')
        self.QLineEdit_subject_ris.setText(self.ris)
        return()

    def open_spi(self):
        self.spi = QFileDialog.getExistingDirectory(self, 'OpenDir')
        self.QLineEdit_subject_ris.setText(self.spi)
        return()

    def open_roi(self):
        self.roi = QFileDialog.getExistingDirectory(self, 'OpenDir')
        self.QLineEdit_subject_ris.setText(self.roi)
        return()

    def open_output_directory(self):
        self.output_directory = QFileDialog.getExistingDirectory(self, 'OpenDir')
        self.QLineEdit_output_dir.setText(self.output_directory)
        return()

    def compute(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            ROIs = pycartool.io.roi.read_roi(self.roi)
            SPI = pycartool.io.source_space.read_spi(self.spi)
            RIS = pycartool.io.inverse_solution.read_ris(self.ris)
            rois_info = create_rois(SPI, ROIs, RIS)
            all_infos = compute_rois_tc(rois_info)
            data = all_infos['rois_tc'].T
            sfreq = all_infos['sfreq']
            pycartool.io.inverse_solution.write_ris("test-rois.ris", data, sfreq)
            solution_points = {'names': all_infos['rois_names'],
                               'coordinates': all_infos['rois_pos']}
            pycartool.io.source_space.write_spi('rois.spi', solution_points)
            QApplication.restoreOverrideCursor()
            self.QMessageBox_finnish = QMessageBox()
            self.QMessageBox_finnish.setWindowTitle("Finished")
            self.QMessageBox_finnish.setText("Finished.")
            self.QMessageBox_finnish.exec_()
        except Exception as e:
            QApplication.restoreOverrideCursor()
            self.QErrorMessage = QErrorMessage()
            self.QErrorMessage.showMessage(str(e))
        return()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    Labels_Tc_Dialog = Labels_Tc_Dialog(QApplication=app)
    Labels_Tc_Dialog.show()
    sys.exit(app.exec_())
