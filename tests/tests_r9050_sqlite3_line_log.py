# ROBOT9050 SQLite3 Line Log Unit Tests
from unittest import TestCase
from r9050_line_log import Robot9050Sqlite3LineLog

class InitTests(TestCase):

    def test_init_unsupported_hash_fn(self):
        with self.assertRaises(KeyError):
            testlog = Robot9050Sqlite3LineLog(
                action='create',
                database=':memory:',
                hashfn_config={'hash_function': 'UNSUPPORTED_CRYPT'}
            )

class AddTests(TestCase):

    def test_add(self):
        testlog = Robot9050Sqlite3LineLog(action='create', database=':memory:')
        testA = 'test_A'
        testlog.add(testA)
        self.assertEqual(testlog.lookup(testA), 1)

    def test_add_multiple(self):
        testlog = Robot9050Sqlite3LineLog(action='create', database=':memory:')
        testA = 'test_A'
        testlog.add(testA)
        testlog.add(testA)
        testlog.add(testA)
        self.assertEqual(testlog.lookup(testA), 3)

    def test_add_all_hash_fns(self):
        fn_names = Robot9050Sqlite3LineLog.SUPPORTED_HASH_FNS
        for f in fn_names:
            with self.subTest(hash_function=f):
                testlog = Robot9050Sqlite3LineLog(
                    action='create',
                    database=':memory:',
                    hashfn_config={'hash_function': f}
                )
                testA = 'test_A'
                testlog.add(testA)
                self.assertEqual(testlog.lookup(testA), 1)

class LookupTests(TestCase):

    def test_lookup_not_found(self):
        testlog = Robot9050Sqlite3LineLog(action='create', database=':memory:')
        self.assertEqual(testlog.lookup('test_A'), 0)

    def test_lookup_wrong(self):
        testlog = Robot9050Sqlite3LineLog(action='create', database=':memory:')
        testlog.add('test_A')
        testlog.add('test_A')
        testlog.add('test_D')
        self.assertEqual(testlog.lookup('test_B'), 0)

