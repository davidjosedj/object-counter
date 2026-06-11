# NIQ Innovation Enablement - Object Counter

A Flask API that takes an image and a confidence threshold, runs object detection on it and returns how many objects were found grouped by class.

The project follows Hexagonal Architecture and is split into three layers:
- entrypoints - the Flask API that receives requests
- domain - the business logic
- adapters - connects to the ML model and database

---

## Prerequisites

- Python 3.10 or higher
- Docker (only needed for production mode with TF Serving + MongoDB/PostgreSQL)
- Make

---

## Quick Start

Step 1 - install dependencies
```bash
make setup
source .venv/bin/activate
export PYTHONPATH=.
```

Step 2 - run the app (no Docker needed)
```bash
make run
```
This uses a fake detector so you can test the API without any ML model running.

Step 3 - run with real predictions (no Docker needed)
```bash
make run-local
```
First run will download the HuggingFace model automatically, may take a few minutes.

Step 4 - run tests
```bash
make test
```

---

## Production Setup (requires Docker)

First download the model:
```bash
make model
```

Then start the services:
```bash
make tfserving
make mongo
```
or if you want PostgreSQL instead of MongoDB:
```bash
make postgres
```

Then run the app:
```bash
make run-prod
make run-prod-postgres
```

---

## Manual Setup (without Make)

Unix:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.
```

Windows PowerShell:
```powershell
python3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$Env:PYTHONPATH = "."
```

Model download (Unix only):
```bash
mkdir -p tmp/model/ssd_mobilenet_v2/1
curl -L -o tmp/model.tar.gz \
  http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v2_coco_2018_03_29.tar.gz
tar -xzvf tmp/model.tar.gz -C tmp/model
mv tmp/model/ssd_mobilenet_v2_coco_2018_03_29/saved_model/saved_model.pb tmp/model/ssd_mobilenet_v2/1
chmod -R 777 tmp/model
rm tmp/model.tar.gz
rm -rf tmp/model/ssd_mobilenet_v2_coco_2018_03_29
```

After download you should have this structure:
```
tmp/model/ssd_mobilenet_v2/1/saved_model.pb
```

TensorFlow Serving

Unix:
```bash
docker run --rm -d \
    --name=tfserving \
    -p 8501:8501 \
    --mount type=bind,source=$(pwd)/tmp/model,target=/models \
    -e MODEL_NAME=ssd_mobilenet_v2 \
    tensorflow/serving
```

Windows PowerShell:
```powershell
docker run --rm -d `
    --name=tfserving `
    -p 8501:8501 `
    -v "$pwd\tmp\model:/models" `
    -e MODEL_NAME=ssd_mobilenet_v2 `
    tensorflow/serving
```

MongoDB:
```bash
docker run --rm --name test-mongo -p 27017:27017 -d mongo:latest
```

PostgreSQL:
```bash
docker run --rm --name test-postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=prod_counter \
  -p 5432:5432 -d postgres:15
```

Note: on Windows replace localhost with 127.0.0.1 if you have connection issues.

---

## Running Modes

- make run - dev mode, uses a fake detector and stores data in memory
- make run-local - uses HuggingFace for real predictions, stores data in memory
- make run-prod - production mode with TF Serving and MongoDB
- make run-prod-postgres - production mode with TF Serving and PostgreSQL

---

## Environment Variables

- ENV - dev, local or prod (default: dev)
- MODEL_NAME - TF Serving model name (default: ssd_mobilenet_v2)
- DB_TYPE - mongo or postgres (default: mongo)
- MONGO_HOST - MongoDB host (default: localhost)
- POSTGRES_HOST - PostgreSQL host (default: localhost)
- POSTGRES_PASSWORD - PostgreSQL password (default: empty)

---

## API Endpoints

### POST /object-count
Returns how many objects were detected in the image grouped by class, plus the total count since the app started.

```bash
curl -F "threshold=0.9" -F "file=@resources/images/boy.jpg" http://127.0.0.1:5000/object-count
```

Response:
```json
{
  "current_objects": [{"object_class": "person", "count": 1}],
  "total_objects":   [{"object_class": "person", "count": 5}]
}
```

### POST /object-predictions
Returns the full list of detected objects with class name, confidence score and bounding box for each one.

```bash
curl -F "threshold=0.5" -F "file=@resources/images/boy.jpg" http://127.0.0.1:5000/object-predictions
```

Response:
```json
[
  {
    "class_name": "person",
    "score": 0.987,
    "box": {"xmin": 0.1, "ymin": 0.2, "xmax": 0.5, "ymax": 0.9}
  }
]
```

---

## Running Tests

```bash
make test
# or
make test-verbose
# or with coverage report
make test-coverage
```

---

## Task 3 - Code Review

After going through the code and running the app I noticed a few issues:

1. MongoDB was opening a new connection on every request which is not good for performance
2. The domain models had no way to be converted to JSON so the API responses were failing
3. The tests in the entrypoints folder were not being picked up by pytest because of a missing __init__.py file

---

## Task 4 - Improvements

I fixed the 3 issues from Task 3:

1. MongoClient is now created once when the class starts and reused for all requests
2. Added a to_dict() method to each domain model so Flask can convert them to JSON
3. Added the missing __init__.py to tests/entrypoints so pytest picks up the tests

I also wrote a couple of tests for the new /object-predictions endpoint to make sure it returns the right response.

---

## Task 5 - Multiple Models

Currently the app only supports one model at a time set via an environment variable. To support multiple models at the same time I would make these changes:

- Accept the model name as a request parameter so the caller decides which model to use
- Load all models once when the app starts and keep them ready, instead of loading on every request
- TF Serving supports multiple models through a config file so all models can run in one Docker container
- The business logic would not need to change at all since the ObjectDetector interface stays the same

---

## Task 6b - Different ML Frameworks

The original app only works with TensorFlow via TF Serving which requires Docker. I added a HuggingFaceObjectDetector that uses PyTorch so you can get real predictions without any Docker setup.

To use it just run:
```bash
make run-local
```

The three detectors in the app now are:
- FakeObjectDetector - for development and testing
- HuggingFaceObjectDetector - for real predictions without Docker
- TFSObjectDetector - for production with TF Serving

The good thing is I only had to add one new class. Nothing else in the app changed because the ObjectDetector interface handles the swap cleanly.
