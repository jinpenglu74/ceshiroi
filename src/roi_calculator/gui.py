from __future__ import annotations

import json
import os
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QDoubleValidator,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .domain import RoiInputs, calculate
from .version import __version__


APP_QSS = """
* {
    color: #dcecff;
    font-family: "Microsoft YaHei UI";
    font-size: 14px;
}
QMainWindow, QWidget#root {
    background: #03132d;
}
QFrame#topbar {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #061d45,stop:0.48 #041736,stop:1 #061c41);
    border: 1px solid #0b65ad;
    border-radius: 14px;
}
QFrame#panel {
    background: #061e42;
    border: 1px solid #0876c7;
    border-radius: 14px;
}
QFrame#section {
    background: #07254d;
    border: 1px solid #0b5d9d;
    border-radius: 10px;
}
QFrame#hero {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #082b5d,stop:0.60 #061b3a,stop:1 #08264e);
    border: 1px solid #19c7ff;
    border-radius: 12px;
}
QFrame#metricCard {
    background: #082750;
    border: 1px solid #0b72bd;
    border-radius: 10px;
}
QFrame#tipCard {
    background: #26321f;
    border: 1px solid #dfbd42;
    border-radius: 10px;
}
QLabel#title {
    color: #ffffff;
    font-size: 30px;
    font-weight: 900;
}
QLabel#subtitle {
    color: #99b6d7;
    font-size: 13px;
}
QLabel#eyebrow {
    color: #2b8fcb;
    font-size: 10px;
    letter-spacing: 4px;
}
QLabel#sectionTitle {
    color: #edf8ff;
    font-size: 18px;
    font-weight: 800;
}
QLabel#subSectionTitle {
    color: #eaf6ff;
    font-size: 16px;
    font-weight: 800;
}
QLabel#hint {
    color: #91acd0;
    font-size: 12px;
}
QLabel#metric {
    color: #61dfff;
    font-size: 56px;
    font-weight: 900;
}
QLabel#metricCaption {
    color: #c8dcf1;
    font-size: 13px;
}
QLabel#smallMetric {
    color: #ffffff;
    font-size: 22px;
    font-weight: 850;
}
QLabel#unit {
    color: #a8c2df;
    font-size: 13px;
}
QLabel#formula {
    color: #c9ddf4;
    font-size: 13px;
}
QLabel#tipTitle {
    color: #ffdf73;
    font-size: 15px;
    font-weight: 800;
}
QLineEdit {
    background: #051a37;
    color: #f3f8ff;
    border: 1px solid #195f9d;
    border-radius: 7px;
    padding: 9px 12px;
    font-size: 15px;
}
QLineEdit:focus {
    border: 1px solid #2ed4ff;
    background: #062142;
}
QPushButton {
    min-height: 22px;
    color: #e9f6ff;
    background: #0a4d8c;
    border: 1px solid #25aee9;
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 800;
}
QPushButton:hover {
    background: #0d67b5;
    border: 1px solid #5ee9ff;
}
QPushButton:pressed {
    background: #073d71;
}
QPushButton#primary {
    background: #0761e9;
    border: 1px solid #56efff;
}
QPushButton#primary:hover {
    background: #0c79ff;
}
QPushButton#ghost {
    background: #082746;
}
QRadioButton {
    spacing: 8px;
    padding: 7px 4px;
    color: #e8f3ff;
    font-weight: 700;
}
QRadioButton::indicator {
    width: 17px;
    height: 17px;
}
QProgressBar {
    background: #09203e;
    border: 1px solid #174f7d;
    border-radius: 7px;
    height: 13px;
    text-align: center;
}
QProgressBar::chunk {
    border-radius: 6px;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #ff316c,stop:0.50 #43baff,stop:1 #43efad);
}
"""


def separator() -> QFrame:
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet("background:#164d78;border:none;")
    return line


