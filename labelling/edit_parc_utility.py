import sys
import os

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QGridLayout, QLabel,
                             QSpinBox, QComboBox, QDialogButtonBox, QCheckBox,
                             QApplication, QFileDialog, QLineEdit, QListWidget,
                             QPushButton, QErrorMessage, QMessageBox, QSlider)
from PyQt5.QtCore import Qt, pyqtSlot

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg \
    import FigureCanvasQTAgg as FigureCanvas

import nibabel as nib
import numpy as np


class LabelsDialog(QDialog):
    def __init__(self, parent=None, QApplication=None):
        super().__init__(parent)
        self.excluded_indices = list()
        self.setWindowTitle('Edit Parcellation Toolbox')
        vbox = QVBoxLayout(self)
        grid = QGridLayout()
        # parcellation
        grid.addWidget(QLabel('Parcellation:'), 0, 0)
        self.QLineEdit_parcellation = QLineEdit()
        grid.addWidget(self.QLineEdit_parcellation, 0, 1)
        self.QPushButton_open_parcellation = QPushButton('Open')
        self.QPushButton_open_parcellation.clicked.connect(self.open_parcellation)
        grid.addWidget(self.QPushButton_open_parcellation, 0, 3)
        # LUT
        grid.addWidget(QLabel('LUT:'), 1, 0)
        self.QLineEdit_lut = QLineEdit()
        grid.addWidget(self.QLineEdit_lut, 1, 1)
        self.QPushButton_open_lut = QPushButton('Open')
        self.QPushButton_open_lut.clicked.connect(self.open_lut)
        grid.addWidget(self.QPushButton_open_lut, 1, 3)
        # Slider
        self.QSlider_slice = QSlider(Qt.Horizontal)
        self.QSlider_slice.setMinimum(0)
        self.QSlider_slice.setMaximum(255)
        self.QSlider_slice.valueChanged.connect(self.draw_slices)
        grid.addWidget(self.QSlider_slice, 2, 1, 1, 3)
        # Label List
        self.QListWidget_labels = QListWidget()
        self.QListWidget_labels.setSelectionMode(QListWidget.ExtendedSelection)
        self.QListWidget_labels.itemSelectionChanged.connect(self.exclude_labels)
        grid.addWidget(self.QListWidget_labels, 3, 1, 1, 1)
        # Canvas
        self.fig, self.axis = plt.subplots(1)
        self.canvas = FigureCanvas(self.fig)
        grid.addWidget(self.canvas, 3, 2, 1, 2)
        vbox.addLayout(grid)

    def open_parcellation(self):
        self.parcellation, _ = QFileDialog.getOpenFileName(self, 'OpenDir')
        self.QLineEdit_parcellation.setText(self.parcellation)
        self.mri = nib.load(self.parcellation)
        self.draw_slices()
        self.set_available_labels()
        return()

    def open_lut(self):
        self.lut, _ = QFileDialog.getOpenFileName(self, 'OpenDir')
        self.QLineEdit_lut.setText(self.lut)
        dtype = [('id', '<i8'), ('name', 'U47'),
                 ('R', '<i8'), ('G', '<i8'), ('B', '<i8'), ('A', '<i8')]
        self.data_lut = np.genfromtxt(self.lut, dtype=dtype)
        print(len(self.data_lut['R']))
        self.palette = np.zeros((self.data_lut['id'][-1] + 1, 3))
        for k, id in enumerate(self.data_lut['id']):
            self.palette[id] = [self.data_lut['R'][k],
                                self.data_lut['G'][k],
                                self.data_lut['B'][k]]
        return()

    def draw_slices(self):
        self.axis.clear()
        data = self.mri.get_data()
        for i in self.excluded_indices:
            data = np.where(data != i, data, 0)
        slice_0 = data[self.QSlider_slice.value(), :, :].astype("int")
        slice_0 = self.palette[slice_0].astype(np.uint8)
        self.axis.imshow(slice_0)
        self.canvas.draw()

    def set_available_labels(self):
        self.get_available_labels()
        self.QListWidget_labels.clear()
        self.QListWidget_labels.insertItems(0, self.available_labels)

    def get_available_labels(self):
        uniques_idx = np.unique(self.mri.get_data())
        uniques_names = [str(self.data_lut[np.where(self.data_lut['id'] == i)[0]]['name'][0]) for i in uniques_idx]
        self.available_labels = uniques_names

    def exclude_labels(self):
        self.excluded_names = [item.data(0) for item in self.QListWidget_labels.selectedItems()]
        self.excluded_indices = [self.data_lut['id'][p] for p in range (0,len(self.data_lut['name'])) if self.data_lut['name'][p] in self.excluded_names]
        self.draw_slices()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    LabelsDialog = LabelsDialog(QApplication=app)
    LabelsDialog.show()
    sys.exit(app.exec_())
