from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from api_keys.models import APIKey
from usage.models import UsageImportJob, UsageLog
from usage.services import import_usage_records

class MyUsageLogsPageTests(TestCase):
    def test_page_uses_plain_usage_record_copy_without_key_column(self):
        user = User.objects.create_user(username="member", password="password")
        self.client.force_login(user)

        response = self.client.get(reverse("my-usage-logs"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "我的使用记录")
        self.assertNotContains(response, "我的 Usage 记录")
        self.assertNotContains(response, "<th>Key</th>", html=True)


class UsageImportAssociationTests(TestCase):
    def test_existing_unmatched_log_gets_association_when_key_is_bound_later(self):
        user = User.objects.create_user(username="member", password="password")
        raw_token = "sk-member-token"
        metadata = APIKey.build_token_metadata(raw_token)
        key = APIKey.objects.create(
            user=user,
            name="API 密钥",
            token_hash=metadata["token_hash"],
            token_prefix=metadata["token_prefix"],
            token_masked=metadata["token_masked"],
            token_plaintext=raw_token,
            source=APIKey.SOURCE_CLIPROXY,
            status=APIKey.STATUS_ACTIVE,
        )
        UsageLog.objects.create(
            request_id="request-1",
            api_key_identifier=raw_token,
            model_name="gpt-5.4",
            total_tokens=100,
            request_time=timezone.now(),
        )

        import_usage_records(
            [
                {
                    "request_id": "request-1",
                    "api_key_identifier": raw_token,
                    "model_name": "gpt-5.4",
                    "total_tokens": 100,
                    "request_time": timezone.now().isoformat(),
                }
            ],
            UsageImportJob.SOURCE_COMMAND,
            "repair-test",
        )

        log = UsageLog.objects.get(request_id="request-1")
        self.assertEqual(log.user, user)
        self.assertEqual(log.api_key, key)
