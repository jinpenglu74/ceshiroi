from __future__ import annotations

import os
import sys

from roi_calculator.domain import RoiInputs, calculate
from roi_calculator.version import __version__


def self_test() -> int:
    result = calculate(
        RoiInputs(
            sale_price=100,
            product_cost=40,
            shipping_cost=10,
            shipping_insurance=2,
            platform_fee_rate=0.05,
            refund_rate=0.0,
            resellable_return=True,
        )
    )
    if abs(result.max_ad_spend - 43.0) > 1e-9:
        return 2
    if result.break_even_roi is None:
        return 3
    expected_roi = 100 / 43
    if abs(result.break_even_roi - expected_roi) > 1e-9:
        return 4
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    if "--version" in sys.argv:
        print(__version__)
        return 0

    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    from roi_calculator.gui import run_gui

    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
