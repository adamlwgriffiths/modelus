from datetime import date, datetime
from inspect import isclass
from ipaddress import IPv4Address, IPv6Address
from cerberus import TypeDefinition

class Field(object):
    def __init__(self, type, primary_key=False, **kwargs):
        self.type = type() if isclass(type) else type
        self.primary_key = primary_key
        self.schema = {**self.type.schema, **kwargs}
        if self.primary_key:
            self.schema['required'] = True

    def __set_name__(self, owner, name):
        self.name = name
        self.type.__set_name__(owner, name)

    def __set__(self, instance, value):
        value = self.type.set(instance, value)
        instance._data[self.name] = value

    def __get__(self, instance, value):
        value = instance._data.get(self.name)
        value = self.type.get(instance, value)
        # update the value incase it changed
        instance._data[self.name] = value
        return value

_types_mapping = {}
def register_types_mapping(data):
    _types_mapping.update(data)
def types_mapping():
    return _types_mapping


_rules = {}
def register_rules(data):
    _rules.update(data)
def rules():
    return _rules

class FieldTypeMeta(type):
    def __new__(metacls, name, bases, namespace, **kwargs):
        if 'types_mapping' in namespace:
            register_types_mapping(namespace['types_mapping'])
            #FieldType.types_mapping.update(namespace['types_mapping'])
        if 'rules' in namespace:
            register_rules(namespace['rules'])
        return super().__new__(metacls, name, bases, namespace, **kwargs)


class FieldType(object, metaclass=FieldTypeMeta):
    schema = None

    def __init__(self, **kwargs):
        self.schema.update(**kwargs)

    def __set_name__(self, owner, name):
        pass

    def set(self, instance, value):
        return value

    def get(self, instance, value):
        return value


class Boolean(FieldType):
    schema = {'type': 'boolean'}

class Number(FieldType):
    schema = {'type': 'number'}

class Integer(FieldType):
    schema = {'type': 'integer'}

class Float(FieldType):
    schema = {'type': 'float'}

class String(FieldType):
    schema = {'type': 'string'}

class EmailAddress(FieldType):
    EMAIL_REGEX = '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    schema = {'type': 'string', 'regex': EMAIL_REGEX}

class Date(FieldType):
    schema = {'type': 'date'}

class DateTime(FieldType):
    schema = {'type': 'datetime'}

class IPAddress(FieldType):
    schema = {'type': 'ipaddress'}
    types_mapping = {'ipaddress': TypeDefinition('ipaddress', (IPv4Address, IPv6Address), ())}
    # dictionary of: <cerberus type name>: [to bytes, from bytes]
    rules = {'ipaddress': [lambda x: str(x), lambda x: ip_address(x.decode('utf-8'))]}

class IPV4Address(FieldType):
    schema = {'type': 'ipv4address'}
    types_mapping = {'ipv4address': TypeDefinition('ipv4address', (IPv4Address,), ())}
    rules = {'ipv4address': [lambda x: str(x), lambda x: IPv4Address(x.decode('utf-8'))]}


class IPV6Address(FieldType):
    schema = {'type': 'ipv6address'}
    types_mapping = {'ipv6address': TypeDefinition('ipv6address', (IPv6Address,), ())}
    rules = {'ipv6address': [lambda x: str(x), lambda x: IPv6Address(x.decode('utf-8'))]}


class List(FieldType):
    schema = {'type': 'list'}

    def __init__(self, type, **kwargs):
        self.type = type() if isclass(type) else type
        if self.type.schema['type'] in ['list', 'set']:
            raise TypeError('Container fields are not nestable')
        super().__init__(schema=self.type.schema, **kwargs)

    def __set_name__(self, owner, name):
        self.type.__set_name__(owner, name)

    def set(self, instance, value):
        return [self.type.set(instance, item) for item in value]

    def get(self, instance, value):
        return [self.type.get(instance, item) for item in value]

class Set(FieldType):
    schema = {'type': 'set'}

    def __init__(self, type, **kwargs):
        self.type = type() if isclass(type) else type
        if self.type.schema['type'] in ['list', 'set']:
            raise TypeError('Container fields are not nestable')
        super().__init__(schema=self.type.schema, **kwargs)

    def __set_name__(self, owner, name):
        self.type.__set_name__(owner, name)

    def set(self, instance, value):
        return {self.type.set(instance, item) for item in value}

    def get(self, instance, value):
        return {self.type.get(instance, item) for item in value}

class ForeignKey(FieldType):
    schema = {'type': 'string', 'coerce': 'primary_key'}

    def __init__(self, type, cascade=True, **kwargs):
        '''cascade indicates that when deleting this model, the linked model should be deleted too.
        '''
        from remodel.model import model
        super().__init__(**kwargs)
        self.type = type
        self.cascade = cascade

    def __set_name__(self, owner, name):
        # register the foreign key cascade with the owner
        if self.cascade:
            cascade = (name, self.type)
            owner._foreign_key_cascades.add(cascade)

    def get(self, instance, value):
        if not isinstance(value, self.type):
            value = instance.db.load(self.type, value)
        return value

    # TODO: when set, add a value to the foreign model
    # TODO: when target model deleted, load the incoming foreign key fields, remove self, and resave
    # if invalid, it will throw an error
    # TODO: when built, add a schema value for this field in the target class


class AutoInteger(FieldType):
    schema = {'type': 'integer'}
    # TODO:
