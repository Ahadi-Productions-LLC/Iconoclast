from __future__ import annotations

import time

from typing import Tuple

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, \
    QLabel, QFrame, QSplitter, QRadioButton, QSpinBox, \
    QStyle, QToolButton, QListWidget, QListWidgetItem, QListView
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QImage, QColor, QPen

from app.extensions.custom_gui import PropertyBox
from app.extensions.spinbox_xy import SpinBoxXY

from app.utilities import utils
from app.editor import timer
from app.editor.icon_editor.icon_view import IconView

class SpeedSpecification(QWidget):
    frame_speed_toggled = pyqtSignal(bool)

    def __init__(self, parent):
        super().__init__()
        self.window = parent.window

        self.layout = QVBoxLayout()

        self.int_speed = QRadioButton("Constant (ms)", self)
        self.int_speed.toggled.connect(self.int_speed_toggled)
        self.frame_speed = QRadioButton("Variable (#frames)", self)

        self.int_speed_box = QSpinBox(self)
        self.int_speed_box.setRange(1, 8192)
        self.int_speed_box.valueChanged.connect(self.change_spinbox)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.int_speed)
        top_layout.addWidget(self.int_speed_box)
        top_layout.addWidget(self.frame_speed)

        self.layout.addLayout(top_layout)

        self.setLayout(self.layout)

    def set_current(self, speed: int, use_frame_time: bool):
        self.int_speed_box.setValue(speed)
        if use_frame_time:
            self.int_speed.setChecked(False)
            self.frame_speed.setChecked(True)
            self.int_speed_toggled(False)
        else:
            self.int_speed.setChecked(True)
            self.frame_speed.setChecked(False)
            self.int_speed_toggled(True)

    def int_speed_toggled(self, checked):
        if checked:
            self.int_speed_box.setEnabled(True)
            self.frame_speed_toggled.emit(False)
            if self.window.current:
                self.window.current.speed = int(self.int_speed_box.value())
        else:
            self.int_speed_box.setEnabled(False)
            self.frame_speed_toggled.emit(True)

    def change_spinbox(self, val):
        if self.window.current:
            self.window.current.speed = int(val)

class FrameTime(QWidget):
    frame_time_changed = pyqtSignal(int, int)

    def __init__(self, idx: int, pix: QPixmap, frame_time: int, parent):
        super().__init__(parent)

        self.idx = idx
        self.lay = QVBoxLayout()

        self.icon = QLabel()
        self.icon.setPixmap(QPixmap(pix))

        self.frame_time = QSpinBox()
        self.frame_time.setAlignment(Qt.AlignRight)
        self.frame_time.setRange(1, 8192)
        self.frame_time.valueChanged.connect(self.on_frame_time_changed)        
        self.frame_time.setValue(frame_time)

        self.lay.addWidget(self.icon)
        self.lay.addWidget(self.frame_time)

        self.setLayout(self.lay)

    def on_frame_time_changed(self, val):
        self.frame_time_changed.emit(self.idx, val)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            pass  # Skip Enters to prevent closing out early
        else:
            super().keyPressEvent(event)

