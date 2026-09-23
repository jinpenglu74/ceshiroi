import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from roi_calculator.gui import MainWindow
from roi_calculator.version import __version__


def test_window_smoke_and_live_recalculate():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert __version__ == "1.0.2"
    assert "ROI智能计算器" in window.windowTitle()

    window.sale_price.set_value(100)
    window.product_cost.set_value(40)
    window.shipping_cost.set_value(10)
    window.shipping_insurance.set_value(2)
    window.platform_fee.set_value(5)
    window.refund_rate.set_value(0)
    window.resell_radio.setChecked(True)
    window.recalculate()

    assert window.roi_value.text() == "2.33"
    assert window.ad_metric.value.text() == "¥43.00"
    assert window.fee_metric.value.text() == "¥5.00"
    assert window.margin_metric.value.text() == "43.0%"

    window.close()
    app.processEvents()
