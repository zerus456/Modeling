# plugin/recommender.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from store.models import Product, OrderItem
import numpy as np

def recommend_products(user, top_n=5):
    products = Product.objects.filter(status="Published")

    product_ids = []
    corpus = []

    for product in products:
        product_ids.append(product.id)
        text = f"{product.name} {product.description or ''} {product.category.name}"
        corpus.append(text)

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus)

    # Lấy sản phẩm user đã mua
    user_orders = OrderItem.objects.filter(order__customer=user)

    user_text = " ".join([
        f"{item.product.name} {item.product.description or ''} {item.product.category.name}"
        for item in user_orders
    ])

    if not user_text:
        return []

    user_vector = vectorizer.transform([user_text])
    similarities = cosine_similarity(user_vector, tfidf_matrix).flatten()

    # Lấy top sản phẩm giống nhất
    top_indices = similarities.argsort()[-top_n:][::-1]
    recommended_ids = [product_ids[i] for i in top_indices]

    recommended_products = Product.objects.filter(id__in=recommended_ids)
    return recommended_products
