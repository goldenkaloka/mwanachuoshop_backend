# shops/management/commands/schedule_subscription_check.py
from django.core.management.base import BaseCommand
from django_q.models import Schedule
from django.utils import timezone
from django.db import OperationalError

class Command(BaseCommand):
    help = 'Sets up the periodic task to check expired subscriptions'

    def handle(self, *args, **kwargs):
        try:
            Schedule.objects.get_or_create(
                name='check_expired_subscriptions',
                defaults={
                    'func': 'shops.tasks.check_expired_subscriptions',
                    'schedule_type': Schedule.MINUTES,
                    'minutes': 60,
                    'next_run': timezone.now(),
                }
            )
            self.stdout.write(self.style.SUCCESS('Successfully set up subscription expiry check task'))
        except OperationalError as e:
            self.stderr.write(self.style.ERROR(f'Failed to set up task: {str(e)}'))
            self.stdout.write(self.style.WARNING('Ensure migrations are applied with "python manage.py migrate"'))