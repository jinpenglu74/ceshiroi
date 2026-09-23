from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget

CYAN = "#35E6FF"
BLUE = "#1687FF"
PURPLE = "#8B6CFF"
GREEN = "#35F3B4"
PINK = "#FF4C8B"
AMBER = "#FFD166"
TEXT = "#E9F6FF"
MUTED = "#83A9CE"
PANEL = "#061A3A"
CARD = "#08234A"


APP_QSS = """
* {
    color: #E9F6FF;
    font-family: "Microsoft YaHei UI";
    font-size: 14px;
}
QMainWindow {
    background: #020A18;
}
QWidget#root {
    background: transparent;
}
QFrame#topbar {
    background: rgba(5, 21, 50, 228);
    border: 1px solid #1768A7;
    border-radius: 14px;
}
QFrame#panel {
    background: rgba(5, 22, 49, 232);
    border: 1px solid #0D6FAF;
    border-radius: 14px;
}
QFrame#section {
    background: rgba(7, 31, 66, 238);
    border: 1px solid #114F85;
    border-radius: 10px;
}
QFrame#hero {
    background: qlineargradient(
        x1:0,y1:0,x2:1,y2:1,
        stop:0 rgba(7,43,88,245),
        stop:0.55 rgba(4,21,50,245),
        stop:1 rgba(5,38,77,245)
    );
    border: 1px solid #20D9FF;
    border-radius: 12px;
}
QFrame#metricCard {
    background: rgba(7, 31, 65, 244);
    border: 1px solid #135D97;
    border-radius: 10px;
}
QFrame#tipCard {
    background: rgba(54, 45, 20, 220);
    border: 1px solid #A88A2F;
    border-radius: 10px;
}
QLabel#title {
    color: white;
    font-size: 30px;
    font-weight: 900;
}
QLabel#subtitle {
    color: #8FB1D2;
    font-size: 13px;
}
QLabel#eyebrow {
    color: #36D9F2;
    font-size: 10px;
    font-weight: 700;
}
QLabel#sectionTitle {
    color: #F0FAFF;
    font-size: 18px;
    font-weight: 850;
}
QLabel#subSectionTitle {
    color: #EAF7FF;
    font-size: 16px;
    font-weight: 800;
}
QLabel#hint {
    color: #83A9CE;
    font-size: 12px;
}
QLabel#metric {
    color: #62E8FF;
    font-size: 60px;
    font-weight: 900;
}
QLabel#metricCaption {
    color: #C4DCF0;
    font-size: 13px;
}
QLabel#smallMetric {
    color: white;
    font-size: 23px;
    font-weight: 850;
}
QLabel#unit {
    color: #91B7DB;
    font-size: 13px;
}
QLabel#formula {
    color: #C5DAF0;
    font-size: 13px;
}
QLabel#tipTitle {
    color: #FFE17A;
    font-size: 15px;
    font-weight: 850;
}
QLineEdit {
    background: rgba(3, 17, 38, 245);
    color: #F4FBFF;
    border: 1px solid #1C5E97;
    border-radius: 7px;
    padding: 9px 12px;
    font-size: 15px;
}
QLineEdit:hover {
    border: 1px solid #2482C8;
}
QLineEdit:focus {
    border: 1px solid #35E6FF;
    background: rgba(5, 30, 62, 250);
}
QPushButton {
    min-height: 22px;
    color: #EAF8FF;
    background: rgba(8, 61, 111, 238);
    border: 1px solid #239BD4;
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 800;
}
QPushButton:hover {
    background: rgba(11, 90, 158, 245);
    border: 1px solid #5EEBFF;
}
QPushButton:pressed {
    background: #07345F;
}
QPushButton#primary {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0761E9,stop:1 #0B8FDF);
    border: 1px solid #56EFFF;
}
QPushButton#primary:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0B76FF,stop:1 #12B7DF);
}
QPushButton#ghost {
    background: rgba(5, 36, 69, 235);
}
QRadioButton {
    spacing: 8px;
    padding: 7px 4px;
    color: #E8F4FF;
    font-weight: 700;
}
QRadioButton::indicator {
    width: 17px;
    height: 17px;
}
QProgressBar {
    background: #071A33;
    border: 1px solid #174F7D;
    border-radius: 7px;
    height: 13px;
    text-align: center;
}
QProgressBar::chunk {
    border-radius: 6px;
    background: qlineargradient(
        x1:0,y1:0,x2:1,y2:0,
        stop:0 #FF356F,
        stop:0.50 #39BEFF,
        stop:1 #39F0B1
    );
}
"""


def add_glow(
    widget: QWidget,
    color: str = CYAN,
    blur: float = 22.0,
    alpha: int = 135,
) -> None:
    effect = QGraphicsDropShadowEffect(widget)
    glow = QColor(color)
    glow.setAlpha(alpha)
    effect.setColor(glow)
    effect.setBlurRadius(blur)
    effect.setOffset(0, 0)
    widget.setGraphicsEffect(effect)
