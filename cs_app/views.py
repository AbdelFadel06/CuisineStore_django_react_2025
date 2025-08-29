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




class CategoryListView(generics.ListCreateAPIView):
  queryset = Category.objects.all()
  serializer_class  = CategoryListSerializer
  permission_classes = [permissions.AllowAny]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
  queryset = Category.objects.all()
  serializer_class = CategorySerializer
  permission_classes = [permissions.AllowAny]


class ProductListView(generics.ListCreateAPIView):
  serializer_class = ProductListSerializer
  permission_classes = [permissions.AllowAny]
  filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
  filterset_fields = [ 'category', 'featured', 'in_stock']
  search = ['name', 'description']
  ordering_fields = ['name', 'price', 'created_at']
  ordering = ['-created_at']

  def get_queryset(self):
    queryset = Product.objects.filter(in_stock = True)

    promotion_id =  self.request.query_params.get('promotion')
    if promotion_id:
      try:
        promotion = Promotion.objects.get(id=promotion_id, active= True)
        if promotion.applicable_products.exists():
          queryset = queryset.filter(id__in=promotion.applicable_products.all())
        elif promotion.applicable_categories.exists():
          queryset = queryset.filter(id__in=promotion.applicable_categories.all())
      except Promotion.DoesNotExist:
        pass
    return queryset


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
  serializer_class = ProductSerializer
  permission_classes = [permissions.AllowAny]
  queryset = Product.objects.all()



class PromotionListView(generics.ListCreateAPIView):
  queryset = Promotion.objects.filter(active = True, valid_to__gte=timezone.now())
  serializer_class = PromotionSerializer
  permission_classes = [permissions.AllowAny]


class PromotionDetailView(generics.RetrieveUpdateDestroyAPIView):
  queryset = Promotion.objects.filter(active = True, valid_to__gte=timezone.now())
  serializer_class = PromotionSerializer
  permission_classes = [permissions.AllowAny]


class BlogPostListView(generics.ListCreateAPIView):
  queryset = BlogPost.objects.filter(published=True, published_at__lte=timezone.now())
  serializer_class = BlogPostSerializer
  permission_classes = [permissions.AllowAny]
  ordering = ['-published_at']

class BlogPostDetailView(generics.RetrieveUpdateDestroyAPIView):
  queryset = BlogPost.objects.filter(published=True)
  serializer_class = BlogPostSerializer
  permission_classes = [permissions.AllowAny]


class CartView(generics.RetrieveAPIView):
  serializer_class = CartSerializer
  permission_classes =[permissions.IsAuthenticated]

  def get_object(self):
    cart, created = Cart.objects.get_or_create(user = self.request.user)
    return cart

class AddCartItem(generics.GenericAPIView):
  serializer_class = CartItemSerializer
  permission_classes = [permissions.IsAuthenticated]

  def post(self, request, *args, **kwargs):
    serializer =  self.get_serializer(data = request.data)
    serializer.is_valid(raise_exception = True)
    cart, created = Cart.objects.get_or_create(user = request.user)
    product = Product.objects.get(id =serializer.validated_data['product_id'])
    quantity = serializer.validated_data['quantity']

    if product.inventory.quantity < quantity:
      return Response(
        {'error': 'Stock insuffisant'},
          status=status.HTTP_400_BAD_REQUEST
         )

      cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
        )

      if not created:
        cart_item.quantity += quantity
        cart_item.save()

      return Response(
        {'message': 'Produit ajouté au panier'},
          status=status.HTTP_200_OK
        )


class UpdateCartItemView(generics.UpdateAPIView):
  serializer_class = CartItemSerializer
  permission_classes= [permissions.IsAuthenticated]
  queryset = CartItem.objects.all()

  def get_queryset(self):
    return CartItem.objects.filter(cart__user = self.request.user)

class RemoveCartItemView(generics.DestroyAPIView):
  permission_classes= [permissions.IsAuthenticated]
  queryset = CartItem.objects.all()

  def get_queryset(self):
    return CartItem.objects.filter(cart__user = self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
  serializer_class = OrderSerializer
  permission_classes = [permissions.IsAuthenticated]


  def get_queryset(self):
    return Order.objects.filter(user = self.request.user)


  def perform_create(self, serializer):
    cart = Cart.objects.get(user = self.request.user)
    cart_items = cart.items.all()

    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    tax = 0
    total = subtotal + tax


    order = serializer.save(
      user =self.request.user,
      subtotal =subtotal,
      tax = tax,
      total = total,
      customer_phone=self.request.user.phone
    )

    for cart_item in cart_items:
      OrderItem.objects.create(
        order = order,
        product = cart_item.product,
        quantity = cart_item.quantity,
        price = cart_item.product.price
      )


    cart_items.all.delete()



  @action(detail=True, methods=['post'])
  def cancel(self, request, pk=None):
    order = self.get_object()
    if order.status in ['pending', 'confirmed']:
      orded.status = 'cancelled'
      order.save()
      return Response({'status' : 'Commande Annuler'})
    return Response(
      {
        'error': "Impossible d'annuler cette commande"
      }, status= status.HTTP_400_BAD_REQUEST
    )
