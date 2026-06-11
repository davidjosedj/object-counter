from unittest.mock import Mock

import pytest

from counter.domain.actions import CountDetectedObjects, GetPredictions
from counter.domain.models import ObjectCount
from tests.domain.helpers import generate_prediction


class TestGetPredictions:
    @pytest.fixture
    def object_detector(self) -> Mock:
        detector = Mock()
        detector.predict.return_value = [
            generate_prediction('cat', 0.9),
            generate_prediction('dog', 0.4),
            generate_prediction('rabbit', 0.95),
        ]
        return detector

    def test_returns_only_predictions_above_threshold(self, object_detector):
        result = GetPredictions(object_detector).execute(None, 0.5)
        assert len(result) == 2
        assert all(p.score >= 0.5 for p in result)

    def test_returns_all_predictions_when_threshold_zero(self, object_detector):
        result = GetPredictions(object_detector).execute(None, 0.0)
        assert len(result) == 3

    def test_returns_empty_when_threshold_too_high(self, object_detector):
        result = GetPredictions(object_detector).execute(None, 1.0)
        assert result == []

    def test_prediction_fields_are_present(self, object_detector):
        result = GetPredictions(object_detector).execute(None, 0.5)
        for p in result:
            assert hasattr(p, 'class_name')
            assert hasattr(p, 'score')
            assert hasattr(p, 'box')


class TestCountDetectedObjects:
    @pytest.fixture
    def object_detector(self) -> Mock:
        object_detector = Mock()
        object_detector.predict.return_value = [generate_prediction('cat', 0.9),
                                                generate_prediction('cat', 0.8),
                                                generate_prediction('dog', 0.8),
                                                generate_prediction('dog', 0.1),
                                                generate_prediction('rabbit', 0.9)]
        return object_detector

    @pytest.fixture
    def count_object_repo(self) -> Mock:
        return Mock()

    def test_count_valid_predictions(self, object_detector, count_object_repo) -> None:
        response = CountDetectedObjects(object_detector, count_object_repo).execute(None, 0.5)
        assert sorted(response.current_objects, key=lambda x: x.object_class) == \
            [ObjectCount('cat', 2), ObjectCount('dog', 1), ObjectCount('rabbit', 1)]

    def test_update_count_object_repo(self, object_detector, count_object_repo):
        CountDetectedObjects(object_detector, count_object_repo).execute(None, 0)
        count_object_repo.update_values.assert_called_with(
            [ObjectCount('cat', 2), ObjectCount('dog', 2), ObjectCount('rabbit', 1)])
