from django import forms
from django.contrib.contenttypes.models import ContentType
from products.models import (
    Category, SubCategory, SubSubCategory, 
    Attribute, ProductAttribute
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

class AttributeForm(forms.ModelForm):
    class Meta:
        model = Attribute
        fields = ['name', 'data_type', 'is_required', 'options', 'apply_to', 'content_type', 'object_id']
        widgets = {
            'options': forms.TextInput(attrs={
                'placeholder': 'Comma-separated values for options'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['options'].required = False
        
        # Limit content_type choices based on apply_to
        if 'apply_to' in self.data:
            apply_to = self.data.get('apply_to')
            if apply_to == 'category':
                self.fields['content_type'].queryset = ContentType.objects.filter(model='category')
            elif apply_to == 'subcategory':
                self.fields['content_type'].queryset = ContentType.objects.filter(model='subcategory')
            elif apply_to == 'subsubcategory':
                self.fields['content_type'].queryset = ContentType.objects.filter(model='subsubcategory')
        
        # Hide object_id field initially
        self.fields['object_id'].widget = forms.HiddenInput()
        self.fields['object_id'].required = False

class AttributeEditForm(AttributeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            self.fields['apply_to'].initial = instance.apply_to
            self.fields['content_type'].queryset = ContentType.objects.filter(
                model=instance.content_type.model
            )
            self.fields['object_id'].initial = instance.object_id