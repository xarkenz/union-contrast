#!/usr/bin/env python3

##################################
### UNION CONTRAST VERSION 0.1 ###
##################################
###### CODED BY SEAN CLARKE ######
##################################

# app color: (106, 168, 79) or #6aa84f

# Importing some modules (data.ucommons is local)
import sys, os, math
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from data.ucommons import breathe as br
from data.ucommons.pyqt import *
from enum import Enum as enum
from typing import *
from PIL import Image

# Some definitions
settings = QSettings("Union", "contrast")
PATH = os.path.dirname(os.path.abspath(__file__)) + "/"
main = None
zmax = 50
zmin = 1
tool = None

# Simple internal setting getter
def getSetting(name, defaultsto, rtype:type=str):
    try: ret = rtype(settings.value(name))
    except: ret = defaultsto
    return ret

# Simple internal setting saver
def saveSetting(name, value):
    if type(value) == bool or value is None:
        value = str(value).lower()
    settings.setValue(name, str(value))

# Retrieving internal settings
current = getSetting("current", "none")
if current == "none": current = None
defaultsize = QSize(getSetting("defaultsize-x", 16, int), getSetting("defaultsize-y", 16, int))
fontfamily = getSetting("fontfamily", "Arial")
gridenabled = getSetting("gridenabled", "false") == "true"
gridspacing = getSetting("gridspacing", 8, int)
iconsize = getSetting("iconsize", 16, int)
monofont = getSetting("monofont", "Monospace")
opendir = getSetting("opendir", "~")
zoomlevel = getSetting("zoomlevel", 1, float)

# Basic pixel class so the pixmaps aren't extremely cluttered
class pixel:
    def __init__(self, r:Union[int,tuple], g:int=None, b:int=None, a:int=None):
        if type(r) == tuple:
            self.r = r[0]
            self.g = r[1]
            self.b = r[2]
            self.a = r[3]
        else:
            self.r = r
            self.g = g
            self.b = b
            self.a = a
    def __tuple__(self):
        return (self.r, self.g, self.b, self.a)

# Basic image class to store some info
class image:
    def __init__(self, pixmap:List[list], path):
        self.h = len(pixmap)
        self.w = len(pixmap[0])
        self.pixmap = pixmap
        self.path = path
        self.name = path.split("/")[-1]

# Load an image to memory
def LoadImage(filename: str, form: str="png"):
    pixmap = []
    try:
        img = Image.open(filename)
        pix = img.load()
        for j in range(img.size[1]):
            pixmap.append([])
            for i in range(img.size[0]):
                pixmap[j].append(pixel(pix[i,j]))
        return image(pixmap, filename)
    except Exception as e:
        print("Failed to load image (line %s, %s)" % (sys.exc_info()[2].tb_lineno, e))
        return None

# Icon getter
def GetIcon(name: str): return PATH + "data/icons/" + name + (".png" if os.path.isfile(PATH+"data/icons/"+name+".png") else ".svg")

# Simple ways of knowing what mode the file is in
def inDraw(): return main.tabs.currentWidget() == main.drawCont
def inEdit(): return main.tabs.currentWidget() == main.textEdit

# Saves the internal settings
def SaveSettings():
    sv = saveSetting
    sv("current", current)
    sv("defaultsize-x", defaultsize.width())
    sv("defaultsize-y", defaultsize.height())
    sv("gridenabled", gridenabled)
    sv("gridspacing", gridspacing)
    sv("fontfamily", fontfamily)
    sv("iconsize", iconsize)
    sv("monofont", monofont)
    sv("opendir", opendir)
    sv("zoomlevel", zoomlevel)

class TKButton(QToolButton): # Basic class for a button in the toolkit (hence the 'tk')
    def __init__(self, act: QAction, *args):
        QPushButton.__init__(self, *args)
        self.setStyleSheet("""
QToolButton {background-color: #3d3d3d; border: none; border-radius: 3px; color: #f7f7f7; padding: 4px; font-family: %s;}
QToolButton:pressed {background-color: #2d2d2d;}
QToolButton:hover:!pressed:!checked {background-color: #4d4d4d;}
QToolButton:checked {background-color: #2d2d2d;}
}""" % fontfamily)
        self.setCheckable(True)
        eff = QGraphicsDropShadowEffect()
        eff.setColor(QColor.fromRgb(0,0,0,100))
        eff.setBlurRadius(5)
        eff.setOffset(0, 2)
        #self.setGraphicsEffect(eff)
        if act.icon().isNull(): self.setText(act.text())
        self.setIcon(act.icon())
        #self.toggled.connect(self.setTool)