class MoneyField(QWidget):
    def __init__(
        self,
        title: str,
        *,
        percent: bool = False,
        prefix: str = "¥",
    ) -> None:
        super().__init__()
        self.percent = percent

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("hint")

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(7)

        prefix_label = QLabel("%" if percent else prefix)
        prefix_label.setAlignment(Qt.AlignCenter)
        prefix_label.setFixedWidth(32)
        prefix_label.setStyleSheet(
            "background:#082850;border:1px solid #174f82;border-radius:7px;"
            "font-weight:800;color:#8fc9f2;padding:8px 0;"
        )

        self.edit = QLineEdit("0.00")
        maximum = 100.0 if percent else 999_999_999.0
        validator = QDoubleValidator(0.0, maximum, 2, self.edit)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.edit.setValidator(validator)
        self.edit.setAlignment(Qt.AlignRight)

        suffix = QLabel("%" if percent else "元")
        suffix.setObjectName("unit")
        suffix.setFixedWidth(28)

        row.addWidget(prefix_label)
        row.addWidget(self.edit, 1)
        row.addWidget(suffix)

        layout.addWidget(title_label)
        layout.addLayout(row)

    def value(self) -> float:
        try:
            return float(self.edit.text().strip() or "0")
        except ValueError:
            return 0.0

    def set_value(self, value: float) -> None:
        self.edit.setText(f"{value:.2f}")


class MetricCard(QFrame):
    def __init__(self, symbol: str, title: str, accent: str) -> None:
        super().__init__()
        self.setObjectName("metricCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(88)

        row = QHBoxLayout(self)
        row.setContentsMargins(14, 12, 14, 12)
        row.setSpacing(12)

        icon = QLabel(symbol)
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(52, 52)
        icon.setStyleSheet(
            f"background:#0a315e;border:1px solid {accent};border-radius:9px;"
            f"color:{accent};font-size:25px;font-weight:900;"
        )

        text = QVBoxLayout()
        text.setSpacing(4)
        title_label = QLabel(title)
        title_label.setObjectName("hint")
        self.value = QLabel("¥0.00")
        self.value.setObjectName("smallMetric")

        text.addWidget(title_label)
        text.addWidget(self.value)

        row.addWidget(icon)
        row.addLayout(text, 1)


class GrowthArt(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(220, 150)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        grid_pen = QPen(QColor(16, 91, 150, 80), 1)
        painter.setPen(grid_pen)
        for x in range(12, width, 34):
            painter.drawLine(x, 14, x, height - 14)
        for y in range(20, height, 28):
            painter.drawLine(8, y, width - 8, y)

        gradient = QLinearGradient(0, height, 0, 20)
        gradient.setColorAt(0.0, QColor("#0e6ed2"))
        gradient.setColorAt(1.0, QColor("#65f2ff"))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor("#2edcff"), 2))

        base = height - 30
        bar_width = 26
        gaps = 18
        heights = [42, 72, 108]
        start_x = width * 0.42
        for index, bar_height in enumerate(heights):
            x = int(start_x + index * (bar_width + gaps))
            painter.drawRoundedRect(
                x,
                base - bar_height,
                bar_width,
                bar_height,
                3,
                3,
            )

        path = QPainterPath()
        path.moveTo(width * 0.18, height * 0.70)
        path.cubicTo(
            width * 0.40,
            height * 0.68,
            width * 0.55,
            height * 0.36,
            width * 0.78,
            height * 0.24,
        )
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor("#6af3ff"), 8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(path)

        arrow = QPainterPath()
        arrow.moveTo(width * 0.74, height * 0.17)
        arrow.lineTo(width * 0.84, height * 0.20)
        arrow.lineTo(width * 0.80, height * 0.31)
        arrow.closeSubpath()
        painter.setBrush(QColor("#6af3ff"))
        painter.setPen(Qt.NoPen)
        painter.drawPath(arrow)


