# views.py
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from django.utils import timezone
from .models import (
    User, UserProfile, Category, Product, ProductImage,
    ProductAttribute, ProductAttributeValue, ProductReview,
    Inventory, Order, OrderItem, Payment, Cart, CartItem, Promotion, BlogPost
)
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    CategorySerializer, CategoryListSerializer, ProductSerializer,
    ProductListSerializer, OrderSerializer,
    OrderItemSerializer, CartSerializer, CartItemSerializer,
    PromotionSerializer, BlogPostSerializer,
    AddToCartSerializer,
)
from .permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly




class CategoryListView(generics.ListAPIView):
  queryset = Category.objects.all()
  serializer_class  = CategoryListSerializer
  permission_classes = [permissions.AllowAny]


class 
