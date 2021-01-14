from .database import Database
from cerberedis import CerbeRedis
from modelus.fields import rules

class RedisDatabase(Database):
    def __init__(self, redis):
        self.redis = redis
        self.db = CerbeRedis(self.redis, rules())

    def create(self, cls, **values):
        # check the primary key doesn't already exist
        obj = cls(self, **values)
        self.save(obj)
        return obj

    def load(self, cls, id):
        data = self.db.load(cls.__name__, cls.schema, id)
        if not data:
            raise ValueError(f'No instance of {cls.__name__} with primary key "{id}" found')
        return cls(self, **data)

    def save(self, obj):
        self.db.save(obj.__class__.__name__, obj.schema, obj.primary_key, obj.data)

    def delete_key(self, cls, id):
        key = self.db.key(cls.__name__, id)
        self.redis.delete(key)

    def delete(self, obj):
        # recursively follow foreign keys with cascade set and delete those too
        for field, model in obj._foreign_key_cascades:
            objects = getattr(obj, field)
            # the key may be a list, so convert everything to a list
            if not isinstance(objects, (set, list)):
                objects = [objects]

            for object in objects:
                self.delete(object)

        # delete the object itself
        self.delete_key(obj.__class__, obj.primary_key)
