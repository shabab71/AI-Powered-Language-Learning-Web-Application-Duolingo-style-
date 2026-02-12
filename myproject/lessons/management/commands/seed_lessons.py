from django.core.management.base import BaseCommand
from lessons.models import Lesson

class Command(BaseCommand):
    help = "Seeds the database with initial lessons data (6 units × 4 lessons each)."

    def handle(self, *args, **options):
        Lesson.objects.all().delete()
        self.stdout.write(self.style.WARNING("Cleared old Lesson data."))

        units = [
            (1, "Introduce yourself"),
            (2, "Greetings"),
            (3, "Order drinks"),
            (4, "Introduce family members"),
            (5, "Talk to the waiter"),
            (6, "Discuss places"),
        ]

        lessons = []
        for unit_number, title in units:
            base_lessons = [
                ("Basic", "🙂", "easy"),
                ("Advanced", "💬", "medium"),
                ("Audio", "🔊", "medium"),
                ("Quiz", "❓", "hard"),
            ]
            for i, (name, icon, diff) in enumerate(base_lessons, start=1):
                lessons.append(
                    Lesson(
                        unit_number=unit_number,
                        unit_title=title,
                        name=name,
                        icon=icon,
                        difficulty=diff,
                        order=i,
                        status="active" if unit_number == 1 else "locked",
                        progress=100 if unit_number == 1 and i < 3 else 0,
                        description=f"{name} lesson for {title.lower()}. Practice and test your skills.",
                    )
                )

        Lesson.objects.bulk_create(lessons)
        self.stdout.write(self.style.SUCCESS(f"✅ Seeded {len(lessons)} lessons successfully!"))
