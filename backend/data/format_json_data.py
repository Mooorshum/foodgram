import json

with open('ingredients.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

transformed_data = [
    {
        "model": "recipes.ingredient",
        "pk": index + 1,
        "fields": {
            "name": ingredient["name"],
            "measurement_unit": ingredient["measurement_unit"]
        }
    }
    for index, ingredient in enumerate(data)
]

with open('transformed_ingredients.json', 'w', encoding='utf-8') as file:
    json.dump(transformed_data, file, ensure_ascii=False, indent=4)

print("Transformation complete!")
