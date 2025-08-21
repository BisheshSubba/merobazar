from django.core.management.base import BaseCommand
from recommendations.utils import HybridRecommender
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Update recommendation matrices and similarities'
    
    def handle(self, *args, **options):
        recommender = HybridRecommender()
        User = get_user_model()
        
        self.stdout.write('Updating user similarities...')
        for user in User.objects.all():
            recommender.calculate_user_similarity(user.id)
        
        self.stdout.write('Updating product similarities...')
        from products.models import Product
        for product in Product.objects.filter(is_active=True):
            recommender.calculate_product_similarity(product.id)
        
        self.stdout.write('Recommendations updated successfully!')