"""Tests for scoring service."""
import pytest
from app.services.scoring import compute_fairness_score, generate_explanation


def test_compute_fairness_score_balanced():
    """Test fairness score for balanced trade."""
    fairness, diff, desc = compute_fairness_score(10000, 10000)
    assert fairness == 100
    assert diff == 0
    assert "perfectly balanced" in desc


def test_compute_fairness_score_unbalanced():
    """Test fairness score for unbalanced trade."""
    fairness, diff, desc = compute_fairness_score(10000, 12000)
    assert fairness < 100
    assert diff == 2000
    assert "receives" in desc.lower()


def test_compute_fairness_score_proposer_gives_more():
    """Test fairness score when proposer gives more."""
    fairness, diff, desc = compute_fairness_score(12000, 10000)
    assert fairness < 100
    assert diff == -2000
    assert "gives" in desc.lower()


def test_generate_explanation():
    """Test explanation generation."""
    explanation = generate_explanation(
        fairness=85,
        volatility=60,
        liquidity=70,
        offer_total=10000,
        want_total=10500,
        diff=500,
        diff_desc="Proposer receives $5.00 more value"
    )
    
    assert len(explanation) >= 2
    assert any("$100.00" in line for line in explanation)
    assert any("$105.00" in line for line in explanation)


def test_generate_explanation_with_warnings():
    """Test explanation with volatility and liquidity warnings."""
    explanation = generate_explanation(
        fairness=50,
        volatility=30,
        liquidity=35,
        offer_total=10000,
        want_total=15000,
        diff=5000,
        diff_desc="Proposer receives $50.00 more value"
    )
    
    assert any("volatile" in line.lower() for line in explanation)
    assert any("harder to trade" in line.lower() or "market activity" in line.lower() for line in explanation)
    assert any("adjust" in line.lower() for line in explanation)

