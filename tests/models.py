import string
from modelus import *

# example user model
KEY_LENGTH = 10
class Complex(Model):
    id = Field(String, primary_key=True)
    string = Field(String, required=True)
    email = Field(EmailAddress, required=True)
    generated = Field(String, required=True, minlength=KEY_LENGTH, maxlength=KEY_LENGTH, default_setter='generated_string')
    list = Field(List(String))
    ipv4_address = Field(IPV4Address)

    class Validator(Model.Validator):
        # provides the functionality for default_setter='generated_string'
        # see cerberus for more information on this
        # format for this is _{step}_{key}_{name}
        # where the step is normalize, key is 'default_setter', name is 'generated_string'
        def _normalize_default_setter_generated_string(self, document):
            return 'a' * KEY_LENGTH

# models with foreign keys
class ModelB(Model):
    id = Field(String, primary_key=True)
    value = Field(String)

class ModelA(Model):
    id = Field(String, primary_key=True)
    keys = Field(List(ForeignKey(ModelB, cascade=True)))
