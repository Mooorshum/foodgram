import csv
import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient

class Command(BaseCommand):
    help = 'Load ingredients data from CSV and JSON files'

    def handle(self, *args, **kwargs):
        self.load_csv_data()
        self.load_json_data()

    def load_csv_data(self):
        with open('/app/data/ingredients.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                Ingredient.objects.create(
                    name=row[0],
                    measurement_unit=row[1]
                )

    def load_json_data(self):
        with open('/app/data/ingredients.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            for item in data:
                Ingredient.objects.create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
