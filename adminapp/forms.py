from django import forms
from django.contrib.contenttypes.models import ContentType
from products.models import (
    Category, SubCategory, SubSubCategory
)

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ['category', 'name']

class SubSubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubSubCategory
        fields = ['subcategory', 'name']

