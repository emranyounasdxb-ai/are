from datetime import UTC, datetime

from app.acquisition.contracts import FetchResult, ManifestCandidate
from app.acquisition.tanami import _combined_normalized
from app.acquisition.tanami_context import (
    ContextTable,
    contextual_tables,
    payment_variants,
    select_unambiguous_plan,
    summary_facts,
)


def test_payment_table_ignores_navigation_leads_and_related_projects():
    table = """<table><tr><th>Installment</th><th>Payment</th><th>Milestone</th></tr>
    <tr><td>Down Payment</td><td>10%</td><td>On Booking</td></tr>
    <tr><td>Installments</td><td>30%</td><td>1% monthly for 30 months</td></tr>
    <tr><td>Final</td><td>60%</td><td>On Handover</td></tr></table>"""
    html = "<form><nav>Payment Plan " + "navigation " * 100 + "</nav><main>"
    html += '<aside id="enq">' + table + "</aside><h2>Payment Plan</h2>" + table
    html += "<h3>More Projects of Example</h3>" + table + "</main></form>"
    tables = contextual_tables(html.encode())
    assert len(tables) == 1
    plans = payment_variants(tables)
    assert plans[0]["percentages"] == [10, 30, 60]
    assert plans[0]["milestones"][1]["source_value"].endswith("1% monthly for 30 months")
    assert select_unambiguous_plan(plans) is not None


def test_separate_unit_and_resident_offers_are_never_one_project_plan():
    tables = [
        ContextTable(
            title,
            [
                ["Installment", "Payment", "Milestone"],
                ["Down Payment", str(percent) + "%", "On Booking Date"],
                ["Installments", str(100 - percent) + "%", "For 99 Months"],
            ],
        )
        for title, percent in [("Option 1: UAE Residents", 1), ("2 Bedroom Plan", 10)]
    ]
    plans = payment_variants(tables)
    assert len(plans) == 2
    assert all(p["is_complete"] for p in plans)
    assert select_unambiguous_plan(plans) is None
    assert select_unambiguous_plan(plans[1:]) is None


def test_options_and_handover_groups_inside_one_table_remain_separate():
    plans = payment_variants(
        [
            ContextTable(
                "2 Bedroom Options",
                [
                    ["Option I"],
                    ["Installments", "Payment (%)", "Milestones"],
                    ["Down Payment", "4%", "On Booking"],
                    ["Installments", "36%", "Monthly"],
                    ["After Handover"],
                    ["Final installments", "60%", "For 48 Months"],
                    ["Option II"],
                    ["Down Payment", "10%", "On Booking"],
                    ["Final", "90%", "On Handover"],
                ],
            )
        ]
    )
    assert [p["percentages"] for p in plans] == [[4, 36, 60], [10, 90]]
    assert plans[0]["milestones"][-1]["stage"] == "post-handover"
    assert plans[1]["milestones"][0]["stage"] == "booking"


def test_incomplete_or_unlabelled_percentages_do_not_become_complete_plans():
    assert payment_variants([ContextTable("Price", [["AED", "10%", "Discount"]])]) == []
    plans = payment_variants(
        [
            ContextTable(
                "Payment Plan",
                [
                    ["Installment", "Payment", "Milestone"],
                    ["Booking", "10%", "On Booking"],
                ],
            )
        ]
    )
    assert plans[0]["requires_review"]
    assert select_unambiguous_plan(plans) is None


def test_future_refresh_retains_a_single_plan_disagreement_and_incomplete_offers():
    base = b"<main><h1>QA</h1><table><tr><td>Down Payment:</td><td>5%</td></tr></table></main>"
    detail = b"""<main><h1>QA Payment Plan</h1><h2>Payment Plan</h2><table>
    <tr><th>Installment</th><th>Payment</th><th>Milestone</th></tr>
    <tr><td>Down Payment</td><td>4%</td><td>On Booking</td></tr>
    <tr><td>Final</td><td>96%</td><td>On Handover</td></tr></table></main>"""
    for body in (detail, detail.replace(b"96%", b"40%")):
        result = _combined_normalized(
            [
                FetchResult(
                    url="https://www.tanamiproperties.com/Projects/QA",
                    status=200,
                    retrieved_at=datetime.now(UTC),
                    body=base,
                ),
                FetchResult(
                    url="https://www.tanamiproperties.com/Projects/QA-PaymentPlan",
                    status=200,
                    retrieved_at=datetime.now(UTC),
                    body=body,
                ),
            ],
            ManifestCandidate(1, "QA", "", ""),
        )
        assert any("down_payment_percentage" in reason for reason in result.conflicts)


def test_summary_retains_unit_applicability_and_does_not_invent_unknown_values():
    facts = summary_facts(
        [
            ContextTable(
                "Summary",
                [
                    ["Property Type:", "Townhouse"],
                    ["Unit type:", "2 to 4 BR"],
                    ["Size:", "1759 to 2946 SQ. FT."],
                    ["Property Type:", "Villa"],
                    ["Unit type:", "4 to 7 BR"],
                    ["Size:", "3282 to 9404 SQ. FT."],
                    ["Handover:", "Q4 - 2028"],
                    ["Down Payment:", "4%"],
                ],
            )
        ]
    )
    assert facts["bedrooms"] == ["2", "3", "4", "5", "6+"]
    assert facts["size_max"] == 9404
    assert facts["unit_summary_evidence"][0]["property_type"] == "Townhouse"
    unknown = summary_facts(
        [
            ContextTable(
                "Summary",
                [
                    ["Property Type:", "Apartment"],
                    ["Unit type:", "Will Be Updated Soon"],
                    ["Size:", "Various Sizes Available"],
                    ["Handover:", "Announcing Soon"],
                ],
            )
        ]
    )
    assert "bedrooms" not in unknown
    assert "unit_types" not in unknown
    assert "handover_year" not in unknown
    assert "size_min" not in unknown
