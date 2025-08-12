from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('category', 'name')

    def __str__(self):
        return f"{self.category.name} - {self.name}"

class SubSubCategory(models.Model):
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='subsubcategories')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('subcategory', 'name')

    def __str__(self):
        return f"{self.subcategory.name} - {self.name}"

class Attribute(models.Model):
    DATA_TYPE_CHOICES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('decimal', 'Decimal'),
        ('boolean', 'Boolean'),
        ('options', 'Options'),
    ]

    name = models.CharField(max_length=100)
    data_type = models.CharField(max_length=20, choices=DATA_TYPE_CHOICES)
    is_required = models.BooleanField(default=False)

    options = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        null=True,
        help_text="For 'Options' type only. Enter choices as comma-separated values."
    )

    APPLY_TO_CHOICES = [
        ('category', 'Entire Category'),
        ('subcategory', 'Specific SubCategory'),
        ('subsubcategory', 'Specific SubSubCategory'),
    ]
    apply_to = models.CharField(max_length=15, choices=APPLY_TO_CHOICES)

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'model__in': ['category', 'subcategory', 'subsubcategory']}
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"{self.name} ({self.get_data_type_display()})"

class Product(models.Model):
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used_like_new', 'Used - Like New'),
        ('used_good', 'Used - Good'),
        ('used_fair', 'Used - Fair'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    subsubcategory = models.ForeignKey(SubSubCategory, on_delete=models.SET_NULL, null=True, blank=True)

    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    brand = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)

    # New location fields
    city = models.CharField(max_length=100, blank=True, null=True)
    location_address = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value_text = models.TextField(blank=True, null=True)
    value_number = models.IntegerField(blank=True, null=True)
    value_decimal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    value_boolean = models.BooleanField(blank=True, null=True)
    value_option = models.CharField(max_length=100, blank=True, null=True)

    @property
    def value(self):
        if self.attribute.data_type == 'text':
            return self.value_text
        elif self.attribute.data_type == 'number':
            return self.value_number
        elif self.attribute.data_type == 'decimal':
            return self.value_decimal
        elif self.attribute.data_type == 'boolean':
            return self.value_boolean
        elif self.attribute.data_type == 'options':
            return self.value_option
        return None

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images',null=True, blank=True)
    image = models.ImageField(upload_to='product_images/')
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
     

    class Meta:
        ordering = ['-is_primary', 'uploaded_at']

    def __str__(self):
        return f"Image for {self.product.name}"
    
class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        verbose_name_plural = "Wishlist Items"

    def __str__(self):
        return f"{self.user.username}'s wishlist: {self.product.name}"

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # Ensures a product can only be added once per user
        verbose_name_plural = "Cart Items"

    def __str__(self):
        return f"{self.user.username}'s cart: {self.product.name}"

    @property
    def total_price(self):
        return self.product.price  
    
class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    sold_at = models.DateTimeField(auto_now_add=True)
    sold_price = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Sale of {self.product.name} for Rs. {self.sold_price}"
    
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"



class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)  
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  

    def __str__(self):
        return f"{self.product.name} - {self.price} (Seller: {self.seller.username})"

