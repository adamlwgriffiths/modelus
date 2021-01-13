from datetime import datetime
from cerberus import Validator, TypeDefinition
from modelus.fields import Field, FieldType, types_mapping


_models = {}
def register_model(model):
    _models[model.__class__.__name__] = model
def model(name):
    return _models[name]

class ModelMeta(type):
    def __new__(metacls, name, bases, namespace, **kwargs):
        def discover_fields():
            return {k:v for k,v in namespace.items() if isinstance(v, Field)}
        def determine_primary_key(fields):
            # ensure we have exactly one primary key
            # don't do this check for the base Model class
            if name != 'Model':
                primary_keys = [field_name for field_name, field in fields.items() if field.primary_key]
                if not len(primary_keys):
                    raise TypeError(f'{name} has no field specified as primary_key')
                if 1 < len(primary_keys):
                    raise TypeError(f'{name} has multiple fields specified as primary_key')
                return primary_keys[0]
        def create_schema():
            return {name: field.schema for name, field in fields.items()}
        def register_model_(cls):
            if name != 'Model':
                register_model(cls)

        fields = discover_fields()
        namespace['_fields'] = fields
        namespace['_primary_key'] = determine_primary_key(fields)
        namespace['schema'] = create_schema()
        #namespace['_foreign_key_fields'] = set()
        namespace['_foreign_key_cascades'] = set()

        cls = super().__new__(metacls, name, bases, namespace, **kwargs)
        register_model_(cls)
        return cls

class Model(object, metaclass=ModelMeta):
    class Validator(Validator):
        # load all the cerberus types that are defined in the FieldType classes
        types_mapping = {**Validator.types_mapping, **types_mapping()}

        # cerberus helpers for common coerce functions
        def _normalize_default_setter_utcnow(self, document):
            return datetime.utcnow()
        def _normalize_coerce_primary_key(self, value):
            if isinstance(value, Model):
                return value.primary_key
            return value

    def __init__(self, db, **values):
        self.db = db
        self._data = {}
        for k,v in values.items():
            setattr(self, k, v)

    @property
    def primary_key(self):
        return self._data.get(self._primary_key)

    @property
    def validator(self):
        validator_type = self.Validator if hasattr(self, 'Validator') else Validator
        return validator_type(self.schema)

    def validate(self):
        # apply transformation rules
        # validate the resulting document
        validator = self.validator
        document = validator.normalized(self._data)
        if not validator(document):
            raise ValueError(str(validator.errors))
        return document

    @property
    def data(self):
        data = self.validate()
        # update any values that were altered as part of normalisation
        self._data.update(data)
        return data
