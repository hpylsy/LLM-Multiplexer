from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from dashboard.views import _get_range_start


class DashboardDefaultRangeTests(TestCase):
    def test_public_dashboard_defaults_to_today(self):
        user = User.objects.create_user(username="member", password="password")
        self.client.force_login(user)

        response = self.client.get(reverse("public-dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["range_name"], "today")

    def test_today_range_starts_at_local_midnight(self):
        local_now = datetime(2026, 4, 26, 0, 23, tzinfo=ZoneInfo("Asia/Shanghai"))

        with patch("dashboard.views.timezone.localtime", return_value=local_now):
            start = _get_range_start("today")

        self.assertEqual(start, datetime(2026, 4, 26, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai")))

    def test_admin_dashboard_defaults_to_today(self):
        user = User.objects.create_user(username="admin", password="password", is_staff=True)
        self.client.force_login(user)

        response = self.client.get(reverse("admin-dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["range_name"], "today")
