
class Database(object):
    def incr(self, cls, field):
        raise NotImplementedError

    def create(self, cls, **values):
        raise NotImplementedError

    def load(self, cls, id):
        raise NotImplementedError

    def save(self, obj):
        raise NotImplementedError

    def delete(self, obj):
        raise NotImplementedError
