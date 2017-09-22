from unittest import TestCase

from stregreport import views


class ViewTests(TestCase):
    def test_parse_id_string_success(self):
        id_string = "11 13 14 1839"
        res = views.parse_id_string(id_string)

        self.assertSequenceEqual([11, 13, 14, 1839], res)

    def test_parse_id_string_fail(self):
        wrong_id_string = "0x10 abe 10"
        with self.assertRaises(RuntimeError):
            views.parse_id_string(wrong_id_string)
