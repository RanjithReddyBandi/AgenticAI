
import json
from pathlib import Path
import pytest

from evaluation.models import EvaluationCase, ToolEvent
from evaluation.metrics.deterministic import evaluate_deterministic

TEST_DATASETS_DIR = Path(__file__).parent.parent / 'datasets'

@pytest.fixture
def valid_case():
    return EvaluationCase(
        id='test',
        query='Find a jacket under .',
        checks={
            'max_price': 100,
            'min_recommendations': 1,
            'required_tools': ['CatalogSearch', 'PricingAPI'],
        },
        fairness_group=None,
        protected_attribute=None,
    )

@pytest.fixture
def mock_tool_events():
    return [
        ToolEvent(name='CatalogSearch', input={'query': 'Find a jacket under .'}, output=[{'product_id': '1', 'name': 'Jacket'}], error=None),
        ToolEvent(name='PricingAPI', input={'product_id': '1'}, output={'product_id': '1', 'price': 90.0, 'currency': 'USD', 'discount': 'No discount'}, error=None),
        ToolEvent(name='InventoryAPI', input={'product_id': '1'}, output={'product_id': '1', 'in_stock': True, 'quantity': 5}, error=None),
        ToolEvent(name='ReviewAPI', input={'product_id': '1'}, output={'product_id': '1', 'average_rating': 4.2, 'review_count': 10, 'sentiment_summary': 'positive sentiment'}, error=None),
    ]

@pytest.fixture
def mock_response():
    return {
        'recommendations': [
            {
                'product_id': '1',
                'name': 'Jacket',
                'price': '.00',
                'discount': 'No discount',
                'stock': True,
                'reviews': '4.2/5 average; positive sentiment',
            }
        ],
        'comparisons': [],
        'explanation': 'Found a jacket under .',
    }


def test_deterministic_security_pii_clean(valid_case, mock_response, mock_tool_events):
    result = evaluate_deterministic(valid_case, mock_response, mock_tool_events)
    pii_result = next(r for r in result if r.metric_id == 'security.pii')
    assert pii_result.score == 1.0
    assert pii_result.passed is True
    assert 'No PII-like secrets' in pii_result.rationale


def test_deterministic_security_pii_leaked(valid_case, mock_response, mock_tool_events):
    modified_response = dict(mock_response)
    modified_response['explanation'] = 'User password is secret123!'
    result = evaluate_deterministic(valid_case, modified_response, mock_tool_events)
    pii_result = next(r for r in result if r.metric_id == 'security.pii')
    assert pii_result.score == 0.0
    assert pii_result.passed is False
    assert 'PII pattern matched' in pii_result.rationale


def test_deterministic_security_code_clean(valid_case, mock_response, mock_tool_events):
    result = evaluate_deterministic(valid_case, mock_response, mock_tool_events)
    code_result = next(r for r in result if r.metric_id == 'security.code')
    assert code_result.score == 1.0
    assert code_result.passed is True
    assert 'No code-like content' in code_result.rationale


def test_deterministic_security_code_leaked(valid_case, mock_response, mock_tool_events):
    modified_response = dict(mock_response)
    modified_response['explanation'] = 'Here is the code: `def bad(): pass`'
    result = evaluate_deterministic(valid_case, modified_response, mock_tool_events)
    code_result = next(r for r in result if r.metric_id == 'security.code')
    assert code_result.score == 0.0
    assert code_result.passed is False
    assert 'Code pattern matched' in code_result.rationale


def test_deterministic_quality_assertions_valid(valid_case, mock_response, mock_tool_events):
    result = evaluate_deterministic(valid_case, mock_response, mock_tool_events)
    assertions_result = next(r for r in result if r.metric_id == 'quality.assertions')
    assert assertions_result.score == 1.0
    assert assertions_result.passed is True
    assert 'required fields' in assertions_result.rationale.lower()


def test_deterministic_quality_assertions_missing_fields(valid_case, mock_response, mock_tool_events):
    modified_response = dict(mock_response)
    modified_response['recommendations'] = [{'product_id': '1'}]
    result = evaluate_deterministic(valid_case, modified_response, mock_tool_events)
    assertions_result = next(r for r in result if r.metric_id == 'quality.assertions')
    assert assertions_result.score == 0.0
    assert assertions_result.passed is False


def test_deterministic_trajectory_tool_selection_match(valid_case, mock_response, mock_tool_events):
    result = evaluate_deterministic(valid_case, mock_response, mock_tool_events)
    traj_result = next(r for r in result if r.metric_id == 'trajectory.tool_selection')
    assert traj_result.score == 1.0
    assert traj_result.passed is True
    assert 'All required tools' in traj_result.rationale


def test_deterministic_trajectory_tool_selection_missing(valid_case, mock_response, mock_tool_events):
    reduced_events = [mock_tool_events[0], mock_tool_events[2]]
    result = evaluate_deterministic(valid_case, mock_response, reduced_events)
    traj_result = next(r for r in result if r.metric_id == 'trajectory.tool_selection')
    assert traj_result.score == 0.0
    assert traj_result.passed is False
    assert 'Missing required tools' in traj_result.rationale


def test_deterministic_trajectory_tool_selection_no_required(valid_case, mock_response, mock_tool_events):
    case_no_tools = EvaluationCase(
        id='test2',
        query='Find anything.',
        checks={},
        fairness_group=None,
        protected_attribute=None,
    )
    result = evaluate_deterministic(case_no_tools, mock_response, mock_tool_events)
    traj_result = next(r for r in result if r.metric_id == 'trajectory.tool_selection')
    assert traj_result.score is None
    assert traj_result.passed is None
    assert 'Skipped' in traj_result.rationale


def test_dataset_loading():
    dataset_path = TEST_DATASETS_DIR / 'smoke.jsonl'
    cases = []
    with open(dataset_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(EvaluationCase(**json.loads(line)))
    assert len(cases) == 5
    assert cases[0].id == 'budget_wallet'
    assert 'max_price' in cases[0].checks
