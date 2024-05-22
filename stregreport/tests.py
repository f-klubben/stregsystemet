from django.test import TestCase
from django.urls import reverse

from stregreport import views


class ParseIdStringTests(TestCase):
    def test_parse_id_string_success(self):
        id_string = "11 13 14 1839"
        res = views.parse_id_string(id_string)

        self.assertSequenceEqual([11, 13, 14, 1839], res)

    def test_parse_id_string_fail(self):
        wrong_id_string = "0x10 abe 10"
        with self.assertRaises(RuntimeError):
            views.parse_id_string(wrong_id_string)

    def test_parse_id_string_unicode(self):
        id_string_unicode = u"11 13"
        res = views.parse_id_string(id_string_unicode)

        self.assertSequenceEqual([11, 13], res)


class SalesReportTests(TestCase):
    fixtures = ["initial_data"]

    def test_sales_view_no_args(self):
        response = self.client.get(reverse("salesreporting", args=0), {}, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("admin/stregsystem/report/sales.html")

    def test_sales_report_all_ok(self):
        self.client.login(username="tester", password="treotreo")
        response = self.client.post(
            reverse("salesreporting"),
            {"products": "1", "from_date": "2007-07-01", "to_date": "2007-07-30"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("admin/stregsystem/report/sales.html")
        self.assertSequenceEqual(response.context["sales"], [('', 'TOTAL', 0, '0.00')])

    def test_sales_report_invalid_products(self):
        self.client.login(username="tester", password="treotreo")
        response = self.client.post(
            reverse("salesreporting"),
            {"products": "abe", "from_date": "2007-07-01", "to_date": "2007-07-30"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("admin/stregsystem/report/error_invalidsalefetch.html")

    def test_sales_report_invalid_date_format(self):
        self.client.login(username="tester", password="treotreo")
        response = self.client.get(
            reverse("salesreporting"),
            {
                "products": "1",
                "from_date": "2007-30-07",
                "to_date": "2007-07-30",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("admin/stregsystem/report/sales.html")
