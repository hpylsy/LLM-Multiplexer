import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'lab_portal.settings'
django.setup()
from django.contrib.auth.models import User
from django.db.models import Count
from users.models import Profile
from usage.models import UsageLog

print('=== Profile Data Integrity ===')
total = User.objects.count()
with_group = Profile.objects.exclude(lab_group='').count()
with_grade = Profile.objects.exclude(grade='').count()
print(f'Total users: {total}')
print(f'With group set: {with_group}')
print(f'With grade set: {with_grade}')

print('\n=== Group Distribution ===')
for row in Profile.objects.values('lab_group').annotate(c=Count('id')).order_by('-c'):
    print(f"  {row['lab_group'] or '(empty)'}: {row['c']}")

print('\n=== Grade Distribution ===')
for row in Profile.objects.values('grade').annotate(c=Count('id')).order_by('grade'):
    print(f"  {row['grade'] or '(empty)'}: {row['c']}")

print('\n=== Dashboard vs Profile Filter Options ===')
groups_in_logs = sorted(set(UsageLog.objects.exclude(user=None).exclude(user__profile__lab_group='').values_list('user__profile__lab_group', flat=True).distinct()))
grades_in_logs = sorted(set(UsageLog.objects.exclude(user=None).exclude(user__profile__grade='').values_list('user__profile__grade', flat=True).distinct()))
groups_in_profiles = sorted(set(Profile.objects.exclude(lab_group='').values_list('lab_group', flat=True).distinct()))
grades_in_profiles = sorted(set(Profile.objects.exclude(grade='').values_list('grade', flat=True).distinct()))
print(f'Groups in usage logs: {groups_in_logs}')
print(f'Groups in profiles:   {groups_in_profiles}')
print(f'Grades in usage logs: {grades_in_logs}')
print(f'Grades in profiles:   {grades_in_profiles}')

missing_groups = set(groups_in_profiles) - set(groups_in_logs)
missing_grades = set(grades_in_profiles) - set(grades_in_logs)
if missing_groups:
    print(f'\nWARN: Groups in profiles but NOT in logs: {missing_groups}')
if missing_grades:
    print(f'WARN: Grades in profiles but NOT in logs: {missing_grades}')

print('\n=== View Filter Tests ===')
from django.test import RequestFactory
from users.views import admin_user_list
rf = RequestFactory()
u = User.objects.filter(is_staff=True).first()
for params in ['', '?group=算法', '?grade=2024', '?status=active', '?status=disabled']:
    req = rf.get(f'/users/admin/list/{params}')
    req.user = u
    resp = admin_user_list(req)
    print(f'  Filter {params or "(none)"}: {resp.status_code}')

print('\nDone.')
