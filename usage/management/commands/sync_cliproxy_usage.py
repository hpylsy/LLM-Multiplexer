from django.core.management.base import BaseCommand, CommandError

from usage.services import sync_cliproxy_usage_records


class Command(BaseCommand):
    help = "从 cliproxy 管理接口同步 usage 数据"

    def handle(self, *args, **options):
        try:
            job = sync_cliproxy_usage_records()
        except Exception as exc:
            raise CommandError(f"同步 cliproxy usage 失败: {exc}")

        self.stdout.write(self.style.SUCCESS(
            f"同步完成：成功 {job.imported_count}，跳过 {job.skipped_count}，失败 {job.failed_count}"
        ))
        if job.summary:
            self.stdout.write(job.summary)
