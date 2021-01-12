import unittest
import string
from secrets import choice
from remodel import *
from models import User, ModelA, ModelB, KEY_LENGTH

class TestModels(unittest.TestCase):
    def test_no_primary_keys(self):
        with self.assertRaises(TypeError):
            class NoPrimaryKeys(Model):
                field_a = Field(String)
                field_b = Field(String)

    def test_multiple_primary_keys(self):
        with self.assertRaises(TypeError):
            class TooManyPrimaryKeys(Model):
                field_a = Field(String, primary_key=True)
                field_b = Field(String, primary_key=True)

    def test_single_primary_keys(self):
        class SinglePrimaryKeys(Model):
            field_a = Field(String, primary_key=True)
            field_b = Field(String)

    def test_model_and_fields(self):
        db = None
        model = User(db,
            username='abc',
            password='def', # please don't store plaintext passwords, this is just a test, don't copy this!
            email='abc@example.com',
            # don't set default
            addresses=['a', 'b']
        )
        self.assertEqual(model.primary_key, 'abc')
        self.assertEqual(model.username, 'abc')
        self.assertEqual(model.password, 'def')
        self.assertEqual(model.email, 'abc@example.com')
        # default is only set on create/save
        # as we aren't using a real db here, we don't test that here
        self.assertIsNone(model.key)
        self.assertEqual(model.addresses, ['a', 'b'])

        # check the serialised data
        d = model.data
        self.assertEqual(d['username'], 'abc')
        self.assertEqual(d['password'], 'def')
        self.assertEqual(d['email'], 'abc@example.com')
        self.assertEqual(d['key'], 'a' * KEY_LENGTH)
        self.assertEqual(d['addresses'], ['a', 'b'])

    def test_foreign_keys(self):
        db = None
        testb_a = ModelB(db, id='a', value='a')
        testb_b = ModelB(db, id='b', value='b')
        testb_c = ModelB(db, id='c', value='c')

        # create parent
        testa = ModelA(db, id='a', keys=[testb_a])

        self.assertEqual(len(testa.keys), 1)
        self.assertEqual(testa.keys[0].id, 'a')

        # add a new foreign key
        testa.keys.append(testb_b)

        self.assertEqual(len(testa.keys), 2)
        self.assertEqual(testa.keys[0].id, 'a')
        self.assertEqual(testa.keys[1].id, 'b')

        # check the serialised data
        d = testa.data
        self.assertEqual(d['id'], 'a')
        self.assertEqual(d['keys'], ['a', 'b'])

        d = testb_a.data
        self.assertEqual(d['id'], 'a')
        self.assertEqual(d['value'], 'a')

        d = testb_b.data
        self.assertEqual(d['id'], 'b')
        self.assertEqual(d['value'], 'b')

        d = testb_c.data
        self.assertEqual(d['id'], 'c')
        self.assertEqual(d['value'], 'c')
