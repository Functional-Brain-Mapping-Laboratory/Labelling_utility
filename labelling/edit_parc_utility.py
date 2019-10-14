import sys
import os

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QGridLayout, QLabel,
                             QSpinBox, QComboBox, QDialogButtonBox, QCheckBox,
                             QApplication, QFileDialog, QLineEdit, QListWidget,
                             QPushButton, QErrorMessage, QMessageBox, QSlider,
                             QTabWidget, QWidget)
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
        self.parcellation = None
        self.lut = None
        self.current_data = None
        self.available_labels = None
        self.mri = None

        self.setWindowTitle('Edit Parcellation Toolbox')
        vbox = QVBoxLayout(self)
        grid = QGridLayout()
        # parcellation
        grid.addWidget(QLabel('Parcellation:'), 0, 0)
        self.QLineEdit_parcellation = QLineEdit()
        grid.addWidget(self.QLineEdit_parcellation, 0, 1, 1, 2)
        self.QPushButton_open_parcellation = QPushButton('Open')
        self.QPushButton_open_parcellation.clicked.connect(self.open_parcellation)
        grid.addWidget(self.QPushButton_open_parcellation, 0, 3)
        # LUT
        grid.addWidget(QLabel('LUT:'), 1, 0)
        self.QLineEdit_lut = QLineEdit()
        grid.addWidget(self.QLineEdit_lut, 1, 1, 1, 2)
        self.QPushButton_open_lut = QPushButton('Open')
        self.QPushButton_open_lut.clicked.connect(self.open_lut)
        grid.addWidget(self.QPushButton_open_lut, 1, 3)
        # View tabs
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        # Add tabs
        self.tabs.addTab(self.tab1, 'View 1')
        self.tabs.addTab(self.tab2, 'View 2')
        self.tabs.addTab(self.tab3, 'View 3')

        # Tab 1
        self.tab1.layout = QVBoxLayout()
        self.QSlider_tab1 = QSlider(Qt.Horizontal)
        self.QSlider_tab1.setMinimum(0)
        self.QSlider_tab1.setMaximum(255)
        self.QSlider_tab1.valueChanged.connect(self.draw_slices_tab1)
        self.tab1.layout.addWidget(self.QSlider_tab1)
        # Canvas
        self.fig1, self.axis1 = plt.subplots(1)
        self.fig1.set_facecolor('black')
        self.axis1.set_facecolor('black')
        self.canvas1 = FigureCanvas(self.fig1)
        self.tab1.layout.addWidget(self.canvas1)
        self.tab1.setLayout(self.tab1.layout)

        # Tab 1
        self.tab2.layout = QVBoxLayout()
        self.QSlider_tab2 = QSlider(Qt.Horizontal)
        self.QSlider_tab2.setMinimum(0)
        self.QSlider_tab2.setMaximum(255)
        self.QSlider_tab2.valueChanged.connect(self.draw_slices_tab2)
        self.tab2.layout.addWidget(self.QSlider_tab2)
        # Canvas
        self.fig2, self.axis2 = plt.subplots(1)
        self.fig2.set_facecolor('black')
        self.axis2.set_facecolor('black')
        self.canvas2 = FigureCanvas(self.fig2)
        self.tab2.layout.addWidget(self.canvas2)
        self.tab2.setLayout(self.tab2.layout)

        # Tab 1
        self.tab3.layout = QVBoxLayout()
        self.QSlider_tab3 = QSlider(Qt.Horizontal)
        self.QSlider_tab3.setMinimum(0)
        self.QSlider_tab3.setMaximum(255)
        self.QSlider_tab3.valueChanged.connect(self.draw_slices_tab3)
        self.tab3.layout.addWidget(self.QSlider_tab3)
        # Canvas
        self.fig3, self.axis3 = plt.subplots(1)
        self.fig3.set_facecolor('black')
        self.axis3.set_facecolor('black')
        self.canvas3 = FigureCanvas(self.fig3)
        self.tab3.layout.addWidget(self.canvas3)
        self.tab3.setLayout(self.tab3.layout)

        grid.addWidget(self.tabs, 3, 2, 1, 2)
        # Label List
        self.QListWidget_labels = QListWidget()
        self.QListWidget_labels.setSelectionMode(QListWidget.ExtendedSelection)
        self.QListWidget_labels.itemSelectionChanged.connect(self.update_data)
        grid.addWidget(self.QListWidget_labels, 3, 1, 1, 1)

        # Save
        self.QPushButton_save_parcellation = QPushButton('Save')
        self.QPushButton_save_parcellation.clicked.connect(self.save_parcellation)
        self.QPushButton_save_parcellation.setEnabled(False)
        grid.addWidget(self.QPushButton_save_parcellation, 4, 2)
        # Add grid
        vbox.addLayout(grid)

    def open_parcellation(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open Parcellation')
        if fname:
            self.parcellation = fname
            self.QLineEdit_parcellation.setText(self.parcellation)
            self.mri = nib.load(self.parcellation)
            if self.mri.get_data().ndim == 3:
                self.source_data = self.mri.get_data()
            elif self.mri.get_data().ndim == 4:
                self.source_data = self.mri.get_data()[:, :, :, 0]
            else:
                self.mri = None
                self.parcellation = None
                self.QLineEdit_parcellation.setText('')
                self.QErrorMessage = QErrorMessage()
                self.QErrorMessage.showMessage('Invalid parcellation file. '
                                               'Parcellation must be a 3D or '
                                               '4D image.')
            self.current_data = self.source_data
            self.update_data()
        self.update_labels()
        return()

    def save_parcellation(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Save Parcellation")
        if fname:
            if fname.endswith('.img'):
                header = nib.FileHolder(fname[:-3] + 'hdr')
                image = nib.FileHolder(fname)
                filemap = {'header': header,
                           'image': image}
                data = self.current_data.astype('uint8')
                img = nib.AnalyzeImage(data, self.mri.affine)
                img.to_file_map(filemap)
            else:
                data = self.current_data
                img = nib.Nifti1Image(data, self.mri.affine)
                img.to_filename(fname)
        return()

    def open_lut(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open LookUp table')
        if fname:
            self.lut = fname
            self.QLineEdit_lut.setText(self.lut)
            dtype = [('id', '<i8'), ('name', 'U47'),
                     ('R', '<i8'), ('G', '<i8'), ('B', '<i8'), ('A', '<i8')]
            self.data_lut = np.genfromtxt(self.lut, dtype=dtype)
            self.palette = np.zeros((self.data_lut['id'][-1] + 1, 3))
            for k, id in enumerate(self.data_lut['id']):
                self.palette[id] = [self.data_lut['R'][k],
                                    self.data_lut['G'][k],
                                    self.data_lut['B'][k]]
        self.update_labels()
        return()

    def update_labels(self):
        if self.lut and self.parcellation:
            uniques_idx = np.unique(self.source_data)
            uniques_names = [str(self.data_lut[np.where(self.data_lut['id'] == i)[0]]['name'][0]) for i in uniques_idx]
            self.available_labels = uniques_names
            self.QListWidget_labels.clear()
            self.QListWidget_labels.insertItems(0, self.available_labels)
            self.QPushButton_save_parcellation.setEnabled(True)
        else:
            self.QPushButton_save_parcellation.setEnabled(False)

    def draw_slices_tab1(self):
        self.axis1.clear()
        data = self.current_data
        slice = data[self.QSlider_tab1.value(), :, :].astype("int")
        slice = self.palette[slice].astype(np.uint8)
        self.axis1.imshow(slice)
        self.canvas1.draw()

    def draw_slices_tab2(self):
        self.axis2.clear()
        data = self.current_data
        slice = data[:, self.QSlider_tab2.value(), :].astype("int")
        slice = self.palette[slice].astype(np.uint8)
        self.axis2.imshow(slice)
        self.canvas2.draw()

    def draw_slices_tab3(self):
        self.axis3.clear()
        data = self.current_data
        slice = data[:, :, self.QSlider_tab3.value()].astype("int").T
        slice = self.palette[slice].astype(np.uint8)
        self.axis3.imshow(slice)
        self.canvas3.draw()

    def draw_slices(self):
        self.draw_slices_tab1()
        self.draw_slices_tab2()
        self.draw_slices_tab3()

    def update_data(self):
        if self.lut and self.parcellation:
            data = self.source_data
            self.excluded_names = [item.data(0) for item in self.QListWidget_labels.selectedItems()]
            self.excluded_indices = [self.data_lut['id'][p] for p in range (0, len(self.data_lut['name'])) if self.data_lut['name'][p] in self.excluded_names]
            for i in self.excluded_indices:
                data = np.where(data != i, data, 0)
            self.current_data = data
            self.draw_slices()




if __name__ == '__main__':
    import qtmodern.styles
    app = QApplication(sys.argv)
    qtmodern.styles.dark(app)
    LabelsDialog = LabelsDialog(QApplication=app)
    LabelsDialog.show()
    sys.exit(app.exec_())