class ReturnOption(QFrame):
    def __init__(self, radio: QRadioButton, symbol: str, subtitle: str) -> None:
        super().__init__()
        self.radio = radio
        self.setObjectName("returnOption")
        self.setStyleSheet(
            "QFrame#returnOption{background:#08264d;border:1px solid #0b659f;"
            "border-radius:9px;}QFrame#returnOption:hover{border:1px solid #24caff;}"
        )
        row = QHBoxLayout(self)
        row.setContentsMargins(10, 7, 10, 7)
        row.setSpacing(10)

        icon = QLabel(symbol)
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(34, 34)
        icon.setStyleSheet("color:#34e4ff;font-size:22px;font-weight:900;")

        text = QVBoxLayout()
        text.setSpacing(1)
        text.addWidget(radio)
        sub = QLabel(subtitle)
        sub.setObjectName("hint")
        text.addWidget(sub)

        row.addWidget(icon)
        row.addLayout(text, 1)

    def set_selected(self, selected: bool) -> None:
        if selected:
            self.setStyleSheet(
                "QFrame#returnOption{background:#07325b;border:2px solid #1bd6ff;"
                "border-radius:9px;}QFrame#returnOption:hover{border:2px solid #63edff;}"
            )
        else:
            self.setStyleSheet(
                "QFrame#returnOption{background:#08264d;border:1px solid #0b659f;"
                "border-radius:9px;}QFrame#returnOption:hover{border:1px solid #24caff;}"
            )


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"ROI智能计算器  v{__version__}")
        self.resize(1560, 900)
        self.setMinimumSize(1200, 760)

        self._build_ui()
        self._load_settings()
        self._wire_events()
        self._sync_return_cards()
        self.recalculate()

    @property
    def settings_path(self) -> Path:
        root = Path(os.getenv("APPDATA", str(Path.home()))) / "ROI智能计算器"
        root.mkdir(parents=True, exist_ok=True)
        return root / "settings.json"

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)

        page = QVBoxLayout(root)
        page.setContentsMargins(24, 16, 24, 18)
        page.setSpacing(12)

        page.addWidget(self._build_topbar())

        body = QHBoxLayout()
        body.setSpacing(14)
        body.addWidget(self._build_left_panel(), 10)
        body.addWidget(self._build_right_panel(), 13)
        page.addLayout(body, 1)

        footer = QHBoxLayout()
        footer.setSpacing(12)

        info = QLabel("ⓘ  测算结果仅供决策参考，请结合真实经营数据动态校准。")
        info.setObjectName("hint")

        self.copy_button = QPushButton("▣  复制测算结果")
        self.copy_button.setObjectName("ghost")

        self.save_button = QPushButton("▣  保存并关闭")
        self.save_button.setObjectName("primary")

        footer.addWidget(info)
        footer.addStretch(1)
        footer.addWidget(self.copy_button)
        footer.addWidget(self.save_button)
        page.addLayout(footer)

    def _build_topbar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("topbar")
        frame.setMinimumHeight(92)

        row = QHBoxLayout(frame)
        row.setContentsMargins(18, 12, 18, 12)
        row.setSpacing(14)

        logo = QLabel("↗")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(58, 58)
        logo.setStyleSheet(
            "background:qlineargradient(x1:0,y1:1,x2:1,y2:0,stop:0 #196ce4,stop:1 #55f4ff);"
            "border:1px solid #42d7ff;border-radius:12px;color:white;"
            "font-size:34px;font-weight:900;"
        )

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        title = QLabel("ROI智能计算器")
        title.setObjectName("title")
        subtitle = QLabel("输入商品成本与投放参数，实时测算盈亏平衡与目标 ROI")
        subtitle.setObjectName("subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        slogan = QVBoxLayout()
        slogan.setSpacing(2)
        e = QLabel("数 据 驱 动 增 长 · 让 投 放 更 有 确 定 性")
        e.setObjectName("eyebrow")
        e.setAlignment(Qt.AlignRight)
        v = QLabel(f"正式版  v{__version__}")
        v.setObjectName("hint")
        v.setAlignment(Qt.AlignRight)
        slogan.addWidget(e)
        slogan.addWidget(v)

        self.reset_button = QPushButton("↻  重置数据")
        self.reset_button.setObjectName("ghost")

        row.addWidget(logo)
        row.addLayout(title_box)
        row.addStretch(1)
        row.addLayout(slogan)
        row.addWidget(self.reset_button)
        return frame

    def _build_left_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setMinimumWidth(470)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        head = QHBoxLayout()
        icon = QLabel("◆")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(44, 44)
        icon.setStyleSheet(
            "background:#0a75c3;border:1px solid #22dcff;border-radius:9px;"
            "font-size:20px;color:#6df1ff;"
        )
        text = QVBoxLayout()
        text.setSpacing(1)
        title = QLabel("经营参数")
        title.setObjectName("sectionTitle")
        desc = QLabel("精准输入经营数据，获取更准确的测算结果")
        desc.setObjectName("hint")
        text.addWidget(title)
        text.addWidget(desc)
        head.addWidget(icon)
        head.addLayout(text)
        head.addStretch()
        layout.addLayout(head)

        layout.addWidget(self._build_income_section())
        layout.addWidget(self._build_platform_section())
        layout.addWidget(self._build_return_section())
        layout.addStretch(1)
        return panel

    def _build_income_section(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("section")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        title = QLabel("🛒   1   商品收入与成本")
        title.setObjectName("subSectionTitle")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)

        self.sale_price = MoneyField("商品售价")
        self.product_cost = MoneyField("商品成本")
        self.shipping_cost = MoneyField("商品运费")
        self.shipping_insurance = MoneyField("运费险")

        grid.addWidget(self.sale_price, 0, 0)
        grid.addWidget(self.product_cost, 0, 1)
        grid.addWidget(self.shipping_cost, 1, 0)
        grid.addWidget(self.shipping_insurance, 1, 1)

        layout.addLayout(grid)
        return frame

    def _build_platform_section(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("section")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        title = QLabel("◔   2   平台与售后")
        title.setObjectName("subSectionTitle")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)

        self.platform_fee = MoneyField("平台扣点", percent=True)
        self.refund_rate = MoneyField("预计退款率", percent=True)

        grid.addWidget(self.platform_fee, 0, 0)
        grid.addWidget(self.refund_rate, 0, 1)

        layout.addLayout(grid)
        return frame

    def _build_return_section(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("section")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        title = QLabel("⟳   3   退货成本口径")
        title.setObjectName("subSectionTitle")
        layout.addWidget(title)

        self.resell_radio = QRadioButton("可再次销售")
        self.loss_radio = QRadioButton("成本全部损失")
        self.resell_radio.setChecked(True)

        self.return_group = QButtonGroup(self)
        self.return_group.setExclusive(True)
        self.return_group.addButton(self.resell_radio)
        self.return_group.addButton(self.loss_radio)

        self.resell_card = ReturnOption(
            self.resell_radio,
            "◇",
            "退货商品成本可回收",
        )
        self.loss_card = ReturnOption(
            self.loss_radio,
            "♜",
            "退货商品成本全部计入",
        )

        options = QHBoxLayout()
        options.setSpacing(12)
        options.addWidget(self.resell_card)
        options.addWidget(self.loss_card)

        layout.addLayout(options)
        return frame

    def _build_right_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        head = QHBoxLayout()
        icon = QLabel("↗")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(44, 44)
        icon.setStyleSheet(
            "background:#073e67;border:none;color:#5cecff;font-size:28px;font-weight:900;"
        )
        text = QVBoxLayout()
        text.setSpacing(1)
        title = QLabel("测算结果")
        title.setObjectName("sectionTitle")
        desc = QLabel("基于您输入的参数，智能测算关键指标")
        desc.setObjectName("hint")
        text.addWidget(title)
        text.addWidget(desc)

        slogan = QLabel("MAKE DATA CREATE MORE VALUE")
        slogan.setObjectName("eyebrow")
        slogan.setAlignment(Qt.AlignRight)

        head.addWidget(icon)
        head.addLayout(text)
        head.addStretch()
        head.addWidget(slogan)
        layout.addLayout(head)

        layout.addWidget(self._build_hero())

        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self.ad_metric = MetricCard("◖", "每单广告费", "#3acbff")
        self.fee_metric = MetricCard("⌂", "预计平台扣点", "#a777ff")
        self.margin_metric = MetricCard("%", "推广前毛利率", "#30e2bd")
        metrics.addWidget(self.ad_metric)
        metrics.addWidget(self.fee_metric)
        metrics.addWidget(self.margin_metric)
        layout.addLayout(metrics)

        layout.addWidget(self._build_formula_card())
        layout.addWidget(self._build_tip_card())
        layout.addStretch(1)
        return panel

    def _build_hero(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("hero")
        frame.setMinimumHeight(260)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)

        top = QHBoxLayout()

        result = QVBoxLayout()
        result.setSpacing(3)
        title = QLabel("最低保本 ROI   ⓘ")
        title.setObjectName("subSectionTitle")
        self.roi_value = QLabel("--")
        self.roi_value.setObjectName("metric")
        self.roi_caption = QLabel("填写左侧参数后自动测算")
        self.roi_caption.setObjectName("metricCaption")
        result.addWidget(title)
        result.addWidget(self.roi_value)
        result.addWidget(self.roi_caption)

        badge_box = QVBoxLayout()
        badge_box.addStretch()
        self.range_badge = QLabel("◎  等待测算")
        self.range_badge.setAlignment(Qt.AlignCenter)
        self.range_badge.setMinimumWidth(160)
        self.range_badge.setStyleSheet(
            "background:#053954;border:1px solid #24d9e7;border-radius:10px;"
            "padding:10px 12px;color:#63f2df;font-weight:900;"
        )
        badge_box.addWidget(self.range_badge)
        badge_box.addStretch()

        top.addLayout(result, 4)
        top.addLayout(badge_box, 2)
        top.addWidget(GrowthArt(), 4)
        layout.addLayout(top, 1)

        self.roi_scale = QProgressBar()
        self.roi_scale.setRange(0, 100)
        self.roi_scale.setValue(50)
        self.roi_scale.setTextVisible(False)
        layout.addWidget(self.roi_scale)

        labels = QHBoxLayout()
        low = QLabel("低 ROI（亏损）")
        mid = QLabel("盈亏平衡线")
        high = QLabel("高 ROI（盈利）")
        low.setStyleSheet("color:#ff5782;font-size:12px;")
        mid.setObjectName("hint")
        high.setStyleSheet("color:#55edb0;font-size:12px;")
        mid.setAlignment(Qt.AlignCenter)
        high.setAlignment(Qt.AlignRight)
        labels.addWidget(low)
        labels.addStretch()
        labels.addWidget(mid)
        labels.addStretch()
        labels.addWidget(high)
        layout.addLayout(labels)

        return frame

    def _build_formula_card(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("section")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(7)

        title = QLabel("▣   计算依据")
        title.setObjectName("subSectionTitle")

        formula = QLabel(
            "预计实收 = 商品售价 × (1 - 预计退款率)\n"
            "预计平台扣点 = 预计实收 × 平台扣点率\n"
            "可承受广告费 = 预计实收 - 预计平台扣点 - 有效商品成本 - 商品运费 - 运费险\n"
            "保本 ROI = 商品售价 ÷ 可承受广告费"
        )
        formula.setObjectName("formula")
        formula.setWordWrap(True)
        formula.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout.addWidget(title)
        layout.addWidget(separator())
        layout.addWidget(formula)
        return frame

    def _build_tip_card(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("tipCard")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(3)

        title = QLabel("💡   如何使用这个结果？")
        title.setObjectName("tipTitle")
        text = QLabel(
            "请先完整填写左侧各项经营参数，再结合保本 ROI 与毛利指标，判断当前商品是否具有足够的广告投放空间。"
        )
        text.setObjectName("hint")
        text.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(text)
        return frame

    def _wire_events(self) -> None:
        for field in (
            self.sale_price,
            self.product_cost,
            self.shipping_cost,
            self.shipping_insurance,
            self.platform_fee,
            self.refund_rate,
        ):
            field.edit.textChanged.connect(self.recalculate)

        self.resell_radio.toggled.connect(self._sync_return_cards)
        self.loss_radio.toggled.connect(self._sync_return_cards)
        self.resell_radio.toggled.connect(self.recalculate)
        self.loss_radio.toggled.connect(self.recalculate)

        self.reset_button.clicked.connect(self.reset_data)
        self.copy_button.clicked.connect(self.copy_result)
        self.save_button.clicked.connect(self.save_and_close)

    def _sync_return_cards(self) -> None:
        self.resell_card.set_selected(self.resell_radio.isChecked())
        self.loss_card.set_selected(self.loss_radio.isChecked())

    def _inputs(self) -> RoiInputs:
        return RoiInputs(
            sale_price=self.sale_price.value(),
            product_cost=self.product_cost.value(),
            shipping_cost=self.shipping_cost.value(),
            shipping_insurance=self.shipping_insurance.value(),
            platform_fee_rate=min(self.platform_fee.value(), 100.0) / 100.0,
            refund_rate=min(self.refund_rate.value(), 100.0) / 100.0,
            resellable_return=self.resell_radio.isChecked(),
        )

    def recalculate(self) -> None:
        try:
            result = calculate(self._inputs())
        except ValueError:
            return

        if result.break_even_roi is None:
            self.roi_value.setText("--")
            if self.sale_price.value() <= 0:
                self.roi_caption.setText("填写左侧参数后自动测算")
                self.range_badge.setText("◎  等待测算")
                self.roi_scale.setValue(0)
            else:
                self.roi_caption.setText("当前参数下推广前已无可承受广告费用")
                self.range_badge.setText("⚠  需优化成本")
                self.roi_scale.setValue(10)
        else:
            roi = result.break_even_roi
            self.roi_value.setText(f"{roi:.2f}")
            self.roi_caption.setText("达到该 ROI 即可覆盖预计成本并实现盈亏平衡")
            scale = max(0, min(100, int((roi / 6.0) * 100)))
            self.roi_scale.setValue(scale)

            if roi <= 2.0:
                self.range_badge.setText("◎  推荐范围\n投放空间充足")
            elif roi <= 3.5:
                self.range_badge.setText("◎  建议范围\n重点监控利润")
            else:
                self.range_badge.setText("⚠  保本偏高\n谨慎放量")

        self.ad_metric.value.setText(f"¥{result.max_ad_spend:.2f}")
        self.fee_metric.value.setText(f"¥{result.platform_fee:.2f}")
        self.margin_metric.value.setText(f"{result.pre_ad_margin_rate * 100:.1f}%")

    def _snapshot(self) -> dict:
        return {
            "sale_price": self.sale_price.value(),
            "product_cost": self.product_cost.value(),
            "shipping_cost": self.shipping_cost.value(),
            "shipping_insurance": self.shipping_insurance.value(),
            "platform_fee": self.platform_fee.value(),
            "refund_rate": self.refund_rate.value(),
            "resellable_return": self.resell_radio.isChecked(),
        }

    def _load_settings(self) -> None:
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except Exception:
            return

        self.sale_price.set_value(float(data.get("sale_price", 0)))
        self.product_cost.set_value(float(data.get("product_cost", 0)))
        self.shipping_cost.set_value(float(data.get("shipping_cost", 0)))
        self.shipping_insurance.set_value(float(data.get("shipping_insurance", 0)))
        self.platform_fee.set_value(float(data.get("platform_fee", 0)))
        self.refund_rate.set_value(float(data.get("refund_rate", 0)))

        resellable = bool(data.get("resellable_return", True))
        self.resell_radio.setChecked(resellable)
        self.loss_radio.setChecked(not resellable)

    def _save_settings(self) -> None:
        self.settings_path.write_text(
            json.dumps(self._snapshot(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def reset_data(self) -> None:
        for field in (
            self.sale_price,
            self.product_cost,
            self.shipping_cost,
            self.shipping_insurance,
            self.platform_fee,
            self.refund_rate,
        ):
            field.set_value(0)
        self.resell_radio.setChecked(True)
        self.recalculate()

    def result_text(self) -> str:
        result = calculate(self._inputs())
        roi = "--" if result.break_even_roi is None else f"{result.break_even_roi:.2f}"
        return (
            f"ROI智能计算器 v{__version__}\n"
            f"最低保本 ROI：{roi}\n"
            f"每单可承受广告费：¥{result.max_ad_spend:.2f}\n"
            f"预计平台扣点：¥{result.platform_fee:.2f}\n"
            f"推广前毛利率：{result.pre_ad_margin_rate * 100:.1f}%"
        )

    def copy_result(self) -> None:
        QApplication.clipboard().setText(self.result_text())
        self.copy_button.setText("✓  已复制")
        QTimer.singleShot(
            1200,
            lambda: self.copy_button.setText("▣  复制测算结果"),
        )

    def save_and_close(self) -> None:
        try:
            self._save_settings()
        except Exception as exc:
            QMessageBox.warning(self, "保存失败", str(exc))
            return
        self.close()

    def closeEvent(self, event) -> None:
        try:
            self._save_settings()
        except Exception:
            pass
        super().closeEvent(event)


def run_gui() -> int:
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("ROI智能计算器")
    app.setApplicationVersion(__version__)
    app.setStyleSheet(APP_QSS)
    app.setFont(QFont("Microsoft YaHei UI", 10))

    window = MainWindow()
    window.show()

    return app.exec()
