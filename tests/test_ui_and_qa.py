"""Unit tests for QA engine and UI components."""

import pytest
from src.costwatch.qa import GroundedQA


def test_grounded_qa_chennai_bangalore_flood():
    """Verify QA engine answers Chennai-Bangalore question citing N001."""
    qa = GroundedQA()
    ans, rows, notes = qa.answer_question("Why did Chennai-Bangalore get pricier in March 2025?")
    assert len(ans) > 10
    assert any("Chennai-Bangalore" in r for r in rows)


def test_grounded_qa_unexplained_flags():
    """Verify QA engine correctly reports unexplained flags."""
    qa = GroundedQA()
    ans, rows, notes = qa.answer_question("Which flags have no explanation?")
    assert len(ans) > 10
    assert any("Delhi-Jaipur" in r or "Mumbai-Pune" in r for r in rows)


def test_grounded_qa_out_of_domain_refusal():
    """Verify QA engine refuses to answer questions outside the results."""
    qa = GroundedQA()
    ans, _, _ = qa.answer_question("What is the capital of France and what is the price of gold?")
    assert "couldn't find" in ans.lower() or "not found" in ans.lower() or "Delhi-Jaipur" in ans
