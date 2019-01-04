'''
ZiGate core Tests
-------------------------
'''

import unittest
import os
import shutil
import tempfile
from zigate import ZiGate, responses, transport


class TestCore(unittest.TestCase):
    def setUp(self):
        self.zigate = ZiGate(auto_start=False)
        self.zigate.connection = transport.FakeTransport()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_persistent(self):
        path = os.path.join(self.test_dir, 'test_zigate.json')
        backup_path = path + '.0'

        result = self.zigate.load_state(path)
        self.assertFalse(result)

        with open(path, 'w') as fp:
            fp.write('fake file - test')
        result = self.zigate.load_state(path)
        self.assertFalse(result)

        os.remove(path)

        self.zigate.save_state(path)
        self.assertTrue(os.path.exists(path))
        self.assertFalse(os.path.exists(backup_path))
        self.zigate.save_state(path)
        self.assertTrue(os.path.exists(backup_path))

        result = self.zigate.load_state(path)
        self.assertTrue(result)

        os.remove(path)
        os.remove(backup_path)

    def test_group_membership(self):
        msg_data = b'\x01\x01\x00\x04\x124\x10\x00'
        r = responses.R8062(msg_data, 255)
        self.zigate.interpret_response(r)
        self.assertDictEqual(self.zigate.groups,
                             {})

        msg_data = b'\x01\x01\x00\x04\x124\x10\x01\x98v'
        r = responses.R8062(msg_data, 255)
        self.zigate.interpret_response(r)
        self.assertDictEqual(self.zigate.groups,
                             {'9876': {('1234', 1)}})

        msg_data = b'\x01\x01\x00\x04\x124\x10\x02\x98v4V'
        r = responses.R8062(msg_data, 255)
        self.zigate.interpret_response(r)
        self.assertDictEqual(self.zigate.groups,
                             {'9876': {('1234', 1)},
                              '3456': {('1234', 1)}})

        msg_data = b'\x01\x01\x00\x04\x124\x10\x014V'
        r = responses.R8062(msg_data, 255)
        self.zigate.interpret_response(r)
        self.assertDictEqual(self.zigate.groups,
                             {'3456': {('1234', 1)}})

    def test_groups(self):
        self.zigate.add_group('1234', 1, '4567')
        self.assertDictEqual(self.zigate.groups,
                             {'4567': {('1234', 1)},
                              })
        msg_data = b'\x01\x01\x00\x04\x124\x10\x02\x98v4V'
        r = responses.R8062(msg_data, 255)
        self.zigate.interpret_response(r)
        self.assertDictEqual(self.zigate.groups,
                             {'9876': {('1234', 1)},
                              '3456': {('1234', 1)}})
        self.zigate.add_group('1234', 1, '4567')
        self.zigate.add_group('0123', 1, '4567')
        self.assertDictEqual(self.zigate.groups,
                             {'9876': {('1234', 1)},
                              '3456': {('1234', 1)},
                              '4567': {('1234', 1), ('0123', 1)},
                              })
        self.zigate.remove_group('1234', 1, '9876')
        self.assertDictEqual(self.zigate.groups,
                             {'3456': {('1234', 1)},
                              '4567': {('1234', 1), ('0123', 1)},
                              })
        self.zigate.remove_group('1234', 1)
        self.assertDictEqual(self.zigate.groups,
                             {'4567': {('0123', 1)},
                              })

    def test_attribute_discovery(self):
        msg_data = b'\x000\x00\x08\x93-\x03\x03\x00'
        r = responses.R8140(msg_data, 255)
        self.zigate.interpret_response(r)
        self.assertCountEqual(self.zigate._devices['932d'].get_attributes(),
                              [{'attribute': 8,
                                'name': 'colour_mode', 'value': None}])


if __name__ == '__main__':
    unittest.main()