class FrameList(QListWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.current = current

        self.setUniformItemSizes(True)
        self.setFlow(QListView.Flow.LeftToRight)
        self.setIconSize(QSize(20, 20))
        self.setGridSize(QSize(20, 40))
        self.setMovement(QListView.Static)
        self.setResizeMode(QListWidget.Adjust)

    def get_icon_size(self) -> Tuple[int, int]:
        width = self.current.pixmap.width() // self.current.frame_x
        height = self.current.pixmap.height() // self.current.frame_y
        return width, height

    def sizeHint(self) -> QSize:
        s = QSize()
        if self.current:
            width, height = self.get_icon_size()
        else:
            width, height = 20, 20
        s.setHeight(max(80, height + 80)) 
        s.setWidth(max(60, width))
        return s

    def frame_time_changed(self, idx: int, val: int):
        self.current.frame_times[idx] = val

    def set_current(self, current):
        self.current = current

        self.clear()
        width, height = self.get_icon_size()
        self.setIconSize(QSize(max(60, width), max(60, height)))
        self.setGridSize(QSize(max(60, width), max(80, height + 40)))
        for num in range(self.current.num_frames):
            # Get subimage
            left = (num % self.current.frame_x) * width
            top = (num // self.current.frame_x) * height
            base_image = self.current.pixmap.copy(left, top, width, height)
            
            if len(self.current.frame_times) < self.current.num_frames:
                self.current.frame_times.extend([1]*(self.current.num_frames - len(self.current.frame_times)))
            frame_time = self.current.frame_times[num]
            frame_time_widget = FrameTime(num, base_image, frame_time, self)
            frame_time_widget.frame_time_changed.connect(self.frame_time_changed)

            item = QListWidgetItem(self)
            item.setSizeHint(frame_time_widget.minimumSizeHint())
            self.addItem(item)
            self.setItemWidget(item, frame_time_widget)
        self.updateGeometry()

class MapAnimationProperties(QWidget):
    def __init__(self, parent, current=None):
        QWidget.__init__(self, parent)
        self.window = parent
        self._data = self.window._data

        # Populate resources
        for resource in self._data:
            resource.pixmap = QPixmap(resource.full_path)

        self.current = current
        self.playing = False
        self.loop = False
        self.last_update = 0
        self.counter = 0
        self.frames_passed = 0

        left_section = QVBoxLayout()

        self.frame_view = IconView(self)
        self.frame_view.scene.setBackgroundBrush(QColor(200, 200, 200))
        left_section.addWidget(self.frame_view)

        button_section = QHBoxLayout()
        button_section.setAlignment(Qt.AlignTop)

        self.play_button = QToolButton(self)
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.play_clicked)

        self.loop_button = QToolButton(self)
        self.loop_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.loop_button.clicked.connect(self.loop_clicked)
        self.loop_button.setCheckable(True)

        button_section.addWidget(self.play_button)
        button_section.addWidget(self.loop_button)
        left_section.addLayout(button_section)

        right_section = QVBoxLayout()

        frame_section = QHBoxLayout()

        self.frame_box = PropertyBox("Frames", SpinBoxXY, self)
        self.frame_box.edit.coordsChanged.connect(self.frames_changed)
        self.frame_box.edit.setMinimum(1)
        frame_section.addWidget(self.frame_box)

        self.total_num_box = PropertyBox("Total Frames", QSpinBox, self)
        self.total_num_box.edit.valueChanged.connect(self.num_frames_changed)
        self.total_num_box.edit.setAlignment(Qt.AlignRight)
        frame_section.addWidget(self.total_num_box)

        right_section.addLayout(frame_section)

        self.speed_box = PropertyBox("Speed", SpeedSpecification, self)
        self.speed_box.edit.frame_speed_toggled.connect(self.which_speed_toggled)
        right_section.addWidget(self.speed_box)

        left_frame = QFrame(self)
        left_frame.setLayout(left_section)
        right_frame = QFrame(self)
        right_frame.setLayout(right_section)

        top_splitter = QSplitter(self)
        top_splitter.setChildrenCollapsible(False)
        top_splitter.addWidget(left_frame)
        top_splitter.addWidget(right_frame)

        self.frame_time_list = PropertyBox("Time for each Frame", FrameList, self)
        self.frame_time_list.setEnabled(False)

        # No need to draw Raw View for this
        # self.raw_view = PropertyBox("Raw Sprite", IconView, self)
        # self.raw_view.edit.setMaximumSize(QSize(360, 360))
        # self.raw_view.edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        final_splitter = QSplitter(self)
        final_splitter.setOrientation(Qt.Vertical)
        final_splitter.setChildrenCollapsible(False)
        final_splitter.addWidget(top_splitter)
        final_splitter.addWidget(self.frame_time_list)
        # final_splitter.addWidget(self.raw_view)

        final_section = QHBoxLayout()
        self.setLayout(final_section)
        final_section.addWidget(final_splitter)

        timer.get_timer().tick_elapsed.connect(self.tick)

    def tick(self):
        if self.current:
            # self.draw_raw()
            self.draw_frame()

    def set_current(self, current):
        self.reset()
        self.current = current
        old_num_frames = self.current.num_frames
        self.frame_box.edit.set_current(current.frame_x, current.frame_y)
        self.total_num_box.edit.setValue(old_num_frames)
        self.speed_box.edit.set_current(current.speed, current.use_frame_time)
        self.frame_time_list.edit.set_current(current)
        self.frame_time_list.setEnabled(current.use_frame_time)
        # self.draw_raw()
        self.draw_frame()

    def which_speed_toggled(self, val: bool):
        self.current.use_frame_time = val
        self.frame_time_list.setEnabled(val)
        self.reset()

    def draw_raw(self):
        pixmap = self.current.pixmap
        base_image = QImage(pixmap.width(), pixmap.height(), QImage.Format_ARGB32)
        base_image.fill(QColor(0, 0, 0, 0))
        painter = QPainter()
        painter.begin(base_image)
        painter.drawImage(0, 0, self.current.pixmap.toImage())
        # Draw grid lines
        painter.setPen(QPen(Qt.black, 1, Qt.DashLine))
        width = self.current.pixmap.width() // self.current.frame_x
        height = self.current.pixmap.height() // self.current.frame_y
        for x in range(self.current.frame_x + 1):
            painter.drawLine(x * width, 0, x * width, self.current.pixmap.height())
        for y in range(self.current.frame_y + 1):
            painter.drawLine(0, y * height, self.current.pixmap.width(), y * height)

        painter.end()

        self.raw_view.edit.set_image(QPixmap.fromImage(base_image))
        self.raw_view.edit.show_image()

    def draw_frame(self):
        if self.playing:
            if self.current.use_frame_time:
                self.frames_passed += 1
                if self.frames_passed > self.current.frame_times[self.counter]:
                    self.counter += 1
                    self.frames_passed = 0
                if self.counter >= len(self.current.frame_times):
                    if not self.loop:
                        self.stop()
                    self.counter = 0
                num = self.counter
            else:
                num = int(time.time() * 1000 - self.last_update) // self.current.speed
                if num >= self.current.num_frames and not self.loop:
                    num = 0
                    self.stop()
                else:
                    num %= self.current.num_frames
        else:
            num = 0

        width = self.current.pixmap.width() // self.current.frame_x
        height = self.current.pixmap.height() // self.current.frame_y
        left = (num % self.current.frame_x) * width
        top = (num // self.current.frame_x) * height
        base_image = self.current.pixmap.copy(left, top, width, height)

        self.frame_view.set_image(base_image)
        self.frame_view.show_image()

    def stop(self):
        self.playing = False
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def reset(self):
        self.stop()
        self.counter = 0
        self.frames_passed = 0

    def play_clicked(self):
        if self.playing:
            self.stop()
        else:
            self.playing = True
            self.last_update = time.time() * 1000
            self.counter = 0
            self.frames_passed = 0
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))

    def loop_clicked(self, val):
        if val:
            self.loop = True
        else:
            self.loop = False

    def frames_changed(self, x, y):
        if self.current:
            self.current.frame_x = x
            self.current.frame_y = y
            minim = x * y - x + 1
            self.total_num_box.edit.setRange(minim, x * y)
            self.total_num_box.edit.setValue(utils.clamp(self.current.num_frames, minim, x * y))
            # Update frame list view
            self.frame_time_list.edit.set_current(self.current)
        # Stop currently drawing and reset counter
        self.reset()

    def num_frames_changed(self, val):
        self.current.num_frames = val
        # Update frame list view
        self.frame_time_list.edit.set_current(self.current)
        # Stop currently drawing and reset counter
        self.reset()
