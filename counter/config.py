import os

from counter.adapters.count_repo import CountMongoDBRepo, CountInMemoryRepo, CountPostgresRepo
from counter.adapters.object_detector import TFSObjectDetector, FakeObjectDetector, HuggingFaceObjectDetector
from counter.domain.actions import CountDetectedObjects, GetPredictions


ENV = os.environ.get('ENV', 'dev')


def _get_detector():
    if ENV == 'prod':
        return TFSObjectDetector(
            host=os.environ.get('TFS_HOST', 'localhost'),
            port=os.environ.get('TFS_PORT', 8501),
            model=os.environ.get('MODEL_NAME', 'ssd_mobilenet_v2')
        )
    if ENV == 'local':
        return HuggingFaceObjectDetector(
            model=os.environ.get('HF_MODEL', 'facebook/detr-resnet-50')
        )
    return FakeObjectDetector()


def _get_repo():
    if ENV == 'prod':
        db_type = os.environ.get('DB_TYPE', 'mongo')
        if db_type == 'postgres':
            return CountPostgresRepo(
                host=os.environ.get('POSTGRES_HOST', 'localhost'),
                port=int(os.environ.get('POSTGRES_PORT', 5432)),
                database=os.environ.get('POSTGRES_DB', 'prod_counter'),
                user=os.environ.get('POSTGRES_USER', 'postgres'),
                password=os.environ.get('POSTGRES_PASSWORD', '')
            )
        return CountMongoDBRepo(
            host=os.environ.get('MONGO_HOST', 'localhost'),
            port=int(os.environ.get('MONGO_PORT', 27017)),
            database=os.environ.get('MONGO_DB', 'prod_counter')
        )
    return CountInMemoryRepo()


def get_count_action() -> CountDetectedObjects:
    return CountDetectedObjects(_get_detector(), _get_repo())


def get_predictions_action() -> GetPredictions:
    return GetPredictions(_get_detector())
