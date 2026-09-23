import pytest

from roi_calculator.domain import RoiInputs, calculate


def test_basic_break_even():
    result = calculate(RoiInputs(100, 40, 10, 2, 0.05, 0, True))
    assert result.expected_revenue == pytest.approx(100)
    assert result.platform_fee == pytest.approx(5)
    assert result.effective_product_cost == pytest.approx(40)
    assert result.max_ad_spend == pytest.approx(43)
    assert result.break_even_roi == pytest.approx(100 / 43)
    assert result.pre_ad_margin_rate == pytest.approx(0.43)


def test_refund_resellable_recovers_product_cost():
    result = calculate(RoiInputs(100, 40, 10, 2, 0.05, 0.20, True))
    assert result.expected_revenue == pytest.approx(80)
    assert result.platform_fee == pytest.approx(4)
    assert result.effective_product_cost == pytest.approx(32)
    assert result.max_ad_spend == pytest.approx(32)
    assert result.break_even_roi == pytest.approx(3.125)


def test_refund_total_loss_keeps_full_product_cost():
    result = calculate(RoiInputs(100, 40, 10, 2, 0.05, 0.20, False))
    assert result.effective_product_cost == pytest.approx(40)
    assert result.max_ad_spend == pytest.approx(24)
    assert result.break_even_roi == pytest.approx(100 / 24)


def test_no_profit_space_returns_no_roi():
    result = calculate(RoiInputs(50, 45, 10, 2, 0.05, 0, False))
    assert result.max_ad_spend < 0
    assert result.break_even_roi is None
    assert not result.is_profitable_before_ads


@pytest.mark.parametrize("field", ["platform_fee_rate", "refund_rate"])
def test_invalid_rates_rejected(field):
    values = dict(
        sale_price=100,
        product_cost=20,
        shipping_cost=5,
        shipping_insurance=1,
        platform_fee_rate=0.1,
        refund_rate=0.1,
        resellable_return=True,
    )
    values[field] = 1.1
    with pytest.raises(ValueError):
        calculate(RoiInputs(**values))


def test_negative_money_rejected():
    with pytest.raises(ValueError):
        calculate(RoiInputs(100, -1, 5, 1, 0.1, 0.1, True))
