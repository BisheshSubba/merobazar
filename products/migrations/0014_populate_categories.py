from django.db import migrations

def create_categories(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    SubCategory = apps.get_model('products', 'SubCategory')
    SubSubCategory = apps.get_model('products', 'SubSubCategory')

    electronics = Category.objects.create(name='Electronics')
    fashion = Category.objects.create(name='Fashion')

    mobiles = SubCategory.objects.create(category=electronics, name='Mobiles')
    laptops = SubCategory.objects.create(category=electronics, name='Laptops')
    mens_wear = SubCategory.objects.create(category=fashion, name="Men's Wear")

    SubSubCategory.objects.create(subcategory=mobiles, name='Smartphones')
    SubSubCategory.objects.create(subcategory=mobiles, name='Feature Phones')
    SubSubCategory.objects.create(subcategory=laptops, name='Gaming Laptops')
    SubSubCategory.objects.create(subcategory=mens_wear, name='Shirts')


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0013_alter_order_status'),
    ]

    operations = [
        migrations.RunPython(create_categories),
    ]
