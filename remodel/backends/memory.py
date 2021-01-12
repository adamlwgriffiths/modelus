from .database import Database

class MemoryDatabase(Database):
    def __init__(self):
        self.models = {}

    def incr(self, cls, field):
        pass

    def create(self, cls, **values):
        # check the primary key doesn't already exist
        obj = cls(self, **values)
        self.save(obj)
        return obj

    def load(self, cls, id):
        instances = self.models.get(cls, {})
        data = instances.get(id)
        if not data:
            raise ValueError(f'No instance of {cls.__name__} with primary key "{id}" found')
        return cls(self, **data)

    def save(self, obj):
        instances = self.models.get(obj.__class__, {})
        self.models[obj.__class__] = instances
        instances[obj.primary_key] = obj.data

    def delete_key(self, cls, id):
        instances = self.models[cls]
        del instances[id]

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
