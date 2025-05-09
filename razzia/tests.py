from django.test import TestCase
from django.urls import reverse
from freezegun import freeze_time

from razzia.models import Razzia

import datetime


class RazziaTests(TestCase):
    fixtures = ["initial_data"]

    def test_razzia_can_create_new(self):
        previous_number_razzias = Razzia.objects.count()

        self.client.login(username="tester", password="treotreo")
        response = self.client.get(reverse("razzia_new"), follow=True)
        last_url, status_code = response.redirect_chain[-1]

        current_number_razzias = Razzia.objects.count()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "razzia.html")
        self.assertEqual(current_number_razzias, previous_number_razzias + 1)

    def test_razzia_member_can_only_register_once(self):
        self.client.login(username="tester", password="treotreo")
        response = self.client.get(reverse("razzia_new"), follow=True)
        razzia_url, _ = response.redirect_chain[-1]

        response_add_1 = self.client.post(
            razzia_url, {"username": "jokke"}, follow=True
        )

        response_add_2 = self.client.post(
            razzia_url, {"username": "jokke"}, follow=True
        )

        self.assertEqual(response_add_1.status_code, 200)
        self.assertEqual(response_add_2.status_code, 200)
        self.assertTemplateUsed(response, "razzia.html")
        # Note: Different interface, should be fixed later.
        # self.assertNotContains(response_add_1, "already checked in", status_code=200)
        # self.assertContains(response_add_2, "already checked in", status_code=200)

    def test_razzia_member_can_register_multiple_times(self):
        with freeze_time() as frozen_datetime:
            self.client.login(username="tester", password="treotreo")
            response = self.client.get(reverse("razzia_new"), follow=True)
            razzia_url, _ = response.redirect_chain[-1]

            response_members_0 = self.client.get(razzia_url + "members", follow=True)

            response_add_1 = self.client.post(
                razzia_url, {"username": "jokke"}, follow=True
            )
            frozen_datetime.tick(delta=datetime.timedelta(hours=1, minutes=1))
            response_add_2 = self.client.post(
                razzia_url, {"username": "jokke"}, follow=True
            )

            response_members_2 = self.client.get(razzia_url + "members", follow=True)

            self.assertEqual(response_add_1.status_code, 200)
            self.assertEqual(response_add_2.status_code, 200)
            self.assertTemplateUsed(response_add_1, "razzia.html")
            self.assertTemplateUsed(response_add_2, "razzia.html")
            # Note: Different interface, should be fixed later.
            # self.assertNotContains(response_add_1, "last checked in at", status_code=200)
            # self.assertContains(response_add_2, "last checked in at", status_code=200)
            self.assertContains(response_members_0, "0 entr", status_code=200)
            self.assertContains(response_members_2, "2 entr", status_code=200)

    def test_razzia_registered_member_is_in_member_list(self):
        self.client.login(username="tester", password="treotreo")
        response = self.client.get(reverse("razzia_new"), follow=True)
        razzia_url, _ = response.redirect_chain[-1]

        response_add = self.client.post(razzia_url, {"username": "jokke"}, follow=True)

        response_members = self.client.get(razzia_url + "members", follow=True)

        self.assertEqual(response_add.status_code, 200)
        self.assertTemplateUsed(response_members, "members.html")
        self.assertContains(response_members, "jokke", status_code=200)

    def test_razzia_unique_members_unique(self):
        self.client.login(username="tester", password="treotreo")
        response = self.client.get(reverse("razzia_new"), follow=True)
        razzia_url, _ = response.redirect_chain[-1]

        response_add = self.client.post(razzia_url, {"username": "jokke"}, follow=True)
        self.assertEqual(response_add.status_code, 200)

        response_members = self.client.get(razzia_url + "members", follow=True)

        self.assertTemplateUsed(response_members, "members.html")
        self.assertContains(response_members, "jokke", status_code=200)

        response_add_2 = self.client.post(razzia_url, {"username": "jan"}, follow=True)
        self.assertEqual(response_add_2.status_code, 200)

        response_members_2 = self.client.get(razzia_url + "members", follow=True)
        self.assertTemplateUsed(response_members, "members.html")
        self.assertContains(response_members, "jan", status_code=200)

        self.assertContains(response_members_2, "2 entr", status_code=200)
        self.assertContains(response_members_2, "2 fember(s)", status_code=200)

    def test_razzia_unique_members_same(self):
        with freeze_time() as frozen_datetime:
            self.client.login(username="tester", password="treotreo")
            response = self.client.get(reverse("razzia_new"), follow=True)
            razzia_url, _ = response.redirect_chain[-1]

            response_members_0 = self.client.get(razzia_url + "members", follow=True)

            response_add_1 = self.client.post(
                razzia_url, {"username": "jokke"}, follow=True
            )
            frozen_datetime.tick(delta=datetime.timedelta(hours=1, minutes=1))
            response_add_2 = self.client.post(
                razzia_url, {"username": "jokke"}, follow=True
            )

            response_members_2 = self.client.get(razzia_url + "members", follow=True)

            self.assertEqual(response_add_1.status_code, 200)
            self.assertEqual(response_add_2.status_code, 200)
            self.assertTemplateUsed(response_add_1, "razzia.html")
            self.assertTemplateUsed(response_add_2, "razzia.html")
            self.assertContains(response_members_0, "0 entr", status_code=200)
            self.assertContains(response_members_0, "0 fember(s)", status_code=200)
            self.assertContains(response_members_2, "2 entr", status_code=200)
            self.assertContains(response_members_2, "1 fember(s)", status_code=200)
