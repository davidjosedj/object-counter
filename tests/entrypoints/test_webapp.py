import io
import json
from pathlib import Path

import pytest

from counter.domain.models import Prediction, Box, ObjectCount, CountResponse
from counter.entrypoints.webapp import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def image_path():
    return Path(__file__).parent.parent.parent / "resources" / "images" / "boy.jpg"


def _post_image(client, endpoint, image_path, threshold='0.5'):
    with open(image_path, 'rb') as f:
        data = {'threshold': threshold, 'file': (io.BytesIO(f.read()), 'test.jpg')}
    return client.post(endpoint, data=data, content_type='multipart/form-data', buffered=True)


# --- /object-count tests ---

def test_object_count_returns_200(client, image_path):
    response = _post_image(client, '/object-count', image_path)
    assert response.status_code == 200


def test_object_count_response_structure(client, image_path):
    response = _post_image(client, '/object-count', image_path)
    body = json.loads(response.data)
    assert 'current_objects' in body
    assert 'total_objects' in body


# --- /object-predictions tests ---

def test_object_predictions_returns_200(client, image_path):
    response = _post_image(client, '/object-predictions', image_path)
    assert response.status_code == 200


def test_object_predictions_returns_list(client, image_path):
    response = _post_image(client, '/object-predictions', image_path)
    body = json.loads(response.data)
    assert isinstance(body, list)
    assert 'class_name' in body[0]
    assert 'score' in body[0]
    assert 'box' in body[0]
