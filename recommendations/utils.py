# recommendations/utils.py
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
from products.models import Product
import json
from datetime import datetime, timedelta

class HybridRecommender:
    def __init__(self):
        self.interaction_weights = {
            'view': 1.0,
            'click': 2.0,
            'wishlist': 3.0,
            'cart': 4.0,
            'purchase': 5.0
        }
    
    def create_user_product_matrix(self):
        """Create user-product interaction matrix"""
        from .models import UserInteraction, Product
        
        interactions = UserInteraction.objects.all()
        users = list(set(interaction.user_id for interaction in interactions))
        products = list(set(interaction.product_id for interaction in interactions))
        
        user_index = {user_id: idx for idx, user_id in enumerate(users)}
        product_index = {product_id: idx for idx, product_id in enumerate(products)}
        
        matrix = np.zeros((len(users), len(products)))
        
        for interaction in interactions:
            user_idx = user_index.get(interaction.user_id)
            product_idx = product_index.get(interaction.product_id)
            if user_idx is not None and product_idx is not None:
                weight = self.interaction_weights.get(interaction.interaction_type, 1.0)
                matrix[user_idx][product_idx] += weight
        
        return matrix, users, products, user_index, product_index
    
    def calculate_user_similarity(self, user_id, top_n=10):
        """Calculate similar users based on interaction patterns"""
        from .models import UserInteraction, UserSimilarity
        
        matrix, users, products, user_index, product_index = self.create_user_product_matrix()
        
        if user_id not in user_index:
            return []
        
        user_idx = user_index[user_id]
        user_vector = matrix[user_idx].reshape(1, -1)
        
        similarities = cosine_similarity(user_vector, matrix)[0]
        
        similar_users = []
        for other_user_idx, similarity in enumerate(similarities):
            if other_user_idx != user_idx and similarity > 0:
                similar_users.append((users[other_user_idx], similarity))
        
        similar_users.sort(key=lambda x: x[1], reverse=True)
        
        # Save to database
        for other_user_id, similarity in similar_users[:top_n]:
            UserSimilarity.objects.update_or_create(
                user1_id=user_id,
                user2_id=other_user_id,
                defaults={'similarity_score': similarity}
            )
        
        return similar_users[:top_n]
    
    def create_product_features(self):
        """Create feature vectors for products"""
        from .models import Product
        
        products = Product.objects.filter(is_active=True)
        features = []
        
        for product in products:
            # Combine various features into a text representation
            features_text = f"{product.name} {product.description} {product.brand or ''} {product.color or ''} {product.condition} {product.category.name if product.category else ''}"
            features.append(features_text)
        
        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        feature_vectors = vectorizer.fit_transform(features)
        
        return feature_vectors, products, vectorizer
    
    def calculate_product_similarity(self, product_id, top_n=10):
        """Calculate similar products based on content features"""
        from .models import ProductSimilarity
        
        feature_vectors, products, _ = self.create_product_features()
        
        product_ids = [p.id for p in products]
        if product_id not in product_ids:
            return []
        
        product_idx = product_ids.index(product_id)
        product_vector = feature_vectors[product_idx]
        
        similarities = cosine_similarity(product_vector, feature_vectors)[0]
        
        similar_products = []
        for other_idx, similarity in enumerate(similarities):
            if other_idx != product_idx and similarity > 0:
                similar_products.append((products[other_idx].id, similarity))
        
        similar_products.sort(key=lambda x: x[1], reverse=True)
        
        # Save to database
        for other_product_id, similarity in similar_products[:top_n]:
            ProductSimilarity.objects.update_or_create(
                product1_id=product_id,
                product2_id=other_product_id,
                defaults={'similarity_score': similarity}
            )
        
        return similar_products[:top_n]
    
    def get_collaborative_recommendations(self, user_id, top_n=20):
        """Get recommendations based on collaborative filtering"""
        from .models import UserSimilarity, UserInteraction, Product
        
        similar_users = UserSimilarity.objects.filter(
            user1_id=user_id
        ).order_by('-similarity_score')[:10]
        
        if not similar_users:
            self.calculate_user_similarity(user_id)
            similar_users = UserSimilarity.objects.filter(
                user1_id=user_id
            ).order_by('-similarity_score')[:10]
        
        recommendations = defaultdict(float)
        
        for similarity in similar_users:
            similar_user_id = similarity.user2_id
            similar_user_interactions = UserInteraction.objects.filter(
                user_id=similar_user_id
            ).exclude(product__user_id=user_id)  # Exclude user's own products
            
            for interaction in similar_user_interactions:
                weight = self.interaction_weights.get(interaction.interaction_type, 1.0)
                recommendations[interaction.product_id] += weight * similarity.similarity_score
        
        # Get top recommendations
        sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
        product_ids = [item[0] for item in sorted_recommendations[:top_n]]
        
        return Product.objects.filter(id__in=product_ids, is_active=True)
    
    def get_content_based_recommendations(self, user_id, top_n=20):
        """Get recommendations based on content similarity to user's interactions"""
        from .models import UserInteraction, ProductSimilarity
        
        # Get user's interacted products
        user_interactions = UserInteraction.objects.filter(
            user_id=user_id
        ).select_related('product')
        
        if not user_interactions:
            return Product.objects.none()
        
        recommendations = defaultdict(float)
        
        for interaction in user_interactions:
            product_id = interaction.product_id
            weight = self.interaction_weights.get(interaction.interaction_type, 1.0)
            
            # Get similar products
            similar_products = ProductSimilarity.objects.filter(
                product1_id=product_id
            ).order_by('-similarity_score')[:10]
            
            if not similar_products:
                self.calculate_product_similarity(product_id)
                similar_products = ProductSimilarity.objects.filter(
                    product1_id=product_id
                ).order_by('-similarity_score')[:10]
            
            for similarity in similar_products:
                if similarity.product2_id != product_id:  # Exclude the same product
                    recommendations[similarity.product2_id] += weight * similarity.similarity_score
        
        # Get top recommendations
        sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
        product_ids = [item[0] for item in sorted_recommendations[:top_n]]
        
        return Product.objects.filter(id__in=product_ids, is_active=True).exclude(user_id=user_id)
    
    def get_hybrid_recommendations(self, user_id, top_n=20, collaborative_weight=0.6, content_weight=0.4):
        """Combine collaborative and content-based recommendations"""
        from .models import Product
        
        collaborative_recs = self.get_collaborative_recommendations(user_id, top_n * 2)
        content_recs = self.get_content_based_recommendations(user_id, top_n * 2)
        
        recommendations = defaultdict(float)
        
        # Add collaborative recommendations with weight
        for product in collaborative_recs:
            recommendations[product.id] += collaborative_weight
        
        # Add content-based recommendations with weight
        for product in content_recs:
            recommendations[product.id] += content_weight
        
        # Get top recommendations
        sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
        product_ids = [item[0] for item in sorted_recommendations[:top_n]]
        
        return Product.objects.filter(id__in=product_ids, is_active=True).exclude(user_id=user_id)
    
    def get_popular_products(self, top_n=20, days=30):
        """Fallback: Get popular products from recent interactions"""
        from .models import UserInteraction, Product
        from django.db.models import Count
        
        recent_date = datetime.now() - timedelta(days=days)
        
        popular_products = Product.objects.filter(
            userinteraction__timestamp__gte=recent_date,
            is_active=True
        ).annotate(
            interaction_count=Count('userinteraction')
        ).order_by('-interaction_count')[:top_n]
        
        return popular_products