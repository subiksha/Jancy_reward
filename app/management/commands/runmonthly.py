from django.core.management.base import BaseCommand
from app.utils import generate_monthly_entries

class Command(BaseCommand):
    help = "Generate monthly charges and rewards"

    def handle(self, *args, **kwargs):
        generate_monthly_entries()
        self.stdout.write(self.style.SUCCESS("Monthly entries generated successfully"))
