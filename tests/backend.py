import unittest
import string
from secrets import choice
from modelus import *
from models import Complex, ModelA, ModelB, KEY_LENGTH
from ipaddress import IPv4Address

class TestBackend(unittest.TestCase):
    '''Generic backend test that only requires a different self.db value in setUp
    '''
    def setUp(self):
        self.db = None

    def tearDown(self):
        self.db = None

    def model_and_fields(self):
        model = Complex(self.db,
            id='abc',
            string='def',
            email='abc@example.com',
            # don't set generated
            list=['a', 'b'],
            ipv4_address=IPv4Address('127.0.0.1'),
        )
        self.assertEqual(model.primary_key, 'abc')
        self.assertEqual(model.id, 'abc')
        self.assertEqual(model.string, 'def')
        self.assertEqual(model.email, 'abc@example.com')
        # key won't be initialised unless saved or created with db.create
        self.assertIsNone(model.generated)
        self.assertEqual(model.list, ['a', 'b'])
        self.assertEqual(model.ipv4_address, IPv4Address('127.0.0.1'))

        # save and verify the default values are filled out
        self.db.save(model)
        self.assertEqual(model.generated, 'a' * KEY_LENGTH)

        # cleanup for next test
        self.db.delete(model)

        # create the model directly via the db
        # this will automatically fill out the default fields that aren't set
        model = self.db.create(Complex,
            id='abc',
            string='def', # please don't store plaintext passwords, this is just a test, don't copy this!
            email='abc@example.com',
            # don't set generated
            list=['a', 'b'],
            ipv4_address=IPv4Address('127.0.0.1'),
        )
        self.assertEqual(model.primary_key, 'abc')
        self.assertEqual(model.id, 'abc')
        self.assertEqual(model.string, 'def')
        self.assertEqual(model.email, 'abc@example.com')
        self.assertIsNotNone(model.generated)
        self.assertEqual(model.list, ['a', 'b'])
        self.assertEqual(model.ipv4_address, IPv4Address('127.0.0.1'))

        # check the serialised data
        d = model.data
        self.assertEqual(d['id'], 'abc')
        self.assertEqual(d['string'], 'def')
        self.assertEqual(d['email'], 'abc@example.com')
        self.assertIsNotNone(d['generated'])
        self.assertEqual(d['list'], ['a', 'b'])
        self.assertEqual(d['ipv4_address'], IPv4Address('127.0.0.1'))

        # reload the model
        model = self.db.load(Complex, 'abc')

        # check the serialised data is the same
        d = model.data
        self.assertEqual(d['id'], 'abc')
        self.assertEqual(d['string'], 'def')
        self.assertEqual(d['email'], 'abc@example.com')
        self.assertIsNotNone(d['generated'])
        self.assertEqual(d['list'], ['a', 'b'])
        self.assertEqual(d['ipv4_address'], IPv4Address('127.0.0.1'))

    def foreign_keys(self):
        # create child models
        # and then a single parent model
        testb_a = self.db.create(ModelB, id='a', value='a')
        testb_b = self.db.create(ModelB, id='b', value='b')
        testb_c = self.db.create(ModelB, id='c', value='c')

        testa = self.db.create(ModelA, id='a', keys=[testb_a])

        self.assertEqual(len(testa.keys), 1)
        self.assertEqual(testa.keys[0].id, 'a')

        # add a new foreign key
        testa.keys.append(testb_b)
        self.db.save(testa)

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

        # reload the values
        testb_a = self.db.load(ModelB, 'a')
        testb_b = self.db.load(ModelB, 'b')
        testb_c = self.db.load(ModelB, 'c')

        testa = self.db.load(ModelA, 'a')

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

        # check that we can dereference foreign keys
        self.assertEqual(testa.keys[0].id, 'a')
        self.assertEqual(testa.keys[0].value, 'a')
        self.assertEqual(testa.keys[1].id, 'b')
        self.assertEqual(testa.keys[1].value, 'b')

    def reverse_foreign_keys(self):
        # check that we can reference a foreign key from the child
        # ie B -> A
        # a = A()
        # b = B(A=a)
        # a.B
        # TODO:

        # check that deleting a model that has an incoming foreign key
        # invalidates the outgoing foreign key
        # ie B -> A
        # delete A
        # should trigger an error when trying to delete B
        testb = self.db.create(ModelB, id='a', value='a')
        testa = self.db.create(ModelA, id='a', keys=[testb])

        with self.assertRaises(TypeError):
            self.db.delete(testb)
