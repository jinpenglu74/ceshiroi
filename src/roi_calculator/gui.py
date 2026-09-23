from __future__ import annotations

import json
import math
import os
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QDoubleValidator,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
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
from .theme import (
    AMBER,
    APP_QSS,
    BLUE,
    CYAN,
    GREEN,
    MUTED,
    PINK,
    PURPLE,
    add_glow,
)
from .version import __version__


class TechBackdrop(QWidget):
    """Animated HUD-style background with grid, nodes and a subtle scan line."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("root")
        self._scan = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(55)

    def _tick(self) -> None:
        self._scan = (self._scan + 3) % max(1, self.height())
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        bg = QLinearGradient(0, 0, self.width(), self.height())
        bg.setColorAt(0.0, QColor("#020713"))
        bg.setColorAt(0.50, QColor("#03142B"))
        bg.setColorAt(1.0, QColor("#041B34"))
        painter.fillRect(self.rect(), bg)

        grid_pen = QPen(QColor(33, 127, 190, 28), 1)
        painter.setPen(grid_pen)
        step = 44
        for x in range(0, self.width(), step):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), step):
            painter.drawLine(0, y, self.width(), y)

        # Circuit paths.
        circuit_pen = QPen(QColor(39, 203, 237, 40), 1)
        painter.setPen(circuit_pen)
        points = [
            (0.04, 0.15, 0.20, 0.15, 0.24, 0.10),
            (0.72, 0.13, 0.88, 0.13, 0.93, 0.19),
            (0.07, 0.78, 0.19, 0.78, 0.24, 0.84),
            (0.76, 0.77, 0.91, 0.77, 0.95, 0.72),
        ]
        for x1, y1, x2, y2, x3, y3 in points:
            path = QPainterPath()
            path.moveTo(self.width() * x1, self.height() * y1)
            path.lineTo(self.width() * x2, self.height() * y2)
            path.lineTo(self.width() * x3, self.height() * y3)
            painter.drawPath(path)
            painter.setBrush(QColor(55, 230, 255, 90))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(
                QPointF(self.width() * x3, self.height() * y3),
                2.8,
                2.8,
            )
            painter.setPen(circuit_pen)

        # Soft radial glows in opposite corners.
        for cx, cy, color in (
            (self.width() * 0.08, self.height() * 0.13, QColor(0, 122, 255, 75)),
            (self.width() * 0.92, self.height() * 0.72, QColor(0, 221, 255, 55)),
        ):
            radial = QRadialGradient(cx, cy, 260)
            radial.setColorAt(0.0, color)
            faded = QColor(color)
            faded.setAlpha(0)
            radial.setColorAt(1.0, faded)
            painter.setBrush(radial)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(cx, cy), 260, 260)

        # Horizontal scan line.
        scan = QLinearGradient(0, self._scan - 16, 0, self._scan + 16)
        scan.setColorAt(0.0, QColor(33, 221, 255, 0))
        scan.setColorAt(0.5, QColor(33, 221, 255, 23))
        scan.setColorAt(1.0, QColor(33, 221, 255, 0))
        painter.fillRect(0, self._scan - 16, self.width(), 32, scan)


class HudFrame(QFrame):
    """Panel with small bright corner brackets."""

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(53, 230, 255, 155), 2)
        painter.setPen(pen)

        inset = 7
        length = 18
        w = self.width() - inset
        h = self.height() - inset

        corners = (
            ((inset, inset + length), (inset, inset), (inset + length, inset)),
            ((w - length, inset), (w, inset), (w, inset + length)),
            ((inset, h - length), (inset, h), (inset + length, h)),
            ((w - length, h), (w, h), (w, h - length)),
        )
        for a, b, c in corners:
            painter.drawLine(*a, *b)
            painter.drawLine(*b, *c)


def separator() -> QFrame:
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet(
        "background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        "stop:0 rgba(41,210,255,0),stop:0.50 rgba(41,210,255,130),"
        "stop:1 rgba(41,210,255,0));border:none;"
    )
    return line


class MoneyField(QWidget):
    def __init__(self, title: str, *, percent: bool = False) -> None:
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

        unit_text = "%" if percent else "¥"
        prefix = QLabel(unit_text)
        prefix.setAlignment(Qt.AlignCenter)
        prefix.setFixedWidth(34)
        prefix.setStyleSheet(
            "background:#08264B;border:1px solid #1A699E;border-radius:7px;"
            "font-weight:900;color:#43DDFB;padding:8px 0;"
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

        row.addWidget(prefix)
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


class MetricCard(HudFrame):
    def __init__(self, symbol: str, title: str, accent: str) -> None:
        super().__init__()
        self.setObjectName("metricCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(92)

        row = QHBoxLayout(self)
        row.setContentsMargins(14, 12, 14, 12)
        row.setSpacing(12)

        icon = QLabel(symbol)
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(54, 54)
        icon.setStyleSheet(
            f"background:#092B55;border:1px solid {accent};border-radius:10px;"
            f"color:{accent};font-size:23px;font-weight:900;"
        )
        add_glow(icon, accent, 18, 105)

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


class RoiRadarArt(QWidget):
    """Decorative data-radar visual for the main result area."""

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(245, 165)
        self._phase = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(90)

    def _animate(self) -> None:
        self._phase = (self._phase + 3) % 360
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        center = QPointF(w * 0.69, h * 0.50)
        radius = min(w, h) * 0.33

        for i, alpha in ((1, 80), (2, 55), (3, 35)):
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(48, 212, 255, alpha), 1))
            painter.drawEllipse(center, radius * i / 3, radius * i / 3)

        painter.setPen(QPen(QColor(43, 141, 207, 60), 1))
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            endpoint = QPointF(
                center.x() + math.cos(rad) * radius,
                center.y() + math.sin(rad) * radius,
            )
            painter.drawLine(center, endpoint)

        # Sweeping radar beam.
        sweep = math.radians(self._phase)
        endpoint = QPointF(
            center.x() + math.cos(sweep) * radius,
            center.y() + math.sin(sweep) * radius,
        )
        painter.setPen(QPen(QColor(66, 239, 255, 150), 2))
        painter.drawLine(center, endpoint)

        # Growth bars.
        base = h * 0.83
        xs = [w * 0.08, w * 0.20, w * 0.32]
        bar_heights = [h * 0.23, h * 0.38, h * 0.55]
        bar_w = max(15, int(w * 0.07))
        grad = QLinearGradient(0, base, 0, h * 0.18)
        grad.setColorAt(0.0, QColor(BLUE))
        grad.setColorAt(1.0, QColor(CYAN))
        painter.setBrush(grad)
        painter.setPen(QPen(QColor(CYAN), 1.5))
        for x, bh in zip(xs, bar_heights):
            painter.drawRoundedRect(
                QRectF(x, base - bh, bar_w, bh),
                3,
                3,
            )

        path = QPainterPath()
        path.moveTo(w * 0.07, h * 0.65)
        path.cubicTo(w * 0.18, h * 0.64, w * 0.28, h * 0.42, w * 0.42, h * 0.29)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(CYAN), 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(path)

        arrow = QPainterPath()
        arrow.moveTo(w * 0.39, h * 0.21)
        arrow.lineTo(w * 0.49, h * 0.25)
        arrow.lineTo(w * 0.43, h * 0.34)
        arrow.closeSubpath()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(CYAN))
        painter.drawPath(arrow)


class ReturnOption(HudFrame):
    def __init__(self, radio: QRadioButton, symbol: str, subtitle: str) -> None:
        super().__init__()
        self.radio = radio
        self.setObjectName("returnOption")

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 7, 10, 7)
        row.setSpacing(10)

        icon = QLabel(symbol)
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(34, 34)
        icon.setStyleSheet("color:#35E6FF;font-size:22px;font-weight:900;")

        text = QVBoxLayout()
        text.setSpacing(1)
        text.addWidget(radio)
        sub = QLabel(subtitle)
        sub.setObjectName("hint")
        text.addWidget(sub)

        row.addWidget(icon)
        row.addLayout(text, 1)
        self.set_selected(False)

    def set_selected(self, selected: bool) -> None:
        if selected:
            self.setStyleSheet(
                "QFrame#returnOption{background:#07325B;border:2px solid #24DFFF;"
                "border-radius:9px;}QFrame#returnOption:hover{border:2px solid #68F0FF;}"
            )
        else:
            self.setStyleSheet(
                "QFrame#returnOption{background:#08264D;border:1px solid #0B659F;"
                "border-radius:9px;}QFrame#returnOption:hover{border:1px solid #24CAFF;}"
            )


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"ROI智能计算器  v{__version__}")
        self.resize(1580, 920)
        self.setMinimumSize(1220, 780)

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
        root = TechBackdrop()
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

        info = QLabel("SYSTEM NOTE  /  测算结果仅供决策参考，请结合真实经营数据动态校准")
        info.setObjectName("hint")

        self.copy_button = QPushButton("复制测算结果")
        self.copy_button.setObjectName("ghost")

        self.save_button = QPushButton("保存并关闭")
        self.save_button.setObjectName("primary")
        add_glow(self.save_button, BLUE, 20, 95)

        footer.addWidget(info)
        footer.addStretch(1)
        footer.addWidget(self.copy_button)
        footer.addWidget(self.save_button)
        page.addLayout(footer)

    def _build_topbar(self) -> HudFrame:
        frame = HudFrame()
        frame.setObjectName("topbar")
        frame.setMinimumHeight(96)

        row = QHBoxLayout(frame)
        row.setContentsMargins(18, 12, 18, 12)
        row.setSpacing(14)

        logo = QLabel("↗")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(60, 60)
        logo.setStyleSheet(
            "background:qlineargradient(x1:0,y1:1,x2:1,y2:0,"
            "stop:0 #1264E3,stop:1 #4DEEFF);"
            "border:1px solid #45DBFF;border-radius:12px;"
            "color:white;font-size:36px;font-weight:900;"
        )
        add_glow(logo, CYAN, 28, 135)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        status = QLabel("ROI INTELLIGENCE CONSOLE")
        status.setObjectName("eyebrow")
        title = QLabel("ROI智能计算器")
        title.setObjectName("title")
        subtitle = QLabel("输入经营参数 · 实时测算盈亏平衡 · 识别广告投放空间")
        subtitle.setObjectName("subtitle")
        title_box.addWidget(status)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        slogan = QVBoxLayout()
        slogan.setSpacing(3)
        line1 = QLabel("DATA DRIVEN GROWTH")
        line1.setObjectName("eyebrow")
        line1.setAlignment(Qt.AlignRight)
        line2 = QLabel("MAKE ROI VISIBLE")
        line2.setStyleSheet("color:#8FC7E8;font-size:11px;font-weight:700;")
        line2.setAlignment(Qt.AlignRight)
        version = QLabel(f"CORE BUILD  V{__version__}")
        version.setObjectName("hint")
        version.setAlignment(Qt.AlignRight)
        slogan.addWidget(line1)
        slogan.addWidget(line2)
        slogan.addWidget(version)

        self.reset_button = QPushButton("重置数据")
        self.reset_button.setObjectName("ghost")

        row.addWidget(logo)
        row.addLayout(title_box)
        row.addStretch(1)
        row.addLayout(slogan)
        row.addWidget(self.reset_button)
        return frame

    def _panel_header(self, code: str, title_text: str, desc_text: str, accent: str):
        row = QHBoxLayout()
        row.setSpacing(12)

        code_label = QLabel(code)
        code_label.setAlignment(Qt.AlignCenter)
        code_label.setFixedSize(46, 46)
        code_label.setStyleSheet(
            f"background:#082A53;border:1px solid {accent};border-radius:9px;"
            f"color:{accent};font-size:15px;font-weight:900;"
        )

        text = QVBoxLayout()
        text.setSpacing(1)
        title = QLabel(title_text)
        title.setObjectName("sectionTitle")
        desc = QLabel(desc_text)
        desc.setObjectName("hint")
        text.addWidget(title)
        text.addWidget(desc)

        row.addWidget(code_label)
        row.addLayout(text)
        row.addStretch(1)
        return row

    def _build_left_panel(self) -> HudFrame:
        panel = HudFrame()
        panel.setObjectName("panel")
        panel.setMinimumWidth(480)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        layout.addLayout(
            self._panel_header(
                "INPUT",
                "经营参数",
                "精准输入商品、平台与售后数据",
                CYAN,
            )
        )

        layout.addWidget(self._build_income_section())
        layout.addWidget(self._build_platform_section())
        layout.addWidget(self._build_return_section())
        layout.addStretch(1)
        return panel

    def _build_income_section(self) -> HudFrame:
        frame = HudFrame()
        frame.setObjectName("section")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        title = QLabel("01  /  商品收入与成本")
        title.setObjectName("subSectionTitle")
        layout.addWidget(title)
        layout.addWidget(separator())

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

    def _build_platform_section(self) -> HudFrame:
        frame = HudFrame()
        frame.setObjectName("section")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        title = QLabel("02  /  平台与售后")
        title.setObjectName("subSectionTitle")
        layout.addWidget(title)
        layout.addWidget(separator())

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)

        self.platform_fee = MoneyField("平台扣点", percent=True)
        self.refund_rate = MoneyField("预计退款率", percent=True)

        grid.addWidget(self.platform_fee, 0, 0)
        grid.addWidget(self.refund_rate, 0, 1)

        layout.addLayout(grid)
        return frame

    def _build_return_section(self) -> HudFrame:
        frame = HudFrame()
        frame.setObjectName("section")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        title = QLabel("03  /  退货成本口径")
        title.setObjectName("subSectionTitle")
        layout.addWidget(title)
        layout.addWidget(separator())

        self.resell_radio = QRadioButton("可再次销售")
        self.loss_radio = QRadioButton("成本全部损失")
        self.resell_radio.setChecked(True)

        self.return_group = QButtonGroup(self)
        self.return_group.setExclusive(True)
        self.return_group.addButton(self.resell_radio)
        self.return_group.addButton(self.loss_radio)

        self.resell_card = ReturnOption(
            self.resell_radio,
            "R",
            "退货商品成本可回收",
        )
        self.loss_card = ReturnOption(
            self.loss_radio,
            "L",
            "退货商品成本全部计入",
        )

        options = QHBoxLayout()
        options.setSpacing(12)
        options.addWidget(self.resell_card)
        options.addWidget(self.loss_card)

        layout.addLayout(options)
        return frame

    def _build_right_panel(self) -> HudFrame:
        panel = HudFrame()
        panel.setObjectName("panel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        head = self._panel_header(
            "LIVE",
            "测算结果",
            "实时分析盈亏平衡与广告承载能力",
            GREEN,
        )
        badge = QLabel("●  ENGINE ONLINE")
        badge.setStyleSheet(
            "color:#47F2B6;background:#082D31;border:1px solid #1B8F73;"
            "border-radius:8px;padding:6px 10px;font-size:11px;font-weight:800;"
        )
        head.addWidget(badge)
        layout.addLayout(head)

        layout.addWidget(self._build_hero())

        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self.ad_metric = MetricCard("AD", "每单广告费", CYAN)
        self.fee_metric = MetricCard("PF", "预计平台扣点", PURPLE)
        self.margin_metric = MetricCard("%", "推广前毛利率", GREEN)
        metrics.addWidget(self.ad_metric)
        metrics.addWidget(self.fee_metric)
        metrics.addWidget(self.margin_metric)
        layout.addLayout(metrics)

        lower = QHBoxLayout()
        lower.setSpacing(12)
        lower.addWidget(self._build_formula_card(), 3)
        lower.addWidget(self._build_tip_card(), 2)
        layout.addLayout(lower)

        layout.addStretch(1)
        return panel

    def _build_hero(self) -> HudFrame:
        frame = HudFrame()
        frame.setObjectName("hero")
        frame.setMinimumHeight(278)
        add_glow(frame, CYAN, 24, 78)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)

        top = QHBoxLayout()

        result = QVBoxLayout()
        result.setSpacing(4)

        micro = QLabel("BREAK-EVEN INTELLIGENCE")
        micro.setObjectName("eyebrow")
        title = QLabel("最低保本 ROI")
        title.setObjectName("subSectionTitle")
        self.roi_value = QLabel("--")
        self.roi_value.setObjectName("metric")
        add_glow(self.roi_value, CYAN, 28, 105)
        self.roi_caption = QLabel("填写左侧参数后自动测算")
        self.roi_caption.setObjectName("metricCaption")
        self.roi_caption.setWordWrap(True)

        result.addWidget(micro)
        result.addWidget(title)
        result.addWidget(self.roi_value)
        result.addWidget(self.roi_caption)

        status = QVBoxLayout()
        status.addStretch()
        self.range_badge = QLabel("STANDBY\n等待测算")
        self.range_badge.setAlignment(Qt.AlignCenter)
        self.range_badge.setMinimumWidth(164)
        self.range_badge.setStyleSheet(
            "background:#07364D;border:1px solid #24D9E7;border-radius:10px;"
            "padding:10px 12px;color:#63F2DF;font-weight:900;"
        )
        status.addWidget(self.range_badge)
        status.addStretch()

        top.addLayout(result, 4)
        top.addLayout(status, 2)
        top.addWidget(RoiRadarArt(), 4)

        layout.addLayout(top, 1)
        layout.addWidget(separator())

        line = QHBoxLayout()
        label = QLabel("ROI RISK / PROFIT VECTOR")
        label.setObjectName("eyebrow")
        self.scale_value = QLabel("0%")
        self.scale_value.setObjectName("hint")
        self.scale_value.setAlignment(Qt.AlignRight)
        line.addWidget(label)
        line.addStretch()
        line.addWidget(self.scale_value)
        layout.addLayout(line)

        self.roi_scale = QProgressBar()
        self.roi_scale.setRange(0, 100)
        self.roi_scale.setValue(0)
        self.roi_scale.setTextVisible(False)
        layout.addWidget(self.roi_scale)

        labels = QHBoxLayout()
        low = QLabel("LOSS")
        mid = QLabel("BREAK-EVEN")
        high = QLabel("PROFIT")
        low.setStyleSheet(f"color:{PINK};font-size:11px;font-weight:800;")
        mid.setStyleSheet("color:#7DB5DB;font-size:11px;font-weight:800;")
        high.setStyleSheet(f"color:{GREEN};font-size:11px;font-weight:800;")
        mid.setAlignment(Qt.AlignCenter)
        high.setAlignment(Qt.AlignRight)
        labels.addWidget(low)
        labels.addStretch()
        labels.addWidget(mid)
        labels.addStretch()
        labels.addWidget(high)
        layout.addLayout(labels)

        return frame

    def _build_formula_card(self) -> HudFrame:
        frame = HudFrame()
        frame.setObjectName("section")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(7)

        title = QLabel("FORMULA CORE  /  计算依据")
        title.setObjectName("subSectionTitle")

        formula = QLabel(
            "预计实收 = 商品售价 × (1 - 预计退款率)\n"
            "预计平台扣点 = 预计实收 × 平台扣点率\n"
            "可承受广告费 = 预计实收 - 平台扣点 - 有效商品成本 - 运费 - 运费险\n"
            "保本 ROI = 商品售价 ÷ 可承受广告费"
        )
        formula.setObjectName("formula")
        formula.setWordWrap(True)
        formula.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout.addWidget(title)
        layout.addWidget(separator())
        layout.addWidget(formula)
        return frame

    def _build_tip_card(self) -> HudFrame:
        frame = HudFrame()
        frame.setObjectName("tipCard")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(5)

        title = QLabel("DECISION ASSIST")
        title.setStyleSheet(f"color:{AMBER};font-size:15px;font-weight:850;")
        sub = QLabel("如何使用这个结果？")
        sub.setObjectName("tipTitle")
        text = QLabel(
            "先完整填写经营参数，再结合保本 ROI 与毛利率判断广告投放空间。"
            "保本门槛越低，通常意味着可承受的获客成本空间越充足。"
        )
        text.setObjectName("hint")
        text.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(sub)
        layout.addWidget(separator())
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
                self.range_badge.setText("STANDBY\n等待测算")
                self.roi_scale.setValue(0)
                self.scale_value.setText("0%")
            else:
                self.roi_caption.setText("当前参数下推广前已无可承受广告费用")
                self.range_badge.setText("ALERT\n需优化成本")
                self.range_badge.setStyleSheet(
                    f"background:#3A1830;border:1px solid {PINK};border-radius:10px;"
                    f"padding:10px 12px;color:#FF86AC;font-weight:900;"
                )
                self.roi_scale.setValue(8)
                self.scale_value.setText("08%")
        else:
            roi = result.break_even_roi
            self.roi_value.setText(f"{roi:.2f}")
            self.roi_caption.setText("达到该 ROI 即可覆盖预计成本并实现盈亏平衡")
            scale = max(0, min(100, int((roi / 6.0) * 100)))
            self.roi_scale.setValue(scale)
            self.scale_value.setText(f"{scale:02d}%")

            if roi <= 2.0:
                self.range_badge.setText("OPTIMAL\n投放空间充足")
                badge_color = GREEN
                badge_bg = "#0B3A34"
            elif roi <= 3.5:
                self.range_badge.setText("WATCH\n重点监控利润")
                badge_color = CYAN
                badge_bg = "#07364D"
            else:
                self.range_badge.setText("CAUTION\n保本门槛偏高")
                badge_color = AMBER
                badge_bg = "#403516"

            self.range_badge.setStyleSheet(
                f"background:{badge_bg};border:1px solid {badge_color};border-radius:10px;"
                f"padding:10px 12px;color:{badge_color};font-weight:900;"
            )

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
        self.copy_button.setText("已复制")
        QTimer.singleShot(1200, lambda: self.copy_button.setText("复制测算结果"))

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
