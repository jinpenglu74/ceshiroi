from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoiInputs:
    sale_price: float
    product_cost: float
    shipping_cost: float
    shipping_insurance: float
    platform_fee_rate: float
    refund_rate: float
    resellable_return: bool = True

    def validate(self) -> None:
        money_values = (
            self.sale_price,
            self.product_cost,
            self.shipping_cost,
            self.shipping_insurance,
        )
        if any(value < 0 for value in money_values):
            raise ValueError("金额不能为负数")
        if not 0 <= self.platform_fee_rate <= 1:
            raise ValueError("平台扣点必须在 0% 到 100% 之间")
        if not 0 <= self.refund_rate <= 1:
            raise ValueError("退款率必须在 0% 到 100% 之间")


@dataclass(frozen=True)
class RoiResult:
    expected_revenue: float
    platform_fee: float
    effective_product_cost: float
    max_ad_spend: float
    break_even_roi: float | None
    pre_ad_margin_rate: float

    @property
    def is_profitable_before_ads(self) -> bool:
        return self.max_ad_spend > 0


def calculate(inputs: RoiInputs) -> RoiResult:
    inputs.validate()

    expected_revenue = inputs.sale_price * (1 - inputs.refund_rate)
    platform_fee = expected_revenue * inputs.platform_fee_rate

    if inputs.resellable_return:
        effective_product_cost = inputs.product_cost * (1 - inputs.refund_rate)
    else:
        effective_product_cost = inputs.product_cost

    max_ad_spend = (
        expected_revenue
        - platform_fee
        - effective_product_cost
        - inputs.shipping_cost
        - inputs.shipping_insurance
    )

    break_even_roi = None
    if inputs.sale_price > 0 and max_ad_spend > 0:
        break_even_roi = inputs.sale_price / max_ad_spend

    pre_ad_margin_rate = (
        max_ad_spend / inputs.sale_price if inputs.sale_price > 0 else 0.0
    )

    return RoiResult(
        expected_revenue=expected_revenue,
        platform_fee=platform_fee,
        effective_product_cost=effective_product_cost,
        max_ad_spend=max_ad_spend,
        break_even_roi=break_even_roi,
        pre_ad_margin_rate=pre_ad_margin_rate,
    )
