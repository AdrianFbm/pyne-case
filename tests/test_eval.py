"""Evaluation suite for the Pyne agent.

Validates query results (DataFrames) rather than narrative text,
making tests nearly deterministic despite LLM non-determinism.
"""

import pytest
from settings import settings

# Override model before importing agent (which initialises the client at import time)
settings.llm_model = "claude-haiku-4-5-20251001"

from agent import ask


# ── Scalar / exact-value tests ──────────────────────────────────────────────


def test_customer_count():
    result = ask("How many customers are in the database?")
    assert result["data"] is not None
    value = result["data"].iloc[0, 0]
    assert int(value) == 200


def test_product_count():
    result = ask("How many products do we sell?")
    assert result["data"] is not None
    value = result["data"].iloc[0, 0]
    assert int(value) == 16


def test_order_count():
    result = ask("How many orders are there?")
    assert result["data"] is not None
    value = result["data"].iloc[0, 0]
    assert int(value) == 3000


def test_order_items_count():
    result = ask("What is the total number of order items?")
    assert result["data"] is not None
    value = result["data"].iloc[0, 0]
    assert int(value) == 6583


# ── Aggregation tests ───────────────────────────────────────────────────────


def test_top_3_products_by_revenue():
    result = ask("What are the top 3 products by revenue?")
    assert result["data"] is not None
    assert len(result["data"]) == 3


# ── Filtering / logic tests ─────────────────────────────────────────────────


def test_distinct_order_statuses():
    result = ask("How many distinct order statuses are there?")
    assert result["data"] is not None
    value = int(result["data"].iloc[0, 0])
    assert 3 <= value <= 6


def test_average_order_total():
    result = ask("What is the average order total?")
    assert result["data"] is not None
    value = float(result["data"].iloc[0, 0])
    assert value > 0


# ── Failure handling ─────────────────────────────────────────────────────────


def test_out_of_scope_question():
    result = ask("What's the weather like?")
    assert result["sql"] is None or result["sql"] == ""
    assert result["data"] is None