class ToolButton(QToolButton): # Basic class for customized QToolButton
    def __init__(self, act: QAction):
        super().__init__()
        self.triggered.connect(act.trigger)
        self.setDefaultAction(act)

class Tools:
    class Pen(enum): name="pen"; text="Pen"

class PercentInput(QLineEdit): # Zoom input on toolbar
    def __init__(self, value:float=None, pmin:float=1.0, pmax:float=1000.0):
        QLineEdit.__init__(self)
        if value is not None: self.setText(str(value))
        self.pmin = pmin; self.pmax = pmax
        self.textChanged.connect(self.percentify)
        self.editingFinished.connect(self.finished)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""QLineEdit {color: #f7f7f7; background-color: #3d3d3d; border: none; border-radius: 3px; min-height: 24px; max-width: 48px; font-family: %s;}
QLineEdit:disabled {background-color: #4d4d4d; color: #c7c7c7;}""" % fontfamily)
    @pyqtSlot(str)
    def percentify(self, text): # Filter text input (see breathe for more)
        self.setText(br.rmNonNumerics(text))
    @pyqtSlot()
    def finished(self): # Handler event to update zooming
        if float(self.text()) > self.pmax: self.setText(str(self.pmax))
        elif float(self.text()) < self.pmin: self.setText(str(self.pmin))
        main.Zoom = float(self.text()) / 100
        main.update()
    def mousePressEvent(self, event): # Customized so the text selects all when clicked
        self.selectAll()
        event.accept()
    def update(self): # Custom update event
        val = main.Zoom * 100
        if type(val) == float:
            if val.is_integer(): val = int(val)
        self.setText(str(val))

class LineNumberArea(QWidget): # Widget intended to contain the line numbers for EditorWidget
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)
    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)

