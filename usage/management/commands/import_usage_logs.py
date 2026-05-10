from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from usage.models import UsageImportJob
from usage.services import import_usage_records


class Command(BaseCommand):
    help = "从 CSV 或 JSONL 文件导入 usage 日志"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str, help="CSV 或 JSONL 文件路径")

    def handle(self, *args, **options):
        file_path = Path(options["file_path"])
        if not file_path.exists():
            raise CommandError(f"文件不存在: {file_path}")

        suffix = file_path.suffix.lower()
        content = file_path.read_text(encoding="utf-8")
        if suffix == ".jsonl":
            import json

            records = [json.loads(line) for line in content.splitlines() if line.strip()]
        elif suffix == ".csv":
            import csv

            records = list(csv.DictReader(content.splitlines()))
        else:
            raise CommandError("仅支持 CSV 或 JSONL")

        job = import_usage_records(records, UsageImportJob.SOURCE_COMMAND, str(file_path))
        self.stdout.write(self.style.SUCCESS(
            f"导入完成：成功 {job.imported_count}，跳过 {job.skipped_count}，失败 {job.failed_count}"
        ))
        if job.summary:
            self.stdout.write(job.summary)
