import sys
import cv2
from PyQt5.QtWidgets import QFileDialog, QWidget, QComboBox, QSizePolicy, QApplication, QMainWindow, QPushButton, \
    QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QListWidget, QListWidgetItem, QCheckBox
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QImage
from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PIL import Image, ImageDraw, ImageEnhance
import os
import numpy as np
import openai
import requests
import random
import math
import pyperclip


def check_key(api_key):
    client = openai.OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "This is a test."}
            ],
            max_tokens=5
        )
    except:
        return False
    else:
        return True


def sec_to_binary(x):
    x = x * 100
    binary = bin(x)
    if len(binary) > 32:
        return False
    return x * 10


def add_gcode(gcode, pw, cpec):
    gcode += f"G0 X0 Y0\n"
    if cpec:
        gcode += f"G92 X{-(pw - 17.5)} Y{-1.5}\n"
        gcode += "G1 X0 Y3\nM74 A1 B0 C0 D0\nG1 X0.75 Y3\nM74 A1 B0 C0 D0\nG1 X1.5 Y3\nM74 A1 B0 C0 D0\n"
        gcode += "G1 X3.75 Y3\nM74 A1 B0 C0 D0\nG1 X4.5 Y3\nM74 A1 B0 C0 D0\nG1 X5.25 Y3\nM74 A1 B0 C0 D0\n"
        gcode += "G1 X9.75 Y3\nM74 A1 B0 C0 D0\nG1 X10.5 Y3\nM74 A1 B0 C0 D0\nG1 X11.25 Y3\nM74 A1 B0 C0 D0\n"
        gcode += "G1 X13.5 Y3\nM74 A1 B0 C0 D0\nG1 X14.25 Y3\nM74 A1 B0 C0 D0\nG1 X15 Y3\nM74 A1 B0 C0 D0\n"
        gcode += "G1 X0 Y2.25\nM74 A1 B0 C0 D0\nG1 X3.75 Y2.25\nM74 A1 B0 C0 D0\nG1 X5.25 Y2.25\n"
        gcode += "M74 A1 B0 C0 D0\nG1 X9.75 Y2.25\nM74 A1 B0 C0 D0\nG1 X13.5 Y2.25\nM74 A1 B0 C0 D0\n"
        gcode += "G1 X0 Y1.5\nM74 A1 B0 C0 D0\nG1 X3.75 Y1.5\nM74 A1 B0 C0 D0\nG1 X4.5 Y1.5\n"
        gcode += "M74 A1 B0 C0 D0\nG1 X5.25 Y1.5\nM74 A1 B0 C0 D0\nG1 X9.75 Y1.5\nM74 A1 B0 C0 D0\n"
        gcode += "G1 X10.5 Y1.5\nM74 A1 B0 C0 D0\nG1 X13.5 Y1.5\nM74 A1 B0 C0 D0\nG1 X0 Y0.75\n"
        gcode += "M74 A1 B0 C0 D0\nG1 X0.75 Y0.75\nM74 A1 B0 C0 D0\nG1 X1.5 Y0.75\nM74 A1 B0 C0 D0\n"
        gcode += "G1 3.75 Y0.75\nM74 A1 B0 C0 D0\nG1 X9.75 Y0.75\nM74 A1 B0 C0 D0\nG1 X13.5 Y0.75\n"
        gcode += "M74 A1 B0 C0 D0\nG1 14.25 Y0.75\nM74 A1 B0 C0 D0\nG1 X15 Y0.75\nM74 A1 B0 C0 D0\n"
        gcode += "G1 X3.75 Y0\nM74 A1 B0 C0 D0\nG1 X9.75 Y0\nM74 A1 B0 C0 D0\n"
        gcode += f"G1 X10.5 Y0\nM74 A1 B0 C0 D0\nG1 X11.25 Y0\nM74 A1 B0 C0 D0\nG92 X{pw - 17.5} Y{1.5}\nG0 X0 Y0"
    return gcode

def player_hand_count(hand):
    num_aces = hand.count(1)
    non_ace_hand_value = sum([card if card != 1 else 0 for card in hand])
    possible_ace_values = []
    for x in range(num_aces + 1):
        possible_ace_values.append(num_aces + (10 * x))
    if num_aces == 0:
        possible_ace_values.append(0)
    possible_values = [value + non_ace_hand_value for value in possible_ace_values]
    possible_legal_values = []
    for value in possible_values:
        if value <= 21:
            possible_legal_values.append(value)
    if len(possible_legal_values) != 0:
        return max(possible_legal_values)
    else:
        return non_ace_hand_value


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')

    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def filter_colors(colors):
    white_colors = ['#FFFFFF', 'FFFFFF', 'ffffff', '#ffffff', [255, 255, 255], [246, 245, 238]]

    filtered_colors = [color for color in colors if color not in white_colors]

    return filtered_colors


class ListItemWidget(QWidget):
    def __init__(self, text, edit_callback, delete_callback):
        super().__init__()
        self.layout = QHBoxLayout()
        self.text = text

        self.lineEdit = QLineEdit(text)
        self.lineEdit.setReadOnly(True)
        self.layout.addWidget(self.lineEdit)

        self.editButton = QPushButton("Edit")
        self.editButton.clicked.connect(self.edit)
        self.layout.addWidget(self.editButton)

        self.deleteButton = QPushButton("Delete")
        self.deleteButton.clicked.connect(delete_callback)
        self.layout.addWidget(self.deleteButton)

        self.setLayout(self.layout)
        self.edit_callback = edit_callback
        self.delete_callback = delete_callback

    def edit(self):
        self.edit_callback(self)

    def setText(self, text):
        self.lineEdit.setText(text)
        self.lineEdit.setReadOnly(True)
        self.editButton.setText("Edit")


class CustomColor(QDialog):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()

        self.setWindowTitle("Enter Custom Colors (HEX)")

        self.listWidget = QListWidget()
        self.layout.addWidget(self.listWidget)

        self.inputLayout = QHBoxLayout()

        self.inputField = QLineEdit()
        self.inputLayout.addWidget(self.inputField)

        self.saveButton = QPushButton("Save")
        self.saveButton.clicked.connect(self.saveItem)
        self.inputLayout.addWidget(self.saveButton)

        self.layout.addLayout(self.inputLayout)

        self.doneButton = QPushButton("Done")
        self.doneButton.clicked.connect(self.accept)
        self.layout.addWidget(self.doneButton)

        self.use_last_checkbox = QCheckBox("Use Last", self)
        self.use_last_checkbox.stateChanged.connect(self.use_last)
        self.layout.addWidget(self.use_last_checkbox)
        self.use_last_checkbox.setEnabled(False)
        if os.path.exists('data/color_order.txt'):
            self.use_last_checkbox.setEnabled(True)

        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.reject)
        self.layout.addWidget(self.cancelButton)

        self.setLayout(self.layout)

        self.currentItem = None
        self.items = []

        self.resize(600, 400)

    def addItem(self, text):
        itemWidget = ListItemWidget(text, self.editItem, lambda: self.deleteItem(itemWidget))
        item = QListWidgetItem()
        item.setSizeHint(itemWidget.sizeHint())
        self.listWidget.addItem(item)
        self.listWidget.setItemWidget(item, itemWidget)

    def editItem(self, widget):
        self.currentItem = widget
        self.inputField.setText(widget.lineEdit.text())
        widget.lineEdit.setReadOnly(False)
        widget.editButton.setText("Editing...")

    def saveItem(self):
        text = self.inputField.text()
        if self.currentItem:
            self.currentItem.setText(text)
        else:
            self.addItem(text)
        self.inputField.clear()
        self.currentItem = None

    def deleteItem(self, widget):
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            if self.listWidget.itemWidget(item) == widget:
                self.listWidget.takeItem(i)
                break

    def use_last(self):
        if os.path.exists('data/color_order.txt'):
            with open('data/color_order.txt', 'r') as file:
                lines = [line.strip() for line in file if line.strip()]

            if self.use_last_checkbox.isChecked():
                existing_items = {self.listWidget.itemWidget(self.listWidget.item(i)).lineEdit.text()
                                  for i in range(self.listWidget.count())}
                for line in lines:
                    if line not in existing_items:
                        self.addItem(line)
            else:
                items_to_remove = set(lines)
                for i in range(self.listWidget.count() - 1, -1, -1):
                    item = self.listWidget.item(i)
                    widget = self.listWidget.itemWidget(item)
                    if widget and widget.lineEdit.text() in items_to_remove:
                        self.listWidget.takeItem(i)

    def accept(self):
        self.items = [self.listWidget.itemWidget(self.listWidget.item(i)).lineEdit.text() for i in
                      range(self.listWidget.count())]
        super().accept()


