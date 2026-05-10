from django.core.management.base import BaseCommand

from dashboard.services import rebuild_daily_usage_stats


class Command(BaseCommand):
    help = "重建 DailyUsageStat 预聚合数据"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=90)

    def handle(self, *args, **options):
        count = rebuild_daily_usage_stats(days=options["days"])
        self.stdout.write(self.style.SUCCESS(f"已重建 {count} 条 DailyUsageStat 数据"))
