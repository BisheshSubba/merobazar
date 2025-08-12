from django import forms
from .models import Product,Category,SubCategory,SubSubCategory

# STEP 1: Basic Info + Images
class ProductBasicInfoForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

# STEP 2: Category Selection
class ProductCategoryForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=True,
        error_messages={
            'required': 'Please select a main category'
        }
    )
    subcategory = forms.ModelChoiceField(
        queryset=SubCategory.objects.none(),
        required=False
    )
    subsubcategory = forms.ModelChoiceField(
        queryset=SubSubCategory.objects.none(),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Handle both initial data and POST data
        if self.data:
            try:
                category_id = int(self.data.get('step2-category', 0))
                if category_id:
                    self.fields['subcategory'].queryset = SubCategory.objects.filter(
                        category_id=category_id
                    )
                
                subcategory_id = int(self.data.get('step2-subcategory', 0))
                if subcategory_id:
                    self.fields['subsubcategory'].queryset = SubSubCategory.objects.filter(
                        subcategory_id=subcategory_id
                    )
            except (ValueError, TypeError):
                pass
        elif self.initial:
            if 'category' in self.initial:
                self.fields['subcategory'].queryset = SubCategory.objects.filter(
                    category_id=self.initial['category']
                )
            if 'subcategory' in self.initial:
                self.fields['subsubcategory'].queryset = SubSubCategory.objects.filter(
                    subcategory_id=self.initial['subcategory']
                )

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        
        # Only validate subcategories if category is selected
        if category:
            subcategory = cleaned_data.get('subcategory')
            if subcategory and subcategory.category != category:
                self.add_error('subcategory', "Selected subcategory doesn't belong to the main category")
            
            subsubcategory = cleaned_data.get('subsubcategory')
            if subsubcategory and subsubcategory.subcategory != subcategory:
                self.add_error('subsubcategory', "Selected sub-subcategory doesn't belong to the subcategory")
        
        return cleaned_data
# STEP 4: Final Details
class ProductFinalDetailsForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['price', 'condition', 'brand', 'color', 'city', 'location_address']
        widgets = {
            'price': forms.NumberInput(attrs={'step': '0.01'}),
        }
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class ProductImageForm(forms.Form):
    images = MultipleFileField(label='Product Images')

class ProductUpdateForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'category', 'subcategory', 'subsubcategory',
            'price', 'condition', 'brand', 'color', 'city', 'location_address'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'price': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up the category dropdowns
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category', 0))
                self.fields['subcategory'].queryset = SubCategory.objects.filter(category_id=category_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            if self.instance.category:
                self.fields['subcategory'].queryset = SubCategory.objects.filter(category=self.instance.category)
            if self.instance.subcategory:
                self.fields['subsubcategory'].queryset = SubSubCategory.objects.filter(subcategory=self.instance.subcategory)