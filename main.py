import sys
from PyQt5 import QtWidgets
from pyqt_core import MainWindow

app = QtWidgets.QApplication(sys.argv)
mainWin = MainWindow()
mainWin.resize(1100, 800)
mainWin.show()
sys.exit(app.exec_())
