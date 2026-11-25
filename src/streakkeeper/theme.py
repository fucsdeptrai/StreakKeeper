STYLESHEET = """
QWidget { color: #dfe2eb; font-family: "Helvetica Neue"; font-size: 13px; }
QMainWindow, QWidget#workspace, QStackedWidget { background: #10141a; }
QFrame#sidebar { background: #181c22; border-right: 1px solid #262a31; }
QFrame#rail { background: #181c22; border-bottom: 1px solid #262a31; }
QFrame#panel { background: #181c22; border: 1px solid #262a31; border-radius: 8px; }
QFrame#notice { background: #29231f; border: 1px solid #4b382d; border-left: 3px solid #ff985e; border-radius: 6px; }
QFrame#hero {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #181c22, stop:0.62 #181c22, stop:1 #33241f);
    border: 1px solid #362923; border-radius: 8px;
}
QLabel#brand { font-size: 15px; font-weight: 700; }
QLabel#section { color: #ffb59d; font-size: 11px; font-weight: 700; }
QLabel#title { font-size: 28px; font-weight: 700; }
QLabel#heading { font-size: 16px; font-weight: 700; }
QLabel#muted { color: #a8aebc; }
QLabel#noteText { color: #eaded5; font-size: 13px; }
QLabel#noteTitle { color: #ffc09e; font-size: 13px; font-weight: 700; }
QLabel#metric { font-size: 24px; font-weight: 700; }
QLabel#status { color: #67df70; font-weight: 600; }
QLabel#status[paused="true"] { color: #ffb689; }
QLabel#badge { background: #262a31; color: #ffb59d; border-radius: 4px; padding: 4px 8px; font-size: 11px; }
QPushButton, QLineEdit, QComboBox, QTimeEdit {
    background: #262a31; border: 1px solid #363a43; border-radius: 5px; padding: 7px 10px;
}
QPushButton { font-weight: 600; }
QPushButton:hover, QComboBox:hover { background: #31353c; }
QPushButton:focus, QLineEdit:focus, QComboBox:focus, QTimeEdit:focus { border-color: #ff6b35; }
QTimeEdit:disabled { color: #818895; }
QPushButton:disabled { color: #818895; background: #21252c; }
QPushButton[primary="true"] { color: #21120b; background: #ff6b35; border-color: #ff6b35; }
QPushButton[primary="true"]:hover { background: #ff865c; }
QPushButton[primary="true"]:disabled { background: #533529; color: #c6a599; border-color: #634033; }
QPushButton[nav="true"] { background: transparent; border-color: transparent; color: #d3c2be; text-align: left; padding: 8px 10px; }
QPushButton[nav="true"]:hover { background: #262a31; }
QPushButton[nav="true"]:checked { background: #ff6b35; color: #24150d; }
QPushButton[nav="true"]:focus { border-color: #ffb59d; }
QLineEdit { background: #10141a; selection-background-color: #a54426; }
QComboBox QAbstractItemView { background: #262a31; selection-background-color: #593326; }
QTableWidget {
    background: #181c22; alternate-background-color: #1c2026;
    border: 1px solid #262a31; border-radius: 6px;
    selection-background-color: #3b2b26; selection-color: #f0e0da;
}
QTableWidget::item { border-bottom: 1px solid #262a31; padding: 0 9px; }
QHeaderView::section { background: #22262d; color: #e1bfb5; padding: 8px 10px; border: 0; font-weight: 600; }
QProgressBar { background: #10141a; border: 1px solid #262a31; border-radius: 4px; max-height: 8px; }
QProgressBar::chunk { background: #67df70; border-radius: 3px; }
QMenu { background: #181c22; border: 1px solid #363a43; }
QMenu::item:selected { background: #3b2b26; }
"""