class ToggleSwitch(QWidget):
    stateChanged = pyqtSignal(bool)

    def __init__(self, on, off, parent=None):
        super(ToggleSwitch, self).__init__(parent)
        self.setFixedSize(100, 30)
        self.checked = True
        self.on = on
        self.off = off

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        outer_rect = QRect(0, 0, self.width(), self.height())
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(150, 150, 150))
        painter.drawRoundedRect(outer_rect, 15, 15)

        inner_width = self.width() // 2
        inner_rect = QRect(0, 0, inner_width, self.height())
        if self.checked:
            inner_rect.moveLeft(0)
        else:
            inner_rect.moveLeft(inner_width)

        painter.setBrush(QColor(255, 255, 255))
        painter.drawRoundedRect(inner_rect, 15, 15)

        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        painter.setPen(Qt.black)

        on_label = self.on
        off_label = self.off

        on_label_rect = QRect(0, 0, inner_width, self.height())
        off_label_rect = QRect(inner_width, 0, inner_width, self.height())

        if self.checked:
            painter.drawText(on_label_rect, Qt.AlignCenter, on_label)
        else:
            painter.drawText(off_label_rect, Qt.AlignCenter, off_label)

    def mousePressEvent(self, event):
        self.checked = not self.checked
        self.update()
        self.stateChanged.emit(self.checked)

    def isChecked(self):
        return self.checked


class APIKeyDialog(QDialog):
    def __init__(self, parent=None):
        super(APIKeyDialog, self).__init__(parent)
        self.setWindowTitle("Enter OpenAI API Key")

        self.api_key = None

        self.layout = QVBoxLayout()

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(self.api_key_input)

        self.buttons_layout = QHBoxLayout()

        self.check_button = QPushButton("Check")
        self.check_button.clicked.connect(self.check_key)
        self.buttons_layout.addWidget(self.check_button)

        self.enter_button = QPushButton("Enter")
        self.enter_button.setEnabled(False)
        self.enter_button.clicked.connect(self.enter)
        self.buttons_layout.addWidget(self.enter_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel)
        self.buttons_layout.addWidget(self.cancel_button)

        self.layout.addLayout(self.buttons_layout)

        self.setLayout(self.layout)
        self.cancels = False

    def check_key(self):
        valid_key = check_key(self.api_key_input.text())
        if not valid_key:
            self.api_key = None
            self.reject()
        else:
            self.enter_button.setEnabled(True)

    def enter(self):
        self.api_key = self.api_key_input.text()
        self.accept()

    def cancel(self):
        self.cancels = True
        self.reject()


class ClickableLabel(QLabel):
    clicked = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.highlighted = False

    def mousePressEvent(self, event):
        self.clicked.emit(self.url)

    def setHighlighted(self, highlighted):
        self.highlighted = highlighted
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.highlighted:
            painter = QPainter(self)
            painter.setBrush(QColor(255, 255, 0, 100))
            painter.drawRect(self.rect())


class EasterEgg(QDialog):
    def __init__(self, parent=None):
        super(EasterEgg, self).__init__(parent)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.question_message = QLabel("Do you want to?", self)
        self.layout.addWidget(self.question_message)

        self.yes_button = QPushButton("Yes", self)
        self.yes_button.clicked.connect(self.accept)
        self.layout.addWidget(self.yes_button)

        self.no_button = QPushButton("No", self)
        self.no_button.clicked.connect(self.reject)
        self.no_button.setDefault(True)
        self.layout.addWidget(self.no_button)


class CustomPageSize(QDialog):
    def __init__(self, parent=None):
        super(CustomPageSize, self).__init__(parent)
        self.setWindowTitle("Enter Custom Page Size")
        self.api_key = None

        self.layout = QVBoxLayout()

        self.page_size_shorter = QLineEdit(self)
        self.page_size_shorter.setPlaceholderText("Enter Width (mm)")
        self.page_size_shorter.setFixedWidth(300)
        self.page_size_shorter.textChanged.connect(self.check_enable_button)
        self.layout.addWidget(self.page_size_shorter)

        self.page_size_longer = QLineEdit(self)
        self.page_size_longer.setPlaceholderText("Enter Height (mm)")
        self.page_size_longer.setFixedWidth(300)
        self.page_size_longer.textChanged.connect(self.check_enable_button)
        self.layout.addWidget(self.page_size_longer)

        self.buttons_layout = QHBoxLayout()

        self.enter_button = QPushButton("Enter")
        self.enter_button.setEnabled(False)
        self.enter_button.clicked.connect(self.enter)
        self.buttons_layout.addWidget(self.enter_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.buttons_layout.addWidget(self.cancel_button)

        self.layout.addLayout(self.buttons_layout)
        self.setLayout(self.layout)

    def check_enable_button(self):
        shorter_text = self.page_size_shorter.text().strip()
        longer_text = self.page_size_longer.text().strip()
        if shorter_text and longer_text:
            self.enter_button.setEnabled(True)
        else:
            self.enter_button.setEnabled(False)

    def enter(self):
        self.shorter_length = float(self.page_size_shorter.text())
        self.longer_length = float(self.page_size_longer.text())
        self.shorter_text = float(self.page_size_shorter.text()) if float(self.page_size_shorter.text()) < float(
            self.page_size_longer.text()) else float(self.page_size_longer.text())
        self.longer_text = float(self.page_size_longer.text()) if float(self.page_size_longer.text()) < float(
            self.page_size_shorter.text()) else float(self.page_size_shorter.text())

        self.accept()


class AdvancedPositioning(QDialog):
    def __init__(self, parent=None):
        super(AdvancedPositioning, self).__init__(parent)
        self.setWindowTitle("Enter Advanced Positioning")
        self.good = True

        self.layout = QVBoxLayout()

        self.x_pos_of_image = QLineEdit(self)
        self.x_pos_of_image.setPlaceholderText("Enter X position of bottom left corner of the image (mm)")
        self.x_pos_of_image.setFixedWidth(500)
        self.x_pos_of_image.textChanged.connect(self.check_enable_button)
        self.layout.addWidget(self.x_pos_of_image)

        self.y_pos_of_image = QLineEdit(self)
        self.y_pos_of_image.setPlaceholderText("Enter Y position of bottom left corner of the image (mm)")
        self.y_pos_of_image.setFixedWidth(500)
        self.y_pos_of_image.textChanged.connect(self.check_enable_button)
        self.layout.addWidget(self.y_pos_of_image)

        self.width_of_image = QLineEdit(self)
        self.width_of_image.setPlaceholderText("Enter the width of the image (mm)")
        self.width_of_image.setFixedWidth(500)
        self.width_of_image.textChanged.connect(self.check_enable_button)
        self.layout.addWidget(self.width_of_image)

        self.buttons_layout = QHBoxLayout()

        self.enter_button = QPushButton("Enter")
        self.enter_button.setEnabled(False)
        self.enter_button.clicked.connect(self.enter)
        self.buttons_layout.addWidget(self.enter_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel)
        self.buttons_layout.addWidget(self.cancel_button)

        self.layout.addLayout(self.buttons_layout)
        self.setLayout(self.layout)

    def check_enable_button(self):
        x_text = self.x_pos_of_image.text().strip()
        y_text = self.y_pos_of_image.text().strip()
        w_text = self.width_of_image.text().strip()

        if x_text and y_text and w_text:
            self.enter_button.setEnabled(True)
        else:
            self.enter_button.setEnabled(False)

    def enter(self):
        self.x_pos = float(self.x_pos_of_image.text())
        self.y_pos = float(self.y_pos_of_image.text())
        self.width = float(self.width_of_image.text())
        self.accept()

    def cancel(self):
        self.good = False
        self.accept()


class ImagePickerDialog(QDialog):
    def __init__(self, urls, parent=None):
        super().__init__(parent)
        self.selected_image_url = None
        self.image_urls = urls
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Image Picker')
        self.setGeometry(200, 200, 600, 400)

        self.setupLayout()

    def setupLayout(self):
        main_layout = QVBoxLayout()
        image_layout = QHBoxLayout()

        self.labels = []
        for url in self.image_urls:
            pixmap = self.loadImageFromUrl(url)
            if pixmap:
                label = ClickableLabel(url)
                label.setPixmap(pixmap)
                label.clicked.connect(self.imageClicked)
                image_layout.addWidget(label)
                self.labels.append(label)

        button_layout = QHBoxLayout()

        use_button = QPushButton("Use Image", self)
        use_button.clicked.connect(self.select_image)
        button_layout.addWidget(use_button)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(image_layout)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def loadImageFromUrl(self, url):
        try:
            response = requests.get(url, verify=False)
            if response.status_code == 200:
                data = response.content
                pixmap = QPixmap()
                pixmap.loadFromData(data)
                pixmap = pixmap.scaledToWidth(150)
                return pixmap
            else:
                return None
        except Exception as e:
            return None

    def imageClicked(self, url):
        self.selected_image_url = url
        for label in self.labels:
            label.setHighlighted(label.url == self.selected_image_url)

    def select_image(self):
        if self.selected_image_url:
            self.accept()


class Deck():
    def __init__(self):
        deck = [rank for rank in range(1, 14) for _ in range(4)]
        self.deck = [card if card < 10 else 10 for card in deck]

    def draw_card(self):
        return self.deck.pop()

    def shuffle_deck(self):
        random.shuffle(self.deck)


class BlackJackPlay(QDialog):
    def __init__(self, hand, dealers_hand, high_score, current_score):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.question_message = QLabel(f"High Score: {high_score if high_score >= current_score else current_score}\nCurrent Score: {current_score}\nYour Hand: {[str(card) if card != 1 else f"1/11" for card in hand]}\nYour Total: {player_hand_count(hand)}\nDealer's Hand: {dealers_hand[0] if dealers_hand[0] != 1 else "1/11"}", self)
        self.layout.addWidget(self.question_message)

        self.yes_button = QPushButton("Hit", self)
        self.yes_button.clicked.connect(self.accept)
        self.layout.addWidget(self.yes_button)

        self.no_button = QPushButton("Stand", self)
        self.no_button.clicked.connect(self.reject)
        self.layout.addWidget(self.no_button)


class BlackJackShow(QDialog):
    def __init__(self, message):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.question_message = QLabel(message, self)
        self.layout.addWidget(self.question_message)

        self.yes_button = QPushButton("Ok", self)
        self.yes_button.clicked.connect(self.accept)
        self.layout.addWidget(self.yes_button)

        self.exec_()


class ShowColors(QDialog):
    def __init__(self, colors):
        super().__init__()

        self.colors = colors

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.question_message = QLabel(colors)
        self.layout.addWidget(self.question_message)

        self.copy_button = QPushButton("Copy", self)
        if not os.path.exists("data/color_order.txt"):
            self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(self.copy)
        self.layout.addWidget(self.copy_button)

        self.close_button = QPushButton("Close", self)
        self.close_button.clicked.connect(self.reject)
        self.layout.addWidget(self.close_button)

    def copy(self):
        self.copy_button.setEnabled(False)
        pyperclip.copy(self.colors)


class ImageSlicer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Slicer")
        self.initUI()
        self.showMaximized()

    def initUI(self):
        self.good = False
        self.save_left_image = True
        self.first_search = True
        self.last_search = ''
        self.last_search_toggle = False
        self.outline_width = 3
        self.brightness = 0.65
        self.display_img = None
        self.x_offset = 0
        self.y_offset = 0
        self.rotated = False
        self.bed_width = 687
        self.bed_height = 640
        self.egg_url = "https://www.akc.org/wp-content/uploads/2017/11/Pembroke-Welsh-Corgi-standing-outdoors-in-the-fall.jpg"
        if os.path.exists('data/default_settings.txt'):
            with open('data/default_settings.txt', 'r') as file:
                self.max_score = float(file.readlines()[13].strip())
        else:
            self.max_score = 0
        self.current_score = 0

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.image_layout = QHBoxLayout()

        self.original_image_label = QLabel(self)
        self.original_image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_layout.addWidget(self.original_image_label)

        self.sliced_image_ui = QVBoxLayout()

        self.sliced_image_label = QLabel(self)
        self.sliced_image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sliced_image_label.setAlignment(Qt.AlignRight)
        self.sliced_image_ui.addWidget(self.sliced_image_label)

        self.sliced_ui_button_layout = QHBoxLayout()

        self.left_arrow_button = QPushButton("<", self)
        self.left_arrow_button.setEnabled(False)
        self.left_arrow_button.clicked.connect(self.display_sliced_image)
        self.sliced_ui_button_layout.addWidget(self.left_arrow_button)

        self.right_arrow_button = QPushButton(">", self)
        self.right_arrow_button.setEnabled(False)
        self.right_arrow_button.clicked.connect(self.display_sliced_paper_image)
        self.sliced_ui_button_layout.addWidget(self.right_arrow_button)

        self.sliced_image_ui.addLayout(self.sliced_ui_button_layout)
        self.image_layout.addLayout(self.sliced_image_ui)
        self.layout.addLayout(self.image_layout)

        self.search_layout = QHBoxLayout()

        self.search_toggle = ToggleSwitch("Google", "AI")
        self.search_layout.addWidget(self.search_toggle)
        self.search_toggle.stateChanged.connect(self.change_button)

        self.search_text = QLineEdit(self)
        self.search_text.setPlaceholderText("Enter Description")
        self.search_layout.addWidget(self.search_text)
        self.search_text.editingFinished.connect(self.search_reset)

        self.search_button = QPushButton("Search", self)
        self.search_button.clicked.connect(self.search)
        self.search_layout.addWidget(self.search_button)

        self.layout.addLayout(self.search_layout)

        self.open_button = QPushButton("Open Image", self)
        self.open_button.clicked.connect(self.open_image)
        self.open_button.clicked.connect(self.top_reset)
        self.layout.addWidget(self.open_button)

        self.pixel_size_layout = QHBoxLayout()
        self.layout.addLayout(self.pixel_size_layout)
        self.pixel_size_label = QLabel("Pixel Size (mm):", self)
        self.pixel_size_layout.addWidget(self.pixel_size_label)
        self.pixel_size = QLineEdit(self)
        self.pixel_size.setPlaceholderText("Enter pixel size")
        self.pixel_size_layout.addWidget(self.pixel_size)
        self.pixel_size.editingFinished.connect(self.reset)

        self.toggle_switch = ToggleSwitch("Portrait", "Landscape")
        self.layout.addWidget(self.toggle_switch)
        self.toggle_switch.stateChanged.connect(self.reset)

        self.page_size_layout = QHBoxLayout()
        self.layout.addLayout(self.page_size_layout)
        self.page_size_label = QLabel("Page Size:", self)
        self.page_size_layout.addWidget(self.page_size_label)
        self.page_size = QComboBox(self)
        self.page_size.addItems(
            ["Letter", "A4", "Index (4\"x6\")", f"Full ({self.bed_width}mmX{self.bed_height}mm)", "Custom (mm)"])
        self.page_size_layout.addWidget(self.page_size)
        self.page_size.currentIndexChanged.connect(self.reset)

        self.color_type_layout = QHBoxLayout()
        self.layout.addLayout(self.color_type_layout)
        self.color_type_label = QLabel("Color Type:", self)
        self.color_type_layout.addWidget(self.color_type_label)
        self.color_type = QComboBox(self)
        self.color_type.addItems(["RGB", "BW", "CMYK", "Custom (HEX)"])
        self.color_type_layout.addWidget(self.color_type)
        self.color_type.currentIndexChanged.connect(self.reset)

        self.margin_layout = QHBoxLayout()
        self.layout.addLayout(self.margin_layout)
        self.margin_label = QLabel("Margin (mm):", self)
        self.margin_layout.addWidget(self.margin_label)
        self.margin = QLineEdit(self)
        self.margin.setPlaceholderText("Enter margin")
        self.margin_layout.addWidget(self.margin)
        self.margin.editingFinished.connect(self.reset)

        self.speed_layout = QHBoxLayout()
        self.layout.addLayout(self.speed_layout)
        self.speed_label = QLabel("Speed (mm/s):", self)
        self.speed_layout.addWidget(self.speed_label)
        self.speed = QLineEdit(self)
        self.speed.setPlaceholderText("Enter speed")
        self.speed_layout.addWidget(self.speed)
        self.speed.editingFinished.connect(self.reset)
        self.solenoid_label = QLabel("Solenoid Extention Time (sec):")
        self.speed_layout.addWidget(self.solenoid_label)
        self.solenoid_time = QLineEdit(self)
        self.solenoid_time.setPlaceholderText("Enter solenoid extention time")
        self.speed_layout.addWidget(self.solenoid_time)
        self.solenoid_time.editingFinished.connect(self.reset)

        self.x_pen_dis_layout = QHBoxLayout()
        self.layout.addLayout(self.x_pen_dis_layout)
        self.x_pen_dis_label = QLabel("X Pen Distance (mm):", self)
        self.x_pen_dis_layout.addWidget(self.x_pen_dis_label)
        self.x_pen_dis = QLineEdit(self)
        self.x_pen_dis.setPlaceholderText("Enter X pen distance")
        self.x_pen_dis_layout.addWidget(self.x_pen_dis)
        self.x_pen_dis.editingFinished.connect(self.reset)

        self.y_pen_dis_layout = QHBoxLayout()
        self.layout.addLayout(self.y_pen_dis_layout)
        self.y_pen_dis_label = QLabel("Y Pen Distance (mm):", self)
        self.y_pen_dis_layout.addWidget(self.y_pen_dis_label)
        self.y_pen_dis = QLineEdit(self)
        self.y_pen_dis.setPlaceholderText("Enter Y pen distance")
        self.y_pen_dis_layout.addWidget(self.y_pen_dis)
        self.y_pen_dis.editingFinished.connect(self.reset)

        self.tolerance_layout = QHBoxLayout()
        self.layout.addLayout(self.tolerance_layout)
        self.tolerance_label = QLabel("Tolerance (mm):", self)
        self.tolerance_layout.addWidget(self.tolerance_label)
        self.tolerance = QLineEdit(self)
        self.tolerance.setPlaceholderText("Enter Tolerance")
        self.tolerance_layout.addWidget(self.tolerance)
        self.tolerance.editingFinished.connect(self.reset)

        self.settings_layout = QHBoxLayout()

        self.load_settings_button = QPushButton("Load Settings", self)
        self.load_settings_button.setEnabled(False)
        self.load_settings_button.clicked.connect(self.load_default_settings)
        self.settings_layout.addWidget(self.load_settings_button)

        self.save_settings = QPushButton("Save Settings", self)
        self.save_settings.setEnabled(False)
        self.save_settings.clicked.connect(self.save_setting)
        self.settings_layout.addWidget(self.save_settings)

        self.layout.addLayout(self.settings_layout)

        self.slicer_row_layout = QHBoxLayout()
        self.checkbox_layout = QHBoxLayout()

        self.accuracy_checkbox = QCheckBox("Accuracy", self)
        self.accuracy_checkbox.stateChanged.connect(self.reset)
        self.accuracy_checkbox.stateChanged.connect(self.tolerance_off)
        self.checkbox_layout.addWidget(self.accuracy_checkbox)
        self.tolerance.setEnabled(self.accuracy_checkbox.isChecked() == True)

        self.advanced_pos_checkbox = QCheckBox("Advanced Positioning", self)
        self.advanced_pos_checkbox.stateChanged.connect(self.reset)
        self.advanced_pos_checkbox.stateChanged.connect(self.margin_off)
        self.checkbox_layout.addWidget(self.advanced_pos_checkbox)

        self.rotate_checkbox = QCheckBox("Rotate Image 90° Clockwise", self)
        self.rotate_checkbox.stateChanged.connect(self.reset)
        self.checkbox_layout.addWidget(self.rotate_checkbox)

        self.cpec_checkbox = QCheckBox("CPEC Watermark", self)
        self.cpec_checkbox.stateChanged.connect(self.reset)
        self.checkbox_layout.addWidget(self.cpec_checkbox)

        self.slicer_row_layout.addLayout(self.checkbox_layout)

        self.slicer_button = QPushButton("Slice", self)
        self.slicer_button.setEnabled(False)
        self.slicer_button.clicked.connect(self.slice)
        self.slicer_row_layout.addWidget(self.slicer_button)

        self.layout.addLayout(self.slicer_row_layout)

        self.save_color_layout = QHBoxLayout()

        self.colors_button = QPushButton("Show Custom Color Order", self)
        self.colors_button.clicked.connect(self.show_colors)
        self.save_color_layout.addWidget(self.colors_button)

        self.save_button = QPushButton("Save Image", self)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_image)
        self.save_color_layout.addWidget(self.save_button)

        self.layout.addLayout(self.save_color_layout)

        self.save_gcode = QPushButton("Save GCode", self)
        self.save_gcode.setEnabled(False)
        self.save_gcode.clicked.connect(self.save_gcod)
        self.layout.addWidget(self.save_gcode)

        self.image = None
        self.sliced_image = None

        self.pixel_size.setText("0.75")
        self.page_size.setCurrentIndex(0)
        self.color_type.setCurrentIndex(0)
        self.margin.setText("5")
        self.speed.setText("100")
        self.solenoid_time.setText("0.5")
        self.x_pen_dis.setText("48")
        self.y_pen_dis.setText("78")
        self.advanced_pos_checkbox.setChecked(False)
        self.rotate_checkbox.setChecked(False)
        self.cpec_checkbox.setChecked(False)
        self.load_default_settings()

        if self.ai_key != 'None':
            correct_key = check_key(self.ai_key)
            if not correct_key:
                self.save_setting(True)

    def open_image(self, searched=False):
        if searched:
            file_path = 'data/tobesliced.png'
            self.image_path = file_path
            self.image = cv2.imread(file_path)
            self.display_original_image()
            self.good = True
            self.top_reset()
        else:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
            if file_path:
                self.image_path = file_path
                self.image = cv2.imread(file_path)
                self.display_original_image()
                self.good = True
                self.top_reset()

    def show_colors(self):
        fil = 'data/color_order.txt'
        if os.path.exists(fil):
            with open(fil, 'r') as file:
                unfiltered_colors = file.readlines()
        unfiltered_colors = [color.strip() for color in unfiltered_colors]
        filtered_colors = filter_colors(unfiltered_colors)
        final_colors = ""
        for color in filtered_colors:
            final_colors += color
            final_colors += "\n"
        dialog = ShowColors(final_colors)
        dialog.exec_()


    def display_original_image(self):
        self.rotated = False
        if self.image is not None:
            if isinstance(self.image, np.ndarray):
                rgb_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
                height, width, channel = rgb_image.shape
                bytes_per_line = channel * width
                q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            else:
                img = self.image.convert('RGB')
                np_img = np.array(img)
                height, width, channel = np_img.shape
                bytes_per_line = channel * width
                q_image = QImage(np_img.data, width, height, bytes_per_line, QImage.Format_RGB888)

            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(self.original_image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

            self.original_image_label.setPixmap(scaled_pixmap)

    def display_sliced_image(self):
        self.left_arrow_button.setEnabled(False)
        self.right_arrow_button.setEnabled(True)
        self.save_left_image = True
        if self.sliced_image is not None:
            if self.sliced_image.mode not in ["RGB", "L"]:
                temp_img = self.sliced_image.convert("RGB")

            enhancer = ImageEnhance.Brightness(temp_img)
            self.display_img = enhancer.enhance(self.brightness)

            if isinstance(self.display_img, np.ndarray):
                rgb_image = cv2.cvtColor(self.display_img, cv2.COLOR_BGR2RGB)
                height, width, channel = rgb_image.shape
                bytes_per_line = channel * width
                qImg = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            else:
                img = self.display_img.convert('RGBA')
                img = img.transpose(Image.FLIP_TOP_BOTTOM)
                data = img.tobytes("raw", "RGBA")
                qImg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)

            label_size = self.sliced_image_label.size()
            scaled_qImg = qImg.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            self.sliced_image_label.setPixmap(QPixmap.fromImage(scaled_qImg))

    def display_sliced_paper_image(self):
        self.left_arrow_button.setEnabled(True)
        self.right_arrow_button.setEnabled(False)
        self.save_left_image = False
        if self.sliced_paper_image is not None:
            if isinstance(self.sliced_paper_image, np.ndarray):
                rgb_image = cv2.cvtColor(self.sliced_paper_image, cv2.COLOR_BGR2RGB)
                height, width, channel = rgb_image.shape
                bytes_per_line = channel * width
                qImg = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            else:
                img = self.sliced_paper_image.convert('RGBA')
                data = img.tobytes("raw", "RGBA")
                qImg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)

            label_size = self.sliced_image_label.size()
            scaled_qImg = qImg.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            self.sliced_image_label.setPixmap(QPixmap.fromImage(scaled_qImg))

    def save_image(self):
        if self.save_left_image:
            if self.sliced_image is not None:
                file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "",
                                                           "Image Files (*.png *.jpg *.jpeg *.bmp)")
                if file_path:
                    imgg = self.sliced_image.copy()
                    imgggg = imgg.transpose(Image.FLIP_TOP_BOTTOM)
                    imgggg.save(file_path)
        else:
            if self.sliced_paper_image is not None:
                file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "",
                                                           "Image Files (*.png *.jpg *.jpeg *.bmp)")
                if file_path:
                    paper_img = self.sliced_paper_image.copy()
                    paper_img.save(file_path)

    def save_setting(self, nonexisting_api_key=False):
        self.save_settings.setEnabled(False)
        self.load_settings_button.setEnabled(False)
        settings_file = 'data/default_settings.txt'
        self.color = "RGB"
        with open(settings_file, 'w') as file:
            file.write(f"{self.pixel_size.text()}\n")
            file.write(f"{self.page_size.currentText()}\n")
            file.write(f"{self.color_type.currentText()}\n")
            file.write(f"{self.margin.text()}\n")
            file.write(f"{self.speed.text()}\n")
            file.write(f"{self.x_pen_dis.text()}\n")
            file.write(f"{self.y_pen_dis.text()}\n")
            file.write(f"{str(self.toggle_switch.checked)}\n")
            if nonexisting_api_key:
                file.write("None\n")
            else:
                file.write(f"{self.ai_key}\n")
            file.write(f"{str(self.advanced_pos_checkbox.isChecked())}\n")
            file.write(f"{str(self.rotate_checkbox.isChecked())}\n")
            file.write(f"{str(self.cpec_checkbox.isChecked())}\n")
            file.write(f"{str(self.solenoid_time.text())}\n")
            file.write(f"{str(self.max_score)}\n")
            file.write(f"{str(self.accuracy_checkbox.isChecked())}\n")
            file.write(f"{str(self.tolerance.text())}\n")


    def save_score(self):
        settings_file = 'data/default_settings.txt'

        with open(settings_file, 'r') as file:
            lines = file.readlines()
            if len(lines) == 16:
                set_pixel_size = lines[0].strip()
                set_page_size = lines[1].strip()
                set_color_type = lines[2].strip()
                set_margin = lines[3].strip()
                set_speed = lines[4].strip()
                set_x_pen_dis = lines[5].strip()
                set_y_pen_dis = lines[6].strip()
                set_toggle_switch = lines[7].strip() == 'True'
                set_ai_key = lines[8].strip()
                set_advanced_pos_checkbox = lines[9].strip() == "True"
                set_rotate_checkbox = lines[10].strip() == "True"
                set_cpec_checkbox = lines[11].strip() == "True"
                set_solenoid_time = lines[12].strip()
                set_current_score = lines[13].strip()
                set_accuracy_checkbox = lines[14].strip() == "True"
                set_tolerance = lines[15].strip()

        with open(settings_file, 'w') as file:
            file.write(f"{set_pixel_size}\n")
            file.write(f"{set_page_size}\n")
            file.write(f"{set_color_type}\n")
            file.write(f"{set_margin}\n")
            file.write(f"{set_speed}\n")
            file.write(f"{set_x_pen_dis}\n")
            file.write(f"{set_y_pen_dis}\n")
            file.write(f"{str(set_toggle_switch)}\n")
            file.write(f"{set_ai_key}\n")
            file.write(f"{str(set_advanced_pos_checkbox)}\n")
            file.write(f"{str(set_rotate_checkbox)}\n")
            file.write(f"{str(set_cpec_checkbox)}\n")
            file.write(f"{set_solenoid_time}\n")
            file.write(f"{str(self.current_score)}\n")
            file.write(f"{str(set_accuracy_checkbox)}\n")
            file.write(f"{str(set_tolerance)}\n")

    def load_default_settings(self):
        self.save_settings.setEnabled(False)
        self.load_settings_button.setEnabled(False)
        settings_file = 'data/default_settings.txt'
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as file:
                lines = file.readlines()
                if len(lines) == 16:
                    self.pixel_size.setText(lines[0].strip())
                    self.page_size.setCurrentText(lines[1].strip())
                    self.color_type.setCurrentText(lines[2].strip())
                    self.margin.setText(lines[3].strip())
                    self.speed.setText(lines[4].strip())
                    self.x_pen_dis.setText(lines[5].strip())
                    self.y_pen_dis.setText(lines[6].strip())
                    self.toggle_switch.checked = lines[7].strip() == 'True'
                    self.ai_key = lines[8].strip()
                    self.advanced_pos_checkbox.setChecked((lines[9].strip() == "True"))
                    self.rotate_checkbox.setChecked((lines[10].strip() == "True"))
                    self.cpec_checkbox.setChecked((lines[11].strip() == "True"))
                    self.solenoid_time.setText(lines[12].strip())
                    self.max_score = int(lines[13].strip())
                    self.accuracy_checkbox.setChecked((lines[14].strip() == "True"))
                    self.tolerance.setText(lines[15].strip())
        else:
            os.makedirs('data')
            with open(settings_file, 'w') as file:
                file.write('')
            self.save_setting(True)
            self.load_default_settings()

    def save_gcod(self):
        if hasattr(self, 'gcod'):
            gcode_file_path, _ = QFileDialog.getSaveFileName(self, "Save GCode", "", "GCode Files (*.gcode)")
            if gcode_file_path:
                with open(gcode_file_path, 'w') as file:
                    file.write(self.gcod)

    def blackjack(self):
        deck = Deck()
        deck.shuffle_deck()
        players_hand = [deck.draw_card() for _ in range(2)]
        dealers_hand = [deck.draw_card() for _ in range(2)]
        if 1 in dealers_hand and 10 in dealers_hand:
            message = f"High Score: {self.max_score if self.max_score >= self.current_score else self.current_score}\nCurrent Score: {self.current_score}\nYour Hand: {[str(card) if card != 1 else f"1/11" for card in players_hand]}\nYour Total: {player_hand_count(players_hand)}\nDealer's Hand: {[str(card) if card != 1 else f"1/11" for card in dealers_hand]}\nDealer's Total: {player_hand_count(dealers_hand)}\nBlackjack! You Lose!"
            BlackJackShow(message)
            return False
        if 1 in players_hand and 10 in players_hand:
            message = f"High Score: {self.max_score if self.max_score >= self.current_score else self.current_score}\nCurrent Score: {self.current_score}\nYour Hand: {[str(card) if card != 1 else f"1/11" for card in players_hand]}\nYour Total: {player_hand_count(players_hand)}\nBlackjack!"
            self.current_score += 1.5
            BlackJackShow(message)
            good = self.blackjack()
            if not good:
                return False
        while True:
            dialog = BlackJackPlay(players_hand, dealers_hand, self.max_score, self.current_score)
            if dialog.exec_() == QDialog.Accepted:
                players_hand.append(deck.draw_card())
                if player_hand_count(players_hand) > 21:
                    message = f"High Score: {self.max_score if self.max_score >= self.current_score else self.current_score}\nCurrent Score: {self.current_score}\nYour Hand: {[str(card) if card != 1 else f"1/11" for card in players_hand]}\nYour Total: {player_hand_count(players_hand)}\nBust!"
                    BlackJackShow(message)
                    return False
            else:
                player_score = player_hand_count(players_hand)
                if player_score > 21:
                    BlackJackShow(f"High Score: {self.max_score if self.max_score >= self.current_score else self.current_score}\nCurrent Score: {self.current_score}\nYour Hand: {[str(card) if card != 1 else f"1/11" for card in players_hand]}\nYour Total: {player_hand_count(players_hand)}\nBust!")
                    return False
                while player_hand_count(dealers_hand) <= 16:
                    dealers_hand.append(deck.draw_card())
                dealers_score = player_hand_count(dealers_hand)
                if player_score == dealers_score:
                    BlackJackShow(f"High Score: {self.max_score if self.max_score >= self.current_score else self.current_score}\nCurrent Score: {self.current_score}\nYour Hand: {[str(card) if card != 1 else f"1/11" for card in players_hand]}\nYour Total: {player_hand_count(players_hand)}\nDealer's Hand: {[str(card) if card != 1 else f"1/11" for card in dealers_hand]}\nDealer's Total: {player_hand_count(dealers_hand)}\nPush!")
                    self.current_score += 0.5
                    good = self.blackjack()
                    if not good:
                        return False
                elif player_score < dealers_score and dealers_score < 22:
                    BlackJackShow(f"High Score: {self.max_score if self.max_score >= self.current_score else self.current_score}\nCurrent Score: {self.current_score}\nYour Hand: {[str(card) if card != 1 else f"1/11" for card in players_hand]}\nYour Total: {player_hand_count(players_hand)}\nDealer's Hand: {[str(card) if card != 1 else f"1/11" for card in dealers_hand]}\nDealer's Total: {player_hand_count(dealers_hand)}\nYou Lose!")
                    return False
                else:
                    BlackJackShow(f"High Score: {self.max_score if self.max_score >= self.current_score else self.current_score}\nCurrent Score: {self.current_score}\nYour Hand: {[str(card) if card != 1 else f"1/11" for card in players_hand]}\nYour Total: {player_hand_count(players_hand)}\nDealer's Hand: {[str(card) if card != 1 else f"1/11" for card in dealers_hand]}\nDealer's Total: {player_hand_count(dealers_hand)}\nYou Win!")
                    self.current_score += 1
                    good = self.blackjack()
                    if not good:
                        return False



    def slice(self):
        if hasattr(self, 'image_path'):
            px_size = float(self.pixel_size.text())
            por = self.toggle_switch.isChecked()
            paper = self.page_size.currentText()
            color = self.color_type.currentText()
            mar = float(self.margin.text())
            sped = float(self.speed.text())
            pendis = (float(self.x_pen_dis.text()), float(self.y_pen_dis.text()))
            advanced = self.advanced_pos_checkbox.isChecked()
            solenoid_ext_time = float(self.solenoid_time.text()) * 100
            if color == "RGB":
                pallete = [
                    255, 0, 0,
                    0, 0, 255,
                    0, 255, 0,
                    0, 0, 0,
                    255, 255, 255
                ]
            elif color == "BW":
                pallete = [
                    0, 0, 0,
                    255, 255, 255
                ]
            elif color == "CMYK":
                pallete = [
                    0, 255, 255,
                    255, 0, 255,
                    255, 255, 0,
                    0, 0, 0
                ]
            else:
                pallete = []
                palete_list = CustomColor()
                if palete_list.exec_() == QDialog.Accepted:
                    hex_list = palete_list.items
                    hex_list = list(set(hex_list))
                    filtered_list = filter_colors(hex_list)
                    filename = 'data/color_order.txt'
                    with open(filename, 'w') as file:
                        for item in hex_list:
                            file.write(f"{item}\n")
                    for hex in hex_list:
                        rgb = hex_to_rgb(hex)
                        for color in rgb:
                            pallete.append(color)
                else:
                    return False

            palllete = [pallete[i:i + 3] for i in range(0, len(pallete), 3)]
            pallllete = filter_colors(palllete)

            image = Image.open(self.image_path)
            if self.rotate_checkbox.isChecked():
                if not self.rotated:
                    self.rotated = True
                    image = image.rotate(-90, expand=True)
            else:
                if self.rotated:
                    image = image.rotate(90, expand=True)
                    self.rotated = False
            new_image_path = 'data/tobesliced.png'
            image.save(new_image_path, "PNG")
            self.image_path = new_image_path

            result = self.pixelate(self.image_path, px_size, por, paper, mar, palllete, advanced)
            if result == False:
                return False
            self.sliced_image = result[0]
            self.sliced_paper_image = result[4]
            self.display_sliced_image()
            self.save_button.setEnabled(True)

            image = result[0]
            ps = (result[1], result[2])
            pwhw = result[3]

            colors = self.get_c_pos(image, pendis, px_size)
            banana = self.create_groups(colors, pallllete, pendis, px_size, color)
            self.gcod = self.grbl_gen(banana, px_size, por, ps, sped, pwhw, color, result[5], solenoid_ext_time)
            if color != "Custom (HEX)" or paper != "Custom (mm)" or advanced:
                self.slicer_button.setEnabled(True)
            self.save_gcode.setEnabled(True)

    def apply_indexed_color(self, image, pal):
        img = image.convert('RGB')
        palette = [val for sublist in pal for val in sublist]
        p_img = Image.new('P', (1, 1))
        p_img.putpalette(bytes(palette))

        conv = img.quantize(palette=p_img, dither=Image.FLOYDSTEINBERG)

        return conv

    def pixelate(self, image_path, pxl_size, port, paper_s, marg, pall, adv):
        paper_dict = {"Letter": (215.9, 279.4), "A4": (210, 297), "Index (4\"x6\")": (101.6, 152.4),
                      f"Full ({self.bed_width}mmX{self.bed_height}mm)": (
                      self.bed_width if self.bed_width < self.bed_height else self.bed_height,
                      self.bed_height if self.bed_height > self.bed_width else self.bed_width)}
        if paper_s not in paper_dict:
            dialog = CustomPageSize(self)
            if dialog.exec_() == QDialog.Accepted:
                paper_dict[paper_s] = (dialog.shorter_length, dialog.longer_length)
            else:
                return False

        img = Image.open(image_path)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)

        pw, ph = paper_dict[paper_s]

        if not port:
            temp_pw = ph
            temp_ph = pw
        else:
            temp_ph = ph
            temp_pw = pw

        if temp_pw > self.bed_width and temp_ph > self.bed_height:
            pw = self.bed_width
            ph = self.bed_height
        elif temp_pw > self.bed_width and temp_ph <= self.bed_height:
            pw = self.bed_width
            ph = temp_ph
        elif temp_pw <= self.bed_width and temp_ph > self.bed_height:
            pw = temp_pw
            ph = self.bed_height
        else:
            pw = temp_pw
            ph = temp_ph

        if adv:
            while True:
                adv_settings_dialog = AdvancedPositioning()
                if adv_settings_dialog.exec_() == QDialog.Accepted:
                    if adv_settings_dialog.good == False:
                        return False
                    adv_settings = [adv_settings_dialog.x_pos, adv_settings_dialog.y_pos, adv_settings_dialog.width, 0]
                    img_h = (img.height * adv_settings[2]) // img.width
                    adv_settings.append(img_h)
                    small_enough = (adv_settings[0] + adv_settings[2]) <= pw and (adv_settings[1] + img_h) <= ph
                    if small_enough:
                        break

            w_px = adv_settings[2] // pxl_size
            h_px = img_h // pxl_size

            target_resolution = (int(math.floor(w_px)), int(math.floor(h_px)))

            img = img.resize(target_resolution, Image.NEAREST)
            img = self.apply_indexed_color(img, pall)

            clr = (255, 255, 255)

            w_px = math.floor(pw / pxl_size)
            h_px = math.floor(ph / pxl_size)

            paper_img = Image.new("RGB", (w_px, h_px), color=clr)

            draw = ImageDraw.Draw(paper_img)
            outline_width = self.outline_width
            draw.rectangle(
                [(0, 0), (w_px - 1, h_px - 1)],
                outline="black",
                width=outline_width
            )

            paste_position = (
                int(math.floor(adv_settings[0] // pxl_size)),
                int(math.floor((ph // pxl_size) - ((adv_settings[1] // pxl_size) + (img_h // pxl_size))))
            )

            if img.mode not in ["RGB", "L"]:
                paste_img = img.convert("RGB")

            enhancer = ImageEnhance.Brightness(paste_img)
            paste_img = enhancer.enhance(self.brightness)

            paste_img = paste_img.transpose(Image.FLIP_TOP_BOTTOM)

            paper_img.paste(paste_img, paste_position)

        else:
            pw -= float(marg) * 2
            ph -= float(marg) * 2
            ready = True

            if pw <= 0 or ph <= 0:
                ready = False
                pw += float(marg) * 2
                ph += float(marg) * 2

            w, h = img.size

            w_px = math.floor(pw / pxl_size)
            h_px = math.floor(ph / pxl_size)

            if port:
                if pw / ph < w / h:
                    h_px = math.floor((h * w_px) / w)
                    target_resolution = (w_px, h_px)
                else:
                    w_px = math.floor((w * h_px) / h)
                    target_resolution = (w_px, h_px)
            else:
                if pw / ph > w / h:
                    w_px = math.floor((w * h_px) / h)
                    target_resolution = (w_px, h_px)
                else:
                    h_px = math.floor((h * w_px) / w)
                    target_resolution = (w_px, h_px)

            img = img.resize(target_resolution, Image.NEAREST)
            img = self.apply_indexed_color(img, pall)

            clr = (255, 255, 255)

            if ready:
                pw += float(marg) * 2
                ph += float(marg) * 2

            w_px = math.floor(pw / pxl_size)
            h_px = math.floor(ph / pxl_size)

            paper_img = Image.new("RGB", (w_px, h_px), color=clr)

            draw = ImageDraw.Draw(paper_img)
            outline_width = self.outline_width
            draw.rectangle(
                [(0, 0), (w_px - 1, h_px - 1)],
                outline="black",
                width=outline_width
            )

            paste_position = (
                (w_px // 2) - img.width // 2,
                (h_px // 2) - img.height // 2
            )

            if img.mode not in ["RGB", "L"]:
                paste_img = img.convert("RGB")

            enhancer = ImageEnhance.Brightness(paste_img)
            paste_img = enhancer.enhance(self.brightness)

            paste_img = paste_img.transpose(Image.FLIP_TOP_BOTTOM)

            paper_img.paste(paste_img, paste_position)

        paper_img.save("data/paperimage.png")
        slice_name = "data/slicedimage.png"
        img.save(slice_name)

        w, h = img.size
        pwh = paper_dict[paper_s]

        return img, w, h, pwh, paper_img, False if not adv else adv_settings

    def get_c_pos(self, img, pendist, px_siz):
        color_map = {i: tuple(img.getpalette()[i * 3:i * 3 + 3]) for i in range(len(img.getpalette()) // 3)}

        xpen, ypen = pendist
        width, height = img.size
        realwidth = width + (int(xpen / px_siz))
        realheight = height + (int(ypen / px_siz))

        posdict = {}
        rev = 0

        for x in list(range(realwidth)):
            for y in range(realheight):
                xlis = list(range(realheight))
                if rev % 2 != 0:
                    xlis = xlis[::-1]
                pos = (x, xlis[y])
                if 0 <= pos[0] < width and 0 <= pos[1] < height:
                    pixel_color_index = img.getpixel(pos)
                    pixel_color = color_map[pixel_color_index]
                else:
                    pixel_color = (256, 256, 256)
                posdict[pos] = pixel_color
            rev += 1

        return posdict

    def create_groups(self, posdictt, p, pd, px_siz, color):
        tolerance = float(self.tolerance.currentText()) / px_siz
        color_group_dict = {}
        x_pen_dis, y_pen_dis = map(float, pd)
        x_error = (x_pen_dis / px_siz) % 1
        y_error = (y_pen_dis / px_siz) % 1
        x_del = int(x_pen_dis / px_siz) if x_error > tolerance or x_error < -tolerance else (x_pen_dis / px_siz)
        y_del = int(y_pen_dis / px_siz) if x_error > tolerance or x_error < -tolerance else (x_pen_dis / px_siz)
        if color == "RGB":
            for pos, colr in posdictt.items():
                colorlis = [1 if colr == tuple(p[3]) else 0,
                            1 if posdictt.get((pos[0] - x_del, pos[1])) == tuple(p[0]) else 0,
                            1 if posdictt.get((pos[0] - x_del, pos[1] - y_del)) == tuple(p[2]) else 0,
                            1 if posdictt.get((pos[0],  pos[1] - y_del)) == tuple(p[1]) else 0
                            ]
                if colorlis != [0, 0, 0, 0]:
                    color_group_dict[pos] = colorlis

                if y_error > tolerance or y_error < -tolerance and x_error <= tolerance and x_error >= -tolerance:
                    pos = (pos[0], pos[1] + y_error)
                    colorlis = [0, 0, 1 if posdictt.get((pos[0] - x_del, pos[1] - (y_pen_dis / px_siz))) == tuple(p[2]) else 0, 1 if posdictt.get((pos[0], pos[1] - (y_pen_dis / px_siz))) == tuple(p[1]) else 0]
                    if colorlis != [0, 0, 0, 0]:
                        color_group_dict[pos] = colorlis

                if x_error > tolerance or x_error < -tolerance and y_error <= tolerance and y_error >= -tolerance:
                    pos = (pos[0] + x_error, pos[1])
                    colorlis = [0, 1 if posdictt.get((pos[0] - (x_pen_dis / px_siz), pos[1])) == tuple(p[0]) else 0, 1 if posdictt.get((pos[0] - x_del, pos[1] - (y_pen_dis / px_siz))) == tuple(p[2]) else 0, 0]
                    if colorlis != [0, 0, 0, 0]:
                        color_group_dict[pos] = colorlis

                if (x_error > tolerance or x_error < -tolerance) and (y_error > tolerance or y_error < -tolerance):
                    pos = (pos[0] + x_error, pos[1])
                    colorlis = [0, 0, 0, 0]
                    if colorlis != [0, 0, 0, 0]:
                        color_group_dict[pos] = colorlis

            return color_group_dict
        elif color == "BW":
            for pos, colr in posdictt.items():
                if colr == tuple(p[0]):
                    colorlis = [1]
                    color_group_dict[pos] = colorlis

            return color_group_dict
        else:
            color_group_lis = []
            remainder = len(p) % 4
            amount = len(p) // 4
            for x in range(amount):
                color_group_dict = {}
                for pos, colr in posdictt.items():
                    colorlis = [1 if colr == tuple(p[0]) else 0,
                                1 if posdictt.get((pos[0] - x_del, pos[1])) == tuple(p[1]) else 0,
                                1 if posdictt.get((pos[0] - x_del, pos[1] - y_del)) == tuple(p[2]) else 0,
                                1 if posdictt.get((pos[0], pos[1] - y_del)) == tuple(p[3]) else 0
                                ]
                    if colorlis != [0, 0, 0, 0]:
                        color_group_dict[pos] = colorlis
                p = p[4:]
                color_group_lis.append(color_group_dict)
            color_group_dict = {}
            if remainder != 0:
                for pos, colr in posdictt.items():
                    prot1 = (1 if colr == tuple(p[0]) else 0) if remainder >= 1 else 0
                    prot2 = (1 if posdictt.get((pos[0] - x_del, pos[1])) == tuple(p[1]) else 0) if remainder >= 2 else 0
                    prot3 = (1 if posdictt.get((pos[0] - x_del, pos[1] - y_del)) == tuple(
                        p[2]) else 0) if remainder >= 3 else 0
                    prot4 = 0
                    colorlis = [prot1, prot2, prot3, prot4]
                    if colorlis != [0, 0, 0, 0]:
                        color_group_dict[pos] = colorlis
                color_group_lis.append(color_group_dict)
            return color_group_lis

    def grbl_gen(self, color_pos, px, por, ps, s, pwh, color, adv_pos, solenoid_time):
        pw, ph = pwh
        w, h = ps
        x_step_mm = 99.3
        y_Step_mm = 53.0
        gcode = f"G21\nG90\nM92 X{x_step_mm} Y{y_Step_mm}\nM500\nM74 T{solenoid_time}\nG28 X Y\nG92 X0 Y0\nG0 F{s * 60}\nG1 F{s * 60}\nM74 R1\nG0 X0 Y0\n"
        if adv_pos == False:
            if color == "RGB":
                for pos, form in color_pos.items():
                    x, y = pos
                    if por:
                        movh = (ph - h * px) / 2
                        movw = (pw - w * px) / 2
                        gcode += f"G0 X{(px * x) + movw} Y{(px * y) + movh}\nM74 A{form[0]} B{form[1]} C{form[2]} D{form[3]}\n"
                    else:
                        movh = (ph - w * px) / 2
                        movw = (pw - h * px) / 2
                        gcode += f"G0 X{(px * x) + movw} Y{(px * y) + movh}\nM74 A{form[0]} B{form[1]} C{form[2]} D{form[3]}\n"

                gcode = add_gcode(gcode, pw, self.cpec_checkbox.isChecked())
                return gcode
            elif color == "BW":
                for pos, form in color_pos.items():
                    x, y = pos
                    if por:
                        movh = (ph - h * px) / 2
                        movw = (pw - w * px) / 2
                        gcode += f"G0 X{(px * x) + movw} Y{(px * y) + movh}\nM74 A1 B0 C0 D0\n"
                    else:
                        movh = (ph - w * px) / 2
                        movw = (pw - h * px) / 2
                        gcode += f"G0 X{(px * x) + movw} Y{(px * y) + movh}\nM74 A1 B0 C0 D0\n"

                gcode = add_gcode(gcode, pw, self.cpec_checkbox.isChecked())
                return gcode
            else:
                rand = 0
                for dict in color_pos:
                    for pos, form in dict.items():
                        x, y = pos
                        if por:
                            movh = (ph - h * px) / 2
                            movw = (pw - w * px) / 2
                            gcode += f"G0 X{(px * x) + movw} Y{(px * y) + movh}\nM74 A{form[0]} B{form[1]} C{form[2]} D{form[3]}\n"
                        else:
                            movh = (ph - w * px) / 2
                            movw = (pw - h * px) / 2
                            gcode += f"G0 X{(px * x) + movw} Y{(px * y) + movh}\nM74 A{form[0]} B{form[1]} C{form[2]} D{form[3]}\n"

                    gcode += f"G0 X0 Y0\n"
                    rand += 1
                    if rand < len(color_pos):
                        gcode += f"M0 Change Pens\n"
                gcode = add_gcode(gcode, pw, self.cpec_checkbox.isChecked())
                return gcode

        else:
            x_pos = adv_pos[0]
            y_pos = adv_pos[1]
            if color == "RGB":
                for pos, form in color_pos.items():
                    x, y = pos
                    gcode += f"G0 X{(px * x) + x_pos} Y{(px * y) + y_pos}\nM74 A{form[0]} B{form[1]} C{form[2]} D{form[3]}\n"
                gcode = add_gcode(gcode, pw, self.cpec_checkbox.isChecked())
                return gcode
            elif color == "BW":
                for pos, form in color_pos.items():
                    x, y = pos
                    gcode += f"G0 X{(px * x) + x_pos} Y{(px * y) + y_pos}\nM74 A1 B0 C0 D0\n"
                gcode = add_gcode(gcode, pw, self.cpec_checkbox.isChecked())
                return gcode
            else:
                rand = 0
                for dict in color_pos:
                    for pos, form in dict.items():
                        x, y = pos
                        gcode += f"G0 X{(px * x) + x_pos} Y{(px * y) + y_pos}\nM74 A{form[0]} B{form[1]} C{form[2]} D{form[3]}\n"
                    gcode += f"G0 X0 Y0\n"
                    rand += 1
                    if rand < len(color_pos):
                        gcode += f"M0 Change Pens\n"
                gcode = add_gcode(gcode, pw, self.cpec_checkbox.isChecked())
                return gcode

    def reset(self):
        if self.good:
            self.slicer_button.setEnabled(True)
        self.save_button.setEnabled(False)
        self.save_gcode.setEnabled(False)
        self.save_settings.setEnabled(True)
        self.load_settings_button.setEnabled(True)

    def top_reset(self):
        if self.good:
            self.slicer_button.setEnabled(True)
        self.save_button.setEnabled(False)
        self.save_gcode.setEnabled(False)

    def search_reset(self):
        if self.search_text.text() != self.last_search or self.last_search_toggle != self.search_toggle.isChecked():
            self.search_button.setEnabled(True)

    def margin_off(self):
        on = self.advanced_pos_checkbox.isChecked() == False
        self.margin.setEnabled(on)

    def tolerance_off(self):
        on = self.accuracy_checkbox.isChecked() == True
        self.tolerance.setEnabled(on)

    def gen_img(self, description):
        client = openai.OpenAI(api_key=self.ai_key)
        response = client.images.generate(
            model="dall-e-2",
            prompt=description,
            size="1024x1024",
            quality="standard",
            n=4
        )
        image_urls = [response.data[0].url, response.data[1].url, response.data[2].url, response.data[3].url]

        return image_urls

    def search(self):
        self.last_search = self.search_text.text()
        self.last_search_toggle = self.search_toggle.isChecked()
        self.first_search = False
        source = self.search_toggle.isChecked()
        search_term = self.search_text.text()
        striped_search = search_term.strip()
        num_of_images = 4
        if striped_search != "":
            if source:
                images = []
                url = f"https://www.googleapis.com/customsearch/v1?key=AIzaSyBedsbiqQW7A1VV22fA1pdfRMyww12FINI&cx=06bc1f24783d245b9&q={search_term}&rigts=(cc_publicdomain%7Ccc_attribute%7Ccc_sharealike%7Ccc_noncommercial).-(cc_nonderived)&searchType=image&num={num_of_images}&filter=1"

                response = requests.get(url)
                data = response.json()

                if 'items' in data:
                    for item in data['items']:
                        if 'link' in item:
                            image_url = item['link']
                            images.append(image_url)
                if striped_search == "corgi":
                    images[0] = self.egg_url
                if len(images) == 4:
                    pick_image = self.select_image(images)
                    if pick_image[1]:
                        picked_image = pick_image[0]
                        self.download_image(picked_image, 'data/tobesliced.png')
                        self.open_image(True)
                        if picked_image == self.egg_url:
                            dialog = EasterEgg()
                            if dialog.exec_() == QDialog.Accepted:
                                self.current_score = 0
                                self.blackjack()
                                if self.current_score > self.max_score:
                                    self.max_score = self.current_score
                                    self.save_score()

            else:
                if self.ai_key == 'None':
                    continued = True
                    while continued:
                        dialog = APIKeyDialog(self)
                        correct = dialog.exec_()
                        if correct == QDialog.Accepted:
                            continued = False
                            self.ai_key = dialog.api_key
                            self.save_setting()
                            images = self.gen_img(search_term)
                            pick_image = self.select_image(images)
                            if pick_image[1]:
                                picked_image = pick_image[0]
                                self.download_image(picked_image, 'data/tobesliced.png')
                                self.open_image(True)
                        elif correct == QDialog.Rejected:
                            if not dialog.cancels:
                                self.ai_key = 'None'
                                self.save_setting(True)
                            else:
                                continued = False

                else:
                    images = self.gen_img(search_term)
                    pick_image = self.select_image(images)
                    if pick_image[1]:
                        picked_image = pick_image[0]
                        self.download_image(picked_image, 'data/tobesliced.png')
                        self.open_image(True)

    def select_image(self, urls):
        dialog = ImagePickerDialog(urls)
        result = dialog.exec_() == QDialog.Accepted
        if result:
            selected_image_url = dialog.selected_image_url
            return selected_image_url, result
        else:
            selected_image_url = None
            self.search_button.setEnabled(True)
            return selected_image_url, result

    def download_image(self, url, save_path):
        response = requests.get(url)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)

    def change_button(self):
        self.search_button.setText("Search" if self.search_toggle.isChecked() else "Generate")
        self.search_reset()

    def keyPressEvent(self, event):
        if event.key() == 16777220:
            if self.first_search:
                self.search()
            else:
                if self.search_text.text() != self.last_search or self.last_search_toggle != self.search_toggle.isChecked():
                    self.search()
                else:
                    if self.good:
                        self.slice()
        super().keyPressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = ImageSlicer()
    editor.show()
    sys.exit(app.exec_())