class EditorWidget(QPlainTextEdit): # Text editor
    def __init__(self, *args):
        super().__init__(*args)
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)
        self.setStyleSheet("color: #f7f7f7; font-family: Roboto Mono; background-color: #2d2d2d; border-radius: 3px; margin: 10px; padding: 3px;")
        self.highlightCurrentLine()
    def lineNumberAreaWidth(self): # Gets the line number width based on number of digits
        digits = 1
        count = max(1, self.blockCount())
        while count >= 10:
            count /= 10
            digits += 1
        space = 3 + self.fontMetrics().width('9') * digits
        return space
    def updateLineNumberAreaWidth(self, _): # Updates width of the line numbers
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)
    def updateLineNumberArea(self, rect, dy): # Updates area of the line numbers
        if dy: self.lineNumberArea.scroll(0, dy)
        else: self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()): self.updateLineNumberAreaWidth(0)
    def resizeEvent(self, event): # Handles resizing of the QTextEdit
        super().resizeEvent(event)
        self.lineNumberArea.setGeometry(QRect(self.contentsRect().left(), self.contentsRect().top(), self.lineNumberAreaWidth(), self.contentsRect().height()))
    def lineNumberAreaPaintEvent(self, event): # Event handler for painting the line number
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QBrush(QColor.fromRgb(61,61,61)))
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        height = self.fontMetrics().height()
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = str(blockNumber + 1)
                painter.setPen(QColor.fromRgb(200, 200, 200))
                painter.drawText(0, top, self.lineNumberArea.width(), height, Qt.AlignCenter, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1
    def highlightCurrentLine(self): # Add a highlight effect to the current line
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor.fromRgb(61,61,61)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

class PixScene(QGraphicsScene): # The background of the drawing canvas (given to PixViewWidget)
    def __init__(self, *args):
        self.bgbrush = QBrush(QColor.fromRgb(0,0,0))
        QGraphicsScene.__init__(self, *args)
    def drawBackground(self, painter, rect):
        painter.fillRect(rect, self.bgbrush)
        drawrect = QRectF(rect.x(), rect.y(), rect.width() + 1, rect.height() + 1)
        #print 'painting ' + repr(drawrect)
        isect = drawrect.intersects

class PixViewWidget(QGraphicsView): # The canvas for drawing
    hMouseDrag = pyqtSignal(int, int)
    def __init__(self, scene, parent):
        QGraphicsView.__init__(self, scene, parent)
        self.zoom = main.Zoom
        self.dragging = False
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setBackgroundBrush(QBrush(QColor.fromRgb(45,45,45)))
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setMouseTracking(True)
        self.YScrollBar = QScrollBar(Qt.Vertical, parent)
        self.XScrollBar = QScrollBar(Qt.Horizontal, parent)
        self.setVerticalScrollBar(self.YScrollBar)
        self.setHorizontalScrollBar(self.XScrollBar)
        self.currentobj = None
    def mousePressEvent(self, event): # starts dragging
        self.dragging = True
        event.accept()
    def mouseMoveEvent(self, event): # keeps dragging
        pos = main.view.mapToScene(event.x(), event.y())
        if self.dragging: self.hMouseDrag.emit(int(pos.x()), int(pos.y()))
        event.accept()
        QGraphicsView.mouseMoveEvent(self, event)
    def mouseReleaseEvent(self, event): # stops dragging
        self.dragging = False
        event.accept()
    def drawForeground(self, painter, vrect): # Draw the actual image to edit
        Zoom = self.zoom
        drawLine = painter.drawLine
        drawRect = painter.drawRect
        fillPath = painter.fillPath
        fillRect = painter.fillRect
        if main.loadedImage is not None: img, width, height = main.loadedImage, main.loadedImage.w, main.loadedImage.h
        else: img, width, height = None, defaultsize.width(), defaultsize.height()
        rect = QRect((vrect.width()-width*Zoom)//2, (vrect.height()-height*Zoom)//2, defaultsize.width()*Zoom, defaultsize.height()*Zoom)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Rounded border (below alpha layer)
        border = QPainterPath()
        border.addRoundedRect(rect.x() - 3, rect.y() - 3, rect.width() + 6, rect.height() + 6, 2, 2)
        fillPath(border, QBrush(QColor.fromRgb(106, 168, 79)))
        
        # Alpha background (below image layer)
        painter.setRenderHint(QPainter.Antialiasing, False)
        startx = rect.x()
        endx = startx + rect.width()
        starty = rect.y()
        endy = starty + rect.height()
        x = startx
        y = starty
        yalt = 0
        while y < endy:
            xalt = yalt % 2
            while x < endx:
                if xalt % 2 == 0: brush = QBrush(QColor.fromRgb(93, 93, 93))
                else: brush = QBrush(QColor.fromRgb(150, 150, 150))
                if x + 8 > endx: w = endx - x
                else: w = 8
                if y + 8 > endy: h = endy - y
                else: h = 8
                fillRect(x, y, w, h, brush)
                x += 8
                xalt += 1
            x = startx
            y += 8
            yalt += 1
        
        # Image (below grid layer)
        if img is not None:
            pix = img.pixmap
            for i in range(img.h):
                for j in range(len(pix[0])):
                    cpix = pix[i][j]
                    fillRect(rect.x()+(j*Zoom), rect.y()+(i*Zoom), Zoom+1, Zoom+1, QBrush(QColor.fromRgb(cpix.r, cpix.g, cpix.b, cpix.a)))
        
        # Grid (top layer)
        if gridenabled:
            startx = rect.x()
            endx = startx + rect.width()
            starty = rect.y()
            endy = starty + rect.height()
            painter.setPen(QPen(QColor.fromRgb(0,0,0), 1, Qt.SolidLine))
            x = startx + gridspacing * Zoom
            while x < endx:
                drawLine(x, starty, x, endy-1)
                x += gridspacing * Zoom
            y = starty + gridspacing * Zoom
            while y < endy:
                drawLine(startx, y, endx-1, y)
                y += gridspacing * Zoom

        # Handle zoom animation
        if round(self.zoom*10, 5)/10 == main.Zoom: self.zoom = main.Zoom
        elif Zoom != main.Zoom:
            self.zoom += (main.Zoom - self.zoom) / 7
            self.update()

class Preferences(QDialog): # Preferences dialog
    applied = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.resize(400, 600)
        self.setPalette(dark((45, 45, 45)))
        
        self.layout = QVBoxLayout()
        self.tabs = UTabWidget(color="6aa84f")
        self.generalTab = QWidget()
        self.generalLayout = QVBoxLayout()

        self.fontsBox = UGroupBox("Fonts")
        self.fontsLayout = QVBoxLayout()
        self.mainFontCombo = UFontComboBox()
        self.mainFontCombo.setCurrentFont(QFont(fontfamily))
        self.fontsLayout.addWidget(self.mainFontCombo)
        self.fontsLayout.addStretch()
        self.fontsBox.setLayout(self.fontsLayout)
        self.generalLayout.addWidget(self.fontsBox)
        self.generalTab.setLayout(self.generalLayout)
        self.tabs.addTab(self.generalTab, "General")
        
        self.buttonBox = QWidget()
        self.buttonBoxLayout = QHBoxLayout()
        self.cancel = UPushButton("Cancel", flat=True)
        self.ok = UPushButton("OK", flat=True)
        self.setdefault = UPushButton("Set default", flat=True)
        self.buttonBoxLayout.addWidget(self.cancel)
        self.buttonBoxLayout.addWidget(self.ok)
        self.buttonBoxLayout.addWidget(self.setdefault)
        self.buttonBox.setLayout(self.buttonBoxLayout)
        
        self.layout.addWidget(self.tabs)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

class ContrastWindow(QMainWindow): # Main window for Contrast (yay)
    def __init__(self):
        super().__init__()
        global PATH, main
        main = self
        
        self.actions = {}
        self.tkactions = {}
        self.Zoom = zoomlevel
        self.loadedImage = None
        self.isdirty = current is None

        self.tkCol = 5
        self.showMaximized()

        self.tabs = UTabWidget(color="6aa84f")
        self.drawCont = QWidget()
        self.drawLayout = QHBoxLayout()
        self.tkCont = QWidget()
        self.tkLayout = QGridLayout()
        self.textEdit = EditorWidget()
        
        self.scene = PixScene(0, 0, 16, 16, self)
        self.scene.setItemIndexMethod(QGraphicsScene.NoIndex)

        self.view = PixViewWidget(self.scene, self)
        self.view.centerOn(0,0) # this scrolls to the top left
        #self.view.XScrollBar.valueChanged.connect(self.XScrollChange)
        #self.view.YScrollBar.valueChanged.connect(self.YScrollChange)
        self.view.setStyleSheet("border: none;")
        self.drawLayout.setContentsMargins(0,0,0,0)

        self.tkCont.setLayout(self.tkLayout)
        self.drawLayout.addWidget(self.tkCont)
        self.drawLayout.addWidget(self.view)
        self.drawCont.setLayout(self.drawLayout)
        self.tabs.addTab(self.drawCont, "Draw")
        self.tabs.addTab(self.textEdit, "Edit")
        self.tabs.currentChanged.connect(self.update)
        self.setCentralWidget(self.tabs)

        self.CreateAction("new", self.hNew, "New", QKeySequence("Ctrl+N"))
        self.CreateAction("open", self.hOpen, "Open", QKeySequence("Ctrl+O"))
        self.CreateAction("save", self.hSave, "Save", QKeySequence("Ctrl+S"))
        self.CreateAction("saveas", self.hSaveAs, "Save As", QKeySequence("Ctrl+Shift+S"))
        self.CreateAction("zoomin", self.hZmIn, "Zoom In", QKeySequence("Ctrl++"))
        self.CreateAction("zoomout", self.hZmOut, "Zoom Out", QKeySequence("Ctrl+-"))
        self.CreateAction("zoomfull", self.hZmFull, "Zoom Full", QKeySequence("Ctrl+1"))
        self.CreateAction("pref", self.hPref, "Preferences")
        self.CreateTKAction(Tools.Pen)
        
        for i, action in zip(range(len(self.tkactions)), self.tkactions.keys()):
            self.tkLayout.addWidget(TKButton(self.tkactions[action]), math.ceil(i/self.tkCol), 5 if i%5 == 0 else i%5)
        #6AA650
        
        menubar = self.menuBar()
        menubar.setObjectName("menubar")
        menubar.setNativeMenuBar(False)
        menubar.setStyleSheet("""QMenuBar#menubar {background-color: #4d4d4d; color: #f7f7f7; border: none; font-family: %s;}
QMenuBar::item {color: #f7f7f7; border: none; border-radius: 3px; background-color: #4d4d4d; margin: 2px; height: 16px; width: 32px; padding: 2px;}
QMenuBar::item:selected {background-color: #5d5d5d;}
QMenuBar::item:pressed {background-color: #3d3d3d;}
QMenu {background-color: #4d4d4d; border: none; border-radius: 3px; color: #f7f7f7; padding: 2px 4px 2px 4px; font-family: %s;}
QMenu::item:selected {background-color: #5d5d5d;}
QMenu::item:pressed {background-color: #3d3d3d;}
QMenu::item:checked {background-color: #3d3d3d;}
QMenu::icon:checked {border: none;}""" % (fontfamily, fontfamily))

        fm = menubar.addMenu("File")
        fm.addAction(self.actions["new"])
        fm.addAction(self.actions["open"])
        fm.addAction(self.actions["save"])
        fm.addAction(self.actions["saveas"])
        em = menubar.addMenu("Edit")
        em.addAction(self.actions["pref"])
        vm = menubar.addMenu("View")
        vm.addAction(self.actions["zoomin"])
        vm.addAction(self.actions["zoomout"])
        vm.addAction(self.actions["zoomfull"])
        
        self.tb = self.addToolBar("Toolbar")
        self.tb.setObjectName("toolbar")
        self.tb.setMovable(False)
        self.zoombar = PercentInput(self.Zoom * 100, zmin * 100, zmax * 100)
        percent = QLabel("%")
        percent.setStyleSheet("color: #f7f7f7; font-family: %s;" % fontfamily)

        self.tb.addAction(self.actions["new"])
        self.tb.addAction(self.actions["open"])
        self.tb.addAction(self.actions["save"])
        self.tb.addAction(self.actions["saveas"])
        self.tb.addSeparator()
        self.tb.addAction(self.actions["zoomin"])
        self.tb.addAction(self.actions["zoomout"])
        self.tb.addWidget(self.zoombar)
        self.tb.addWidget(percent)
        self.tb.addAction(self.actions["zoomfull"])
        self.tb.addSeparator()

        self.tb.setStyleSheet("""QToolBar#toolbar {background-color: #4d4d4d; border: none; font-family: %s;}
QToolButton {color: #f7f7f7; background-color: #4d4d4d; border: none; border-radius: 3px; font-family: %s; min-width: %s; height: %s; padding: 4px;}
QToolButton:hover {background-color: #5d5d5d;}
QToolButton:pressed {background-color: #3d3d3d;}
QToolButton:disabled {color: #a7a7a7; background-color: #5d5d5d;}
QToolBar::separator {max-width: 2px; border-left: 1px solid #5d5d5d; max-height: 16px; margin: 2px;}
QToolTip {background-color: #4d4d4d; border: none; color: #f7f7f7; padding: 1px 2px 1px 2px; border-radius: 3px; font-family: %s;}
""" % (fontfamily, fontfamily, iconsize, iconsize, fontfamily))

        if current is not None: self.hOpen(openfile=current)
        self.update()
        self.show()

    def CreateAction(self, shortname, function, text, shortcut=None, toggle=False, onstate=None, statustext=None): # A little special action maker
        icon = QIcon(GetIcon(shortname))
        if onstate is not None:
            icon.addPixmap(QPixmap(GetIcon(onstate)), QIcon.Active, QIcon.On)
            icon.addPixmap(QPixmap(GetIcon(onstate)), QIcon.Normal, QIcon.On)
        icon.addPixmap(QPixmap(GetIcon(shortname)), QIcon.Disabled)
        action = QAction(icon, text, self)
        if shortcut is not None: action.setShortcut(shortcut)
        if statustext is not None: action.setStatusTip(statustext)
        if toggle: action.setCheckable(True)
        action.triggered.connect(function)
        self.actions[shortname] = action

    def CreateTKAction(self, tool: Tools): # A little special toolkit action maker
        icon = QIcon(GetIcon(tool.name.value))
        action = QAction(icon, tool.text.value, self)
        action.setCheckable(True)
        self.tkactions[tool.name.value] = action

    def hNew(self): # Handle creation of a new file
        pass
    def hOpen(self, *args, openfile=None): # Handle opening of existing file
        if openfile is None: fpath = QFileDialog.getOpenFileName(self, "Open File", opendir, "Image Files(*.usf *.union *.png);;All Files(*)")[0]
        else: fpath = openfile
        if fpath == "": return
        fname = fpath.split("/")[-1]
        fext = fname.split(".")[-1]
        try: open(fpath, "r")
        except FileNotFoundError: # This should not happen unless something is terribly wrong lol
            QMessageBox.warning(self, "Invalid file", "The file '%s' does not appear to exist." % fname, QMessageBox.Ok)
            return
        if fext in ["usf", "union"]:
            return
        else: # eh, let LoadImage handle it from here
            self.loadedImage = LoadImage(fpath, fext)
            self.update()
    def hSave(self): # Handle saving of current file
        return True
    def hSaveAs(self): # Handle saving to a different filename
        pass
    def hZmIn(self): # Handle zooming in
        if self.Zoom * 2 <= zmax: self.ZoomTo(self.Zoom * 2)
        elif self.Zoom < zmax: self.ZoomTo(zmax)
    def hZmOut(self): # Handle zooming out
        if self.Zoom / 2 >= zmin: self.ZoomTo(self.Zoom / 2)
        elif self.Zoom > zmin: self.ZoomTo(zmin)
    def hZmFull(self): # Handle zooming to 100%
        self.ZoomTo(1)
    def hPref(self): # Open the preferences dialog (Preferences)
        prefDialog = Preferences().exec_()
    def update(self): # Custom update function to keep things running smoothly
        SaveSettings()
        if self.loadedImage is None: current = None
        else: current = self.loadedImage.path
        self.actions['zoomin'].setEnabled(self.Zoom < zmax and inDraw())
        self.actions['zoomfull'].setEnabled(self.Zoom != 1 and inDraw())
        self.actions['zoomout'].setEnabled(self.Zoom > zmin and inDraw())
        self.zoombar.setEnabled(inDraw())
        self.setWindowTitle("%s%s - Contrast" % ("*" if self.isdirty else "", "untitled" if self.loadedImage is None else self.loadedImage.name))
        self.setWindowIcon(QIcon(GetIcon("ucicon")))
        self.setPalette(dark())
        self.setIconSize(QSize(iconsize, iconsize))
        self.zoombar.update()
        self.scene.update()
    @pyqtSlot(bool)
    def ZoomTo(self, z): # Zoom function
        self.Zoom = z
        self.update()
    def closeAccept(self, event):
        global current
        current = None
        self.update()
        event.accept()
    def closeEvent(self, event): # Called when the user attempts to close the window
        if current is not None:
            if not self.isdirty: self.closeAccept(event); return
            msg = QMessageBox()
            msg.setPalette(self.palette())
            msg.setText("There are unsaved changes in this file.")
            msg.setInformativeText("Do you want to save them?")
            msg.addButton(UPushButton("Discard", color=(233, 84, 32)), 2)
            msg.addButton(UPushButton("Save", color=(106, 168, 79)), 0)
            msg.addButton(UPushButton("Cancel"), 1)
            resp = msg.exec_()
            if resp == 1:
                if self.hSave: self.closeAccept(event)
                else: event.ignore()
            elif resp == 0: self.closeAccept(event)
            else: event.ignore()
        else: self.closeAccept(event)

class LoadingWindow(QDialog): # Startup window with progress bar
    def __init__(self, *args):
        super().__init__(*args)

if __name__ == "__main__": # Core functions for behind-the-scenes action
    try:
        app = QApplication(["UnionContrast"])
        ContrastWindow()
        sys.exit(app.exec_())
    except Exception as e:
        print("Encountered an error while running program (line %s, %s)" % (sys.exc_info()[2].tb_lineno, e))
        raise
        sys.exit(1)
