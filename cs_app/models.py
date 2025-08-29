from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone


class User(AbstractUser):
  phone = models.CharField(max_length=20)


class UserProfile(models.Model):
  user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  avatar = models.ImageField(upload_to="media/users_profile", blank=True)


class Category(models.Model):
  name = models.CharField(max_length=50)
  slug = models.CharField(unique=True)
  description = models.TextField(blank=True)
  image = models.ImageField(upload_to="media/categories/", blank=True)
  parent =models.ForeignKey('self',on_delete=models.CASCADE, blank=True, null=True, related_name='children')


class Product(models.Model):
  name = models.CharField(max_length=50)
  slug = models.CharField(unique=True)
  description = models.TextField(blank=True)
  price = models.DecimalField(max_digits=10, decimal_places=2)
  compare_price = models.DecimalField(max_digits=10, decimal_places=2)
  category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
  featured = models.BooleanField(default=False)
  in_stock = models.BooleanField(default=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)


class ProductImage(models.Model):
  product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
  image = models.ImageField(upload_to="media/Products", blank=True)
  alt_text = models.CharField(max_length=100, blank=True)
  is_default = models.BooleanField(default=False)


class ProductAttribute(models.Model):
  name = models.CharField(max_length=50)
  description = models.TextField(blank=True)


class ProductAttributeValue(models.Model):
  product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attribute_values')
  attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
  value = models.CharField(max_length=200)


class Inventory(models.Model):
  product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory')
  quantity = models.IntegerField(default=0)
  low_stock = models.IntegerField(default=6)
  updated_at = models.DateTimeField(auto_now=True)


class InventoryHistory(models.Model):
  inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='history')
  quantity_changed = models.IntegerField()
  reason = models.TextField()
  created_at = models.DateTimeField(auto_now_add=True)


class Order(models.Model):
  ORDER_STATUS = (
    ('pending', 'En attente'),
    ('confirmed', 'Confirmer'),
    ('cancelled', 'Annuler'),
    ('refunded', 'Rembourser')
  )
  user = models.ForeignKey(User, on_delete=models.SET_NULL , related_name='orders', null=True, blank=True)
  order_number = models.CharField(max_length=20, unique= True)
  status = models.CharField(choices=ORDER_STATUS, default= ' pending')
  customer_phone = models.CharField(max_length=20)
  tax = models.DecimalField(max_digits=10, decimal_places=2)
  subtotal = models.DecimalField(max_digits=10, decimal_places=2)
  total = models.DecimalField(max_digits=10, decimal_places=2)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)


class OrderItem(models.Model):
  order = models.ForeignKey(Order, on_delete=models.CASCADE , related_name='items')
  product = models.ForeignKey(Product, on_delete=models.CASCADE)
  quantity = models.PositiveIntegerField()
  price = models.DecimalField(max_digits=10, decimal_places=2)


class Payment(models.Model):
  PAYMENT_METHOD = (
    ('momo', 'Mobile Money'),
    ('cash', 'Espece')
  )

  PAYMENT_STATUS = (
    ('pending', 'En attente'),
    ('completed', 'Completer'),
    ('failed', 'Echec'),
    ('refunded', 'Rembourser')
  )

  payment_method = models.CharField(choices=PAYMENT_METHOD)
  payment_status = models.CharField(choices=PAYMENT_STATUS, default='pending')
  order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
  amount = models.DecimalField(max_digits=10 , decimal_places=2)
  transaction_id = models.CharField(max_length=200,  blank=True)
  created_at = models.DateTimeField(auto_now_add=True)


class Cart(models.Model):
  user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
  session_key = models.CharField(max_length=40, null=True, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)


class CartItem(models.Model):
  cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
  product = models.ForeignKey(Product, on_delete=models.CASCADE)
  quantity = models.PositiveIntegerField(default=1)
  added_at = models.DateTimeField(auto_now_add=True)


class Promotion(models.Model):
    # Définir les types de réduction directement dans Promotion
    DISCOUNT_TYPES = (
        ('percentage', 'Pourcentage'),
        ('fixed', 'Montant fixe'),
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    applicable_categories = models.ManyToManyField(Category, blank=True)
    applicable_products = models.ManyToManyField(Product, blank=True)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def is_valid(self):
        """Vérifie si la promotion est actuellement valide"""
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to

    def calculate_discount(self, amount):
        """Calcule le montant de la réduction"""
        if not self.is_valid():
            return 0

        if self.discount_type == 'percentage':
            discount = amount * (self.discount_value / 100)
            # Si vous voulez limiter le discount max pour les pourcentages
            if hasattr(self, 'max_discount'):
                discount = min(discount, self.max_discount)
            return discount
        elif self.discount_type == 'fixed':
            return min(self.discount_value, amount)
        return 0


class BlogPost(models.Model):
  title = models.CharField(max_length=200)
  slug = models.SlugField(unique=True)
  content = models.TextField()
  excerpt = models.TextField(blank=True)
  author = models.ForeignKey(User, on_delete=models.CASCADE)
  featured_image = models.ImageField(upload_to='media/blog/', blank=True)
  published = models.BooleanField(default=False)
  published_at = models.DateTimeField(null=True, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
