"""Synthetic monthly finance calculations against a disposable MySQL database."""

from datetime import datetime
from decimal import Decimal

import pytest

from app.assets.router import asset_month_summary
from app.bills.service import list_bills
from app.incomes.router import income_summary
from app.investments.router import investment_month_rows
from app.models.asset import AssetItem, AssetMonthValue
from app.models.bill import Bill
from app.models.income import IncomeEntry, MonthlyIncome
from app.models.investment import InvestmentItem, InvestmentMonth
from app.models.user import User
from app.reports.router import category_summary

pytestmark = pytest.mark.mysql


async def test_category_drilldown_matches_report_expense_scope(upload_db):
    sessions, task_id, user_id = upload_db
    async with sessions() as session:
        for index, (bill_type, lifecycle, archived) in enumerate([
            ("expense", "unprocessed", True),
            ("income", "unprocessed", True),
            ("expense", "skipped", True),
            ("expense", "cross_month_refund", True),
            ("expense", "unprocessed", False),
        ]):
            session.add(Bill(
                user_id=user_id, upload_task_id=task_id, source="wechat",
                order_id=f"report-scope-{index}", amount=Decimal("10"),
                bill_type=bill_type, bill_time=datetime(2026, 1, 5, 12),
                lifecycle=lifecycle, archived=archived,
            ))
        await session.commit()
        user = await session.get(User, user_id)
        report = (await category_summary(user, session, month="2026-01"))["data"]
        bills, total = await list_bills(session, user_id, month="2026-01",
                                       unclassified=True, report_expense=True)
        assert report["total_expense"] == "10.00"
        assert total == 1
        assert sum((bill.amount for bill in bills), Decimal("0")) == Decimal(report["total_expense"])


async def test_asset_items_recur_without_carrying_values_and_investments_count_once(upload_db):
    sessions, _, user_id = upload_db
    async with sessions() as session:
        bank = AssetItem(user_id=user_id, name="测试银行卡", kind="asset")
        debt = AssetItem(user_id=user_id, name="测试负债", kind="liability")
        fund = InvestmentItem(user_id=user_id, name="测试基金", first_month="2026-01",
                              initial_principal=Decimal("1000"))
        session.add_all([bank, debt, fund])
        await session.flush()
        session.add_all([
            AssetMonthValue(item_id=bank.id, month="2026-01", amount=Decimal("200")),
            AssetMonthValue(item_id=debt.id, month="2026-01", amount=Decimal("50")),
            InvestmentMonth(item_id=fund.id, month="2026-01", buys=Decimal("100"),
                            sells=Decimal("0"), closing_value=Decimal("1100")),
            InvestmentMonth(item_id=fund.id, month="2026-02", buys=Decimal("50"),
                            sells=Decimal("20"), closing_value=Decimal("1150")),
        ])
        await session.commit()

        january = await asset_month_summary(session, user_id, "2026-01")
        assert january["asset_total"] == "1300.00"
        assert january["liability_total"] == "50.00"
        assert january["net_assets"] == "1250.00"
        assert january["complete"] is True
        assert len(january["investments"]) == 1

        february = await asset_month_summary(session, user_id, "2026-02")
        assert february["asset_total"] == "1150.00"
        assert february["complete"] is False
        assert [row["amount"] for row in february["items"]] == [None, None]
        profit = await investment_month_rows(session, user_id, "2026-02")
        assert profit[0]["profit"] == "20.00"


async def test_investment_missing_prior_month_does_not_fake_profit(upload_db):
    sessions, _, user_id = upload_db
    async with sessions() as session:
        fund = InvestmentItem(user_id=user_id, name="待补估值", first_month="2026-01",
                              initial_principal=Decimal("100"))
        session.add(fund)
        await session.flush()
        session.add(InvestmentMonth(item_id=fund.id, month="2026-02", buys=Decimal("10"),
                                    sells=Decimal("0"), closing_value=Decimal("120")))
        await session.commit()
        row = (await investment_month_rows(session, user_id, "2026-02"))[0]
        assert row["closing_value"] == "120.00"
        assert row["profit"] is None
        assert row["missing_previous"] is True


async def test_linked_legacy_asset_is_not_counted_with_investment(upload_db):
    sessions, _, user_id = upload_db
    async with sessions() as session:
        old_stock = AssetItem(user_id=user_id, name="旧股票账户", kind="asset", legacy_type="stock")
        session.add(old_stock)
        await session.flush()
        fund = InvestmentItem(user_id=user_id, name="新投资项", first_month="2026-01",
                              initial_principal=Decimal("500"), linked_asset_item_id=old_stock.id)
        session.add(fund)
        await session.flush()
        session.add_all([
            AssetMonthValue(item_id=old_stock.id, month="2026-01", amount=Decimal("500")),
            InvestmentMonth(item_id=fund.id, month="2026-01", buys=Decimal("0"),
                            sells=Decimal("0"), closing_value=Decimal("600")),
        ])
        await session.commit()
        summary = await asset_month_summary(session, user_id, "2026-01")
        assert summary["asset_total"] == "600.00"
        assert summary["items"][0]["amount"] == "500.00"
        assert summary["items"][0]["included_in_total"] is False


async def test_dated_income_and_legacy_month_only_income_are_summed_once(upload_db):
    sessions, _, user_id = upload_db
    async with sessions() as session:
        session.add_all([
            IncomeEntry(user_id=user_id, occurred_at=datetime(2026, 1, 3, 9),
                        amount=Decimal("100"), source="工资"),
            IncomeEntry(user_id=user_id, occurred_at=datetime(2026, 1, 20, 9),
                        amount=Decimal("200"), source="工资"),
            MonthlyIncome(user_id=user_id, year_month="2026-01", amount=Decimal("50"),
                          source="旧记录"),
        ])
        await session.commit()
        user = await session.get(User, user_id)
        response = await income_summary(user, session, year=2026, month="2026-01")
        assert response["data"]["month_total"] == "350.00"
        assert response["data"]["year_total"] == "350.00"
        assert response["data"]["legacy_monthly"][0]["year_month"] == "2026-01"
