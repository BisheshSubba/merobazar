from rest_framework import serializers
from .models import Product, ProductImage, Category, SubCategory, SubSubCategory

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class SubCategorySerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    
    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'category']

class SubSubCategorySerializer(serializers.ModelSerializer):
    subcategory = SubCategorySerializer()
    
    class Meta:
        model = SubSubCategory
        fields = ['id', 'name', 'subcategory']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    subcategory = SubCategorySerializer()
    subsubcategory = SubSubCategorySerializer()
    images = ProductImageSerializer(many=True)
    user = serializers.StringRelatedField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'condition',
            'brand', 'color', 'city', 'location_address',
            'category', 'subcategory', 'subsubcategory',
            'images', 'user', 'created_at'
        ]