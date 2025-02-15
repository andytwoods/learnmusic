import random
from datetime import timedelta
from django.utils.timezone import now
from django.core.management.base import BaseCommand
from notes.models import LearningScenario, NoteRecordPackage


class Command(BaseCommand):
    help = "Create X NoteRecordPackage records for the most recent LearningScenario"

    def add_arguments(self, parser):
        # Argument to specify the number of records to create
        parser.add_argument(
            'num_records', type=int, help="Number of NoteRecordPackage records to create"
        )

    def handle(self, *args, **options):
        # Get the number of records to create
        num_records = options['num_records']

        # Get the latest LearningScenario
        learningscenario = LearningScenario.objects.last()
        if not learningscenario:
            self.stdout.write(self.style.ERROR("No LearningScenario objects found."))
            return

        # Example list of notes
        base_notes = [
            {"note": "F", "octave": "3", "alter": "1"},
            {"note": "G", "octave": "3", "alter": "-1"},
            {"note": "G", "octave": "3", "alter": "0"},
            {"note": "G", "octave": "3", "alter": "1"},
            {"note": "A", "octave": "3", "alter": "-1"},
            {"note": "A", "octave": "3", "alter": "0"},
            {"note": "B", "octave": "3", "alter": "0"},
            {"note": "C", "octave": "4", "alter": "0"},
            {"note": "D", "octave": "4", "alter": "0"},
        ]

        # Create X records with progressive dates and dynamic logs
        for i in range(num_records):
            # Days back from today
            days_back = i + 1

            # Dynamically adjust the number of notes (up to 25% fewer notes)
            notes_for_today = self.vary_notes(base_notes)

            # Example log with variations
            log_data = self.generate_log(notes_for_today, days_back, total_records=num_records)

            # Create the NoteRecordPackage with a progressively earlier `created` timestamp
            note_record_package = NoteRecordPackage.objects.create(
                learningscenario=learningscenario,
                log=log_data,
                created=now() - timedelta(days=days_back)  # Set creation date progressively earlier
            )

            # Print success for each created record
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created NoteRecordPackage (id={note_record_package.id}) with created date {note_record_package.created}"
                )
            )

    def vary_notes(self, base_notes):
        """
        Randomly reduce the number of notes by up to 25%.

        Args:
            base_notes (list): The full list of available notes.

        Returns:
            list: Reduced list of notes to include in the log.
        """
        reduction_factor = random.uniform(0.75, 1.0)  # Reduce notes by 75% to 100%
        reduced_count = int(len(base_notes) * reduction_factor)
        return random.sample(base_notes, reduced_count)  # Randomly sample the reduced number of notes

    def generate_log(self, notes, days_back, total_records):
        """
        Dynamically generate log data, making records more accurate and faster the closer they are to the current date.

        Args:
            notes (list): List of notes to include in the log.
            days_back (int): Number of days the record is from today.
            total_records (int): Total number of records to create.

        Returns:
            list: Log data for the NoteRecordPackage.
        """
        log_data = []
        for note in notes:
            # Calculate accuracy and reaction time based on how close this is to "today"
            proximity_factor = (total_records - days_back + 1) / total_records

            # Generate reactions and correctness
            n = random.randint(1, 3)  # Number of responses
            reaction_time_log = [
                int(random.randint(100, 600) * (1 - proximity_factor * 0.5)) for _ in range(n)
            ]  # Faster reaction times closer to today
            correct_log = [
                random.choices([True, False], [proximity_factor, 1 - proximity_factor])[0]
                for _ in range(n)
            ]  # More accurate closer to today

            # Construct the record structure
            log_data.append({
                "note": note["note"],
                "octave": note["octave"],
                "alter": note["alter"],
                "reaction_time": sum(reaction_time_log) / n,  # Average reaction time
                "n": n,
                "reaction_time_log": reaction_time_log,
                "correct": correct_log,
            })

        return log_data
