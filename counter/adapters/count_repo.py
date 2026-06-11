from typing import List

import psycopg2
from pymongo import MongoClient

from counter.domain.models import ObjectCount
from counter.domain.ports import ObjectCountRepo


class CountInMemoryRepo(ObjectCountRepo):

    def __init__(self):
        self.store = dict()

    def read_values(self, object_classes: List[str] = None) -> List[ObjectCount]:
        if object_classes is None:
            return list(self.store.values())
        return [self.store.get(object_class) for object_class in object_classes]

    def update_values(self, new_values: List[ObjectCount]):
        for new_object_count in new_values:
            key = new_object_count.object_class
            try:
                stored_object_count = self.store[key]
                self.store[key] = ObjectCount(key, stored_object_count.count + new_object_count.count)
            except KeyError:
                self.store[key] = ObjectCount(key, new_object_count.count)


class CountMongoDBRepo(ObjectCountRepo):

    def __init__(self, host, port, database):
        self.__client = MongoClient(host, port)
        self.__database = database

    def __get_counter_col(self):
        return self.__client[self.__database].counter

    def read_values(self, object_classes: List[str] = None) -> List[ObjectCount]:
        counter_col = self.__get_counter_col()
        query = {"object_class": {"$in": object_classes}} if object_classes else None
        return [ObjectCount(c['object_class'], c['count']) for c in counter_col.find(query)]

    def update_values(self, new_values: List[ObjectCount]):
        counter_col = self.__get_counter_col()
        for value in new_values:
            counter_col.update_one(
                {'object_class': value.object_class},
                {'$inc': {'count': value.count}},
                upsert=True
            )


class CountPostgresRepo(ObjectCountRepo):

    def __init__(self, host, port, database, user, password):
        self.__conn_params = {
            'host': host, 'port': port, 'dbname': database,
            'user': user, 'password': password
        }
        self.__ensure_table()

    def __get_connection(self):
        return psycopg2.connect(**self.__conn_params)

    def __ensure_table(self):
        with self.__get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS object_counts (
                        object_class VARCHAR(255) PRIMARY KEY,
                        count INTEGER NOT NULL DEFAULT 0
                    )
                """)

    def read_values(self, object_classes: List[str] = None) -> List[ObjectCount]:
        with self.__get_connection() as conn:
            with conn.cursor() as cur:
                if object_classes:
                    cur.execute(
                        "SELECT object_class, count FROM object_counts WHERE object_class = ANY(%s)",
                        (object_classes,)
                    )
                else:
                    cur.execute("SELECT object_class, count FROM object_counts")
                return [ObjectCount(row[0], row[1]) for row in cur.fetchall()]

    def update_values(self, new_values: List[ObjectCount]):
        with self.__get_connection() as conn:
            with conn.cursor() as cur:
                for value in new_values:
                    cur.execute("""
                        INSERT INTO object_counts (object_class, count)
                        VALUES (%s, %s)
                        ON CONFLICT (object_class)
                        DO UPDATE SET count = object_counts.count + EXCLUDED.count
                    """, (value.object_class, value.count))
