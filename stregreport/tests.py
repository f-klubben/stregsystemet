from django.test import TestCase
from django.urls import reverse

from stregreport import views
from stregreport.models import BreadRazzia


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
        id_string_unicode = "11 13"
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
        self.assertSequenceEqual(response.context["sales"], [("", "TOTAL", 0, "0.00")])

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
            {"products": "1", "from_date": "2007-30-07", "to_date": "2007-07-30"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("admin/stregsystem/report/sales.html")


class BreadRazziaTests(TestCase):
    fixtures = ["initial_data"]

    def test_bread_razzia_can_create_new(self):
        previous_number_razzias = BreadRazzia.objects.count()

        self.client.login(username="tester", password="treotreo")
        response = self.client.get(reverse("bread_new"), follow=True)
        last_url, status_code = response.redirect_chain[-1]

        current_number_razzias = BreadRazzia.objects.count()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("admin/stregsystem/razzia/bread.html")
        self.assertEqual(current_number_razzias, previous_number_razzias + 1)

    def test_bread_razzia_member_can_only_register_once(self):
        self.client.login(username="tester", password="treotreo")
        response = self.client.get(reverse("bread_new"), follow=True)
        razzia_url, _ = response.redirect_chain[-1]

        response_add_1 = self.client.post(razzia_url, {"username": "jokke"}, follow=True)

        response_add_2 = self.client.post(razzia_url, {"username": "jokke"}, follow=True)

        self.assertEqual(response_add_1.status_code, 200)
        self.assertEqual(response_add_2.status_code, 200)
        self.assertTemplateUsed("admin/stregsystem/razzia/bread.html")
        self.assertNotContains(response_add_1, "already checked in", status_code=200)
        self.assertContains(response_add_2, "already checked in", status_code=200)

    def test_bread_razzia_registered_member_is_in_member_list(self):
        self.client.login(username="tester", password="treotreo")
        response = self.client.get(reverse("bread_new"), follow=True)
        razzia_url, _ = response.redirect_chain[-1]

        response_add = self.client.post(razzia_url, {"username": "jokke"}, follow=True)

        response_members = self.client.get(razzia_url + "members", follow=True)

        self.assertEqual(response_add.status_code, 200)
        self.assertTemplateUsed("admin/stregsystem/razzia/bread_members.html")
        self.assertContains(response_members, "jokke", status_code=200)
