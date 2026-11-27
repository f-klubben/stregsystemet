import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from stregreport import views
from stregreport.models import BreadRazzia
from freezegun import freeze_time

from stregsystem.models import Category, Member


class ParseIdsStringTests(TestCase):
    def test_parse_ids_string_success(self):
        id_string = "11 13 14 1839"
        res = views.parse_ids_string(id_string)

        self.assertSequenceEqual([11, 13, 14, 1839], res)

    def test_parse_ids_string_fail(self):
        wrong_id_string = "0x10 abe 10"
        with self.assertRaises(RuntimeError):
            views.parse_ids_string(wrong_id_string)

    def test_parse_ids_string_unicode(self):
        id_string_unicode = u"11 13"
        res = views.parse_ids_string(id_string_unicode)

        self.assertSequenceEqual([11, 13], res)

    def test_parse_ids_string_with_whitespace(self):
        id_string = "    \r\n  11  \r    13 \n    "
        res = views.parse_ids_string(id_string)

        self.assertSequenceEqual([11, 13], res)


class CategoryRankReportTests(TestCase):
    fixtures = ["initial_data"]

    def setUp(self):
        Category.objects.all().delete()

    def test_no_categories(self):
        self.client.login(username="tester", password="treotreo")
        response = self.client.get(reverse("report_categoryranks"), {}, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("admin/stregsystem/report/ranks.html")

        self.assertEqual(len(response.context['stat_lists']), 0)

    def test_single_category_shown(self):
        self.client.login(username="tester", password="treotreo")
        catA = Category.objects.create(name="Category A")
        catA.save()

        response = self.client.get(reverse("report_categoryranks"), {}, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("admin/stregsystem/report/ranks.html")

        stat_lists = response.context['stat_lists']

        self.assertEqual(stat_lists[0][0], catA.name)


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


class RazziaTests(TestCase):
    fixtures = ["initial_data"]

    def test_bread_razzia_can_create_new(self):
        previous_number_razzias = BreadRazzia.objects.filter(razzia_type=BreadRazzia.BREAD).count()

        self.client.login(username="tester", password="treotreo")
        response = self.client.get(reverse("razzia_new_BR"), follow=True)
        last_url, status_code = response.redirect_chain[-1]

        current_number_razzias = BreadRazzia.objects.filter(razzia_type=BreadRazzia.BREAD).count()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/stregsystem/razzia/bread.html")
        self.assertEqual(current_number_razzias, previous_number_razzias + 1)

    def test_foobar_razzia_can_create_new(self):
        previous_number_razzias = BreadRazzia.objects.filter(razzia_type=BreadRazzia.FOOBAR).count()

        self.client.login(username="tester", password="treotreo")
        response = self.client.get(reverse("razzia_new_FB"), follow=True)
        last_url, status_code = response.redirect_chain[-1]

        current_number_razzias = BreadRazzia.objects.filter(razzia_type=BreadRazzia.FOOBAR).count()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/stregsystem/razzia/foobar.html")
        self.assertEqual(current_number_razzias, previous_number_razzias + 1)

    def test_bread_razzia_member_can_only_register_once(self):
        self.client.login(username="tester", password="treotreo")
        response = self.client.get(reverse("razzia_new_BR"), follow=True)
        razzia_url, _ = response.redirect_chain[-1]

        response_add_1 = self.client.post(razzia_url, {"username": "jokke"}, follow=True)

        response_add_2 = self.client.post(razzia_url, {"username": "jokke"}, follow=True)

        self.assertEqual(response_add_1.status_code, 200)
        self.assertEqual(response_add_2.status_code, 200)
        self.assertTemplateUsed(response, "admin/stregsystem/razzia/bread.html")
        self.assertNotContains(response_add_1, "already checked in", status_code=200)
        self.assertContains(response_add_2, "already checked in", status_code=200)

    def test_foobar_razzia_member_can_register_multiple_times(self):
        with freeze_time() as frozen_datetime:
            self.client.login(username="tester", password="treotreo")
            response = self.client.get(reverse("razzia_new_FB"), follow=True)
            razzia_url, _ = response.redirect_chain[-1]

            response_members_0 = self.client.get(razzia_url + "members", follow=True)

            response_add_1 = self.client.post(razzia_url, {"username": "jokke"}, follow=True)
            frozen_datetime.tick(delta=datetime.timedelta(hours=1, minutes=1))
            response_add_2 = self.client.post(razzia_url, {"username": "jokke"}, follow=True)

            response_members_2 = self.client.get(razzia_url + "members", follow=True)

            self.assertEqual(response_add_1.status_code, 200)
            self.assertEqual(response_add_2.status_code, 200)
            self.assertTemplateUsed(response_add_1, "admin/stregsystem/razzia/foobar.html")
            self.assertTemplateUsed(response_add_2, "admin/stregsystem/razzia/foobar.html")
            self.assertNotContains(response_add_1, "last checked in at", status_code=200)
            self.assertContains(response_add_2, "last checked in at", status_code=200)
            self.assertContains(response_members_0, "0 fember(s)", status_code=200)
            self.assertContains(response_members_2, "2 fember(s)", status_code=200)

    def test_razzia_registered_member_is_in_member_list(self):
        self.client.login(username="tester", password="treotreo")
        response = self.client.get(reverse("razzia_new_BR"), follow=True)
        razzia_url, _ = response.redirect_chain[-1]

        response_add = self.client.post(razzia_url, {"username": "jokke"}, follow=True)

        response_members = self.client.get(razzia_url + "members", follow=True)

        self.assertEqual(response_add.status_code, 200)
        self.assertTemplateUsed(response_members, "admin/stregsystem/razzia/members.html")
        self.assertContains(response_members, "jokke", status_code=200)


class SignupReportTests(TestCase):
    def setUp(self) -> None:
        self.tz = timezone.get_current_timezone()

    def test_parse_local_date(self) -> None:
        parsed_time = views.parse_local_date("19-10-2026")

        aware_time = timezone.datetime(
            year=2026,
            month=10,
            day=19,
            hour=0,
            minute=0,
            second=0,
            tzinfo=self.tz,
        )
        self.assertEqual(parsed_time, aware_time)

        utc_time = timezone.localtime(aware_time, timezone=timezone.utc)
        self.assertEqual(parsed_time.day, 19)
        self.assertEqual(utc_time.day, 18)

    def test_current_local_date(self) -> None:
        local_date = views.current_local_date()
        utc_date = timezone.datetime.now(timezone.utc)

        self.assertLess(local_date - local_date, utc_date - local_date)

    def test_aware_date_to_local_str(self) -> None:
        aware_time = timezone.datetime(
            year=2026,
            month=10,
            day=19,
            hour=0,
            minute=30,
            second=0,
            tzinfo=self.tz,
        )

        local_str = views.aware_date_to_local_str(aware_time)

        utc_time = timezone.localtime(aware_time, timezone=timezone.timezone.utc)

        self.assertEqual(utc_time.day, 18)
        self.assertEqual(local_str, "19-10-2026")

    def test_inclusive_date_range(self) -> None:
        Member.objects.create().save()

        to_date = views.current_local_date()
        from_date = to_date - timezone.timedelta(days=30)

        date_range = views.inclusive_date_range(from_date, to_date)

        query = Member.objects.filter(created_at__range=date_range)

        self.assertGreater(query.count(), 0)
