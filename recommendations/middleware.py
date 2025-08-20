from django.utils.deprecation import MiddlewareMixin
from products.models import UserInteraction

class RecommendationMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Check if this is a product detail view
            if 'product_id' in view_kwargs or 'pk' in view_kwargs:
                product_id = view_kwargs.get('product_id') or view_kwargs.get('pk')
                
                try:
                    # Track view interaction
                    UserInteraction.objects.create(
                        user=request.user,
                        product_id=product_id,
                        interaction_type='view'
                    )
                except:
                    pass