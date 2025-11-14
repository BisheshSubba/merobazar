from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .utils import HybridRecommender
from products.models import Product
from .models import UserInteraction
import json

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_interaction(request):
    """Track user interaction with a product"""
    product_id = request.data.get('product_id')
    interaction_type = request.data.get('interaction_type', 'view')
    
    if not product_id:
        return Response({'error': 'Product ID is required'}, status=400)
    
    # Create or update interaction
    interaction, created = UserInteraction.objects.get_or_create(
        user=request.user,
        product_id=product_id,
        interaction_type=interaction_type,
        defaults={'weight': 1.0}
    )
    
    if not created:
        interaction.weight += 1.0
        interaction.save()
    
    return Response({'status': 'success', 'interaction_id': interaction.id})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recommendations(request):
    """Get hybrid recommendations for authenticated user"""
    recommender = HybridRecommender()
    
    try:
        recommendations = recommender.get_hybrid_recommendations(
            user_id=request.user.id,
            top_n=request.GET.get('limit', 20)
        )
        
        # Serialize recommendations
        from products.serializers import ProductSerializer 
        serializer = ProductSerializer(recommendations, many=True, context={'request': request})
        
        return Response({
            'count': len(recommendations),
            'results': serializer.data
        })
        
    except Exception as e:
        # Fallback to popular products
        popular_products = recommender.get_popular_products(top_n=20)
        from products.serializers import ProductSerializer
        serializer = ProductSerializer(popular_products, many=True, context={'request': request})
        
        return Response({
            'count': len(popular_products),
            'results': serializer.data,
            'note': 'Using popular products as fallback'
        })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_similar_products(request, product_id):
    """Get products similar to a specific product"""
    recommender = HybridRecommender()
    
    try:
        similar_products = recommender.calculate_product_similarity(product_id, top_n=10)
        from products.serializers import ProductSerializer
        serializer = ProductSerializer(similar_products, many=True, context={'request': request})
        
        return Response({
            'count': len(similar_products),
            'results': serializer.data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['GET'])
def get_popular_products(request):
    """Get popular products (no authentication required)"""
    recommender = HybridRecommender()
    days = request.GET.get('days', 30)
    limit = request.GET.get('limit', 20)
    
    popular_products = recommender.get_popular_products(
        top_n=limit,
        days=int(days)
    )
    
    from products.serializers import ProductSerializer
    serializer = ProductSerializer(popular_products, many=True, context={'request': request})
    
    return Response({
        'count': len(popular_products),
        'results': serializer.data
    })