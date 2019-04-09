from data.ucommons import breathe as b
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from enum import Enum as enum

def dark(bg:tuple=(61, 61, 61)):
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(*bg))
    palette.setColor(QPalette.Base, QColor(50, 50, 50))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
    palette.setColor(QPalette.Text, QColor(247, 247, 247))
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.white)
    palette.setColor(QPalette.Highlight, QColor(0, 168, 207))
    palette.setColor(QPalette.HighlightedText, QColor(247, 247, 247))
    palette.setColor(QPalette.WindowText, QColor(247, 247, 247))
    return palette

class UPushButton(QPushButton):
	def __init__(self, *props, color:tuple=None, flat:bool=False, tl:bool=True, tr:bool=True, br:bool=True, bl:bool=True):
		super().__init__(*props)
		if color is not None:
			norml = ""
			press = ""
			hover = ""
			for i in color:
				norml += b.strip_start(str(hex(i)), 2)
				if i < 16: norml += "0"
				if i > 16: press += b.strip_start(str(hex(i - 16)), 2)
				else: press += "00"
				if i < 239: hover += b.strip_start(str(hex(i + 16)), 2)
				else: hover += "ff"
		elif flat: norml = "3d3d3d"; press = "2d2d2d"; hover = "4d4d4d"
		else: norml = "4d4d4d"; press = "3d3d3d"; hover = "5d5d5d"
		tl = "3" if tl else "0"
		tr = "3" if tr else "0"
		br = "3" if br else "0"
		bl = "3" if bl else "0"
		self.setStyleSheet("""
	QPushButton {
		background-color: #%s;
		color: #f7f7f7;
		border: none;
		border-top-right-radius: %spx;
		border-top-left-radius: %spx;
		border-bottom-right-radius: %spx;
		border-bottom-left-radius: %spx;
		min-width: 72px;
		height: 32px;
	}
	QPushButton:pressed {
		background-color: #%s;
	}
	QPushButton:hover:!pressed {
		background-color: #%s;
	}""" % (norml, tr, tl, br, bl, press, hover))

class UTabWidget(QTabWidget):
	def __init__(self, *props, bgcolor:str="3d3d3d", color:str="4d4d4d", padding:int=48):
		super().__init__(*props)
		self.setStyleSheet("""QTabWidget {background-color: #%s; border: none;}
QTabWidget::pane {color: #f7f7f7; border: none; background-color: #%s;}
QTabBar::tab {color: #f7f7f7; background-color: #4d4d4d; border-top: 2px solid #4d4d4d; padding: 2px %spx 2px %spx;}
QTabBar::tab:selected {background-color: #4d4d4d; border-top: 2px solid #%s;}""" % (bgcolor, bgcolor, padding, padding, color))

class UGroupBox(QGroupBox):
	def __init__(self, *props):
		super().__init__(*props)
		self.setStyleSheet("color: #f7f7f7; border: none; border: 1px solid #4d4d4d; border-radius: 3px; padding: 16px 2px 2px 2px;")
		
class UFontComboBox(QFontComboBox):
	def __init__(self, *props):
		super().__init__(*props)
		self.setStyleSheet("color: #f7f7f7; border: none; background-color: #4d4d4d; border-radius: 3px; padding: 2px;")
