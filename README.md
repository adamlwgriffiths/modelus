# Modelus


Declarative data types using [Cerberus](https://github.com/pyeve/cerberus) for schemas.

## Features

* Declarative data model
* De-coupled backends, the following are included:
  * Redis - Using [Cerberedis](https://github.com/adamlwgriffiths/cerberedis).
  * In-memory - For debugging, testing, and performance
* Basic foreign keys
* Cerberus schemas remove the need for bytes->string encode/decode

The code is simple to understand.
The decoupled backend makes it perfect as a base implementation for other ORMs
or to simply understand how they are implemented.

This code is not intended to be highly-performant, instead it provides sufficient performance
for the basic use case of loading simple models with none-to-little relationships.


## Installation

    $ pip install modelus


## Example

A basic example:

```
>>> from modelus import Model, Field, String, List
>>> from modelus.backends.memory import MemoryDatabase
>>>
>>> class MyModel(Model):
...     id = Field(String, primary_key=True)
...     values = Field(List(String), required=True)
...
>>> db = MemoryDatabase()
>>> mymodel = db.create(MyModel, id='abc', values=['a', 'b', 'c'])
>>> # reload
>>> mymodel = db.load(MyModel, 'abc')
>>> print(mymodel.data)
{'id': 'abc', 'values': ['a', 'b', 'c']}
```

A more complex example:

```
import string
from secrets import choice
from modelus import Model, Field, String, EmailAddress, List
from modelus.backends.redis import RedisDatabase
from redis import Redis
import bcrypt

KEY_LENGTH = 10

class User(Model):
    username = Field(String, primary_key=True)
    password = Field(String, required=True)
    email = Field(EmailAddress, required=True)
    key = Field(String, required=True, minlength=KEY_LENGTH, maxlength=KEY_LENGTH, default_setter='random_string')
    addresses = Field(List(String))

    class Validator(Model.Validator):
        def _normalize_default_setter_random_string(self, document):
            def generate_string(size, chars):
                return ''.join([choice(chars) for _ in range(size)])

            valid_chars = ''.join([string.ascii_lowercase, string.digits])
            return generate_string(KEY_LENGTH, valid_chars)

    @classmethod
    def hash_password(cls, password):
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        return hashed.decode('utf-8')


redis = Redis()
db = RedisDatabase(redis)
user = db.create(User,
    username='Bob',
    password=User.hash_password('password'),
    email='bob@example.com',
    addresses=['123 Fake Street, Imagination Land, 1234']
)
# user will be defined now because the model was saved
print(user.key)
```

## Usage

### Models

All data types are specified as a sub-class of Model.

Each field is specified as a class attribute which is a Field object containing a field type.

The backend must be provided to the Model as this used by the ForeignKey functionality.

For example:

```
>>> from modelus import Model, Field, String, List
>>> from modelus.backends.memory import MemoryDatabase
>>>
>>> class MyModel(Model):
...     id = Field(String, primary_key=True)
...     values = Field(List(String), required=True)
...
>>> db = MemoryDatabase()
>>> mymodel = db.create(MyModel, id='abc', values=['a', 'b', 'c'])
>>> # reload
>>> mymodel = db.load(MyModel, 'abc')
>>> print(mymodel.data)
{'id': 'abc', 'values': ['a', 'b', 'c']}
```

It is possible to pass in None as the database if you don't intened to save the model.
In this case you can simply use the obj.data property to get the serialised model data.

```
>>> mymodel = MyModel(None, id='abc', values=['a', 'b', 'c'])
>>> print(mymodel.data)
{'id': 'abc', 'values': ['a', 'b', 'c']}
```

### Field validation and defaults

Parameters to fields are simply passed through to the Cerberus schema.
[See this documentation](https://docs.python-cerberus.org/en/stable/validation-rules.html) for more Cerberus validation rules.

Cerberus validator rules can be added by adding a child class called "Validator" to your model definition.

```
from modelus import Model, Field, String

class MyModel(Model):
    # default_setter is a cerberus attribute which will set the value if it is not already
    # but only on save
    # the value may be either a function or a string
    # if the value is a string, the function must be defined in the Validator class as _normalize_default_setter_<name>
    # https://docs.python-cerberus.org/en/stable/normalization-rules.html
    value = Field(String, default_setter='generated_string')

    class Validator(Model.Validator):
        def _normalize_default_setter_generated_string(self, document):
            return 'abcdefg'
```


### Foreign Keys

It is recommended if there are relationships that you manage themselves as foreign key support is rudimentary.

Field Attributes are passed through the [Cerberus](https://github.com/pyeve/cerberus) as the field schema.
The only exception is the primary_key field, which is used

```
    >>> from modelus import Model, Field, String, Integer, List, ForeignKey
    >>> from modelus.backends.memory import MemoryDatabase
    >>>
    >>> class ModelB(Model):
    ...     id = Field(String, primary_key=True)
    ...     value = Field(Integer)
    ...
    >>> class ModelA(Model):
    ...     id = Field(String, primary_key=True)
    ...     keys = Field(List(ForeignKey(ModelB, cascade=True)))
    ...
    >>> db = MemoryDatabase()
    >>> modelb_1 = db.create(ModelB, id='1', value=1)
    >>> modelb_2 = db.create(ModelB, id='2', value=2)
    >>>
    >>> modela = db.create(ModelA, id='1', keys=[modelb_1, modelb_2])
    >>> print(modela.keys[0].value)
    1
```

Defining a ForeignKey field with cascade=True will cause the linked model to be deleted when the current model is deleted.

```
>>> db.load(ModelB, '1')
<__main__.ModelB object at 0x7ffbe215ebb0>
>>> # delete modela
>>> # modela will delete the referenced foreign keys
>>> db.delete(modela)
>>> db.load(ModelB, '1')
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/adam/Workspace/modelus/modelus/backends/memory.py", line 20, in load
    raise ValueError(f'No instance of {cls.__name__} with primary key "{id}" found')
ValueError: No instance of ModelB with primary key "1" found
```

### Adding new Field Types

New field types should be as simple as sub-classing FieldType.

The type must define a schema, which follows Cerberus.

If the type is unsupported by Cerberus, you must also add types_mapping and rules fields
which is automatically added to the Validator instance.

Again, this follows the Cerberus types_mapping format.
The rules field follows the Cerberedis rules format which is a list of 2 lambdas.
The first converts the value to bytes, the second from bytes.

The following is a field type that is provided by ReModel, that is not supported by Cerberus.

```
class IPV4Address(FieldType):
    schema = {'type': 'ipv4address'}
    types_mapping = {'ipv4address': TypeDefinition('ipv4address', (IPv4Address,), ())}
    rules = {'ipv4address': [lambda x: str(x), lambda x: IPv4Address(x.decode('utf-8'))]}
```


## Limitations

* Containers cannot be nested. Ie. lists and sets cannot contain lists, sets, or models.
* Foreign keys
  * Do not support reverse lookups
  * Deleting a referenced model does not update the outgoing foreign key.


## Future Work

* Expand Foreign Keys
  * Support reverse look-up of foreign keys
  * Removal foreign key when deleting child model, resave before deletion will trigger validation
* Partial text search
* Index fields
* Improve README
