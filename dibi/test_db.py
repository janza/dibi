import unittest

from dibi.db import SQLParser


class SQLParserTest(unittest.TestCase):
    def test_get_db(self):
        # parser = ()
        self.assertEqual('foo', SQLParser.get_db_from_use('use foo.bar'))

    def test_get_shell_cmd_for_pipe(self):
        # parser = ()
        self.assertEqual('cat dog', SQLParser.get_shell_cmd_for_pipe('select * from foo.bar -- !cat dog'))

    def test_handle_placeholders_stores(self):
        parser = SQLParser()
        put_result, query = next(parser.handle_placeholders('result := select * from foo.bar'))
        self.assertEqual(query, 'select * from foo.bar')
        self.assertEqual(put_result, None)
        self.assertEqual(parser.variables, {
            'result': 'select * from foo.bar'
        })

    def test_handle_placeholders_replaces(self):
        parser = SQLParser()
        next(parser.handle_placeholders('result := select "bla"'))
        result = parser.handle_placeholders('select * from foo.$result')
        put_result, _ = next(result)
        put_result(['bar', 'baz'])
        _, query = next(result)
        self.assertEqual(query, 'select * from foo. bar')
        _, query = next(result)
        self.assertEqual(query, 'select * from foo. baz')
