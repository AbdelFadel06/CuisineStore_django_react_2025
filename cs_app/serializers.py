from rest_framework import serializers
from .models import Category, CartItem, Cart, Product, ProductImage, ProductAttribute, ProductAttributeValue, Payment, Promotion,  BlogPost,  User, UserProfile, Order, OrderItem, Inventory, InventoryHistory
from django.contrib.auth import authenticate

class CategorySerializer(serializers.ModelSerializer):
  class Meta:
    model = Category
    fiels = '__all__'
    read_only = ['slug']

class CategoryListSerializer(serializers.ModelSerializer):
  product_count = serializers.SerializerMethodField()
  class Meta:
    model = Category
    fields = ['id','name', 'slug', 'description', 'image', 'product_count']

  def get_product_count(self, obj):
    return obj.products.count()


class ProductListSerializer(serializers.ModelSerializer):
  image_url = serializers.SerializerMethodField()
  category_name = serializers.CharField(source = 'category.name', read_only = True)

  class Meta:
    model = Product
    fields = ['id', 'name', 'slug', 'price', 'compare_price', 'category_name',
            'image_url', 'featured', 'in_stock']

  def get_image_url(self, obj):
    main_image = obj.images.filter(is_default = True).first()
    if main_image:
      return main_image.image.url
    return None

class ProductImageSerializer(serializers.ModelSerializer):
  class Meta:
    model = Product
    fields = '__all__'


class ProductAttributeValueSerializer(serializers.ModelSerializer):
  attribute_name = serializers.CharField(source = 'attribute.name', read_only = True)
  class Meta:
    model = ProductAttribute
    fields= ['id', 'attribute_name', 'value']


class ProductSerializer(serializers.ModelSerializer):
  images = ProductImageSerializer(many= True, read_only =True)
  attribute_values = ProductAttributeValueSerializer(many=True, read_only = True)
  category_name = serializers.CharField(source = 'category.name', read_only = True)
  in_stock = serializers.BooleanField(read_only = True)

  class Meta:
    model = Product
    fields = ['id', 'name', 'slug', 'description', 'price', 'compare_price',
            'category', 'category_name', 'featured',
            'in_stock', 'images', 'attribute_values',
            'created_at', 'updated_at']
    read_only = ['slug', 'created_at', 'updated_at']



class OrderItemSerializer(serializers.ModelSerializer):
  product_name = serializers.CharField(source = 'product.name', read_only = True)

  class Meta:
    model = OrderItem
    fields = ['id', 'product', 'product_name', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
  items = OrderItemSerializer(many =True, read_only = True)
  status_display = serializers.CharField(source = 'get_status_display', read_only = True)

  class Meta:
    model = Order
    fields = ['id', 'order_number', 'status', 'status_display', 'customer_phone', 'items', 'subtotal', 'tax',
             'total', 'created_at', 'updated_at']
    read_only = ['order_number', 'created_at', 'updated_at']


class CartItemSerializer(serializers.ModelSerializer):
  product_name = serializers.CharField(source='product.name', read_only=True)
  product_price = serializers.DecimalField(source='product.price', read_only=True, max_digits=10, decimal_places=2)
  total_price = serializers.SerializerMethodField()

  class Meta:
    model = CartItem
    fields = ['id', 'product', 'product_name', 'product_price', 'quantity', 'total_price']

  def get_total_price(self, obj):
    return obj.quantity * obj.product.price



class CartSerializer(serializers.ModelSerializer):
  items = CartItemSerializer(many= True, read_only = True)
  total =  serializers.SerializerMethodField()

  class Meta:
    model = Cart
    fields= ['id', 'items', 'total', 'created_at', 'updated_at']

  def get_total (self, obj):
    return sum(item.quantity * item.product.price for item in obj.items.all())



class UserLoginSerializer(serializers.ModelSerializer):
  username = serializers.CharField()
  password = serializers.CharField()

  def validate(self, data):
    user = authenticate(**data)
    if user and user.is_active:
      return user
    raise serializers.ValidationError('Identifiants invalides')

class UserRegistrationSerializer(serializers.ModelSerializer):
  password = serializers.CharField(write_only=True, min_length=8)
  password_confirm = serializers.CharField(write_only=True)

  class Meta:
    model = User
    fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']

  def validate(self, data):
    if data['password'] != data['password_confirm'] :
      raise serializers.ValidationError("Les mots de passe ne correspondent pas")
    return data

  def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
  class Meta:
    model = UserProfile
    fields = '__all__'

class PromotionSerializer(serializers.ModelSerializer):
  class Meta:
    model = Promotion
    fields = '__all__'


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(
        min_value=1,
        help_text="ID du produit à ajouter au panier"
    )
    quantity = serializers.IntegerField(
        min_value=1,
        default=1,
        help_text="Quantité à ajouter (1-10)"
    )

    def validate_product_id(self, value):
        try:
            product = Product.objects.get(id=value)

            if not product.in_stock:
                raise serializers.ValidationError("Ce produit n'est pas en stock")

            if hasattr(product, 'inventory') and product.inventory.quantity < 1:
                raise serializers.ValidationError("Produit en rupture de stock")

            return value

        except Product.DoesNotExist:
            raise serializers.ValidationError("Produit non trouvé")

    def validate(self, data):
        product_id = data['product_id']
        quantity = data['quantity']

        try:
            product = Product.objects.get(id=product_id)

            if hasattr(product, 'inventory'):
                available_stock = product.inventory.quantity
                if available_stock < quantity:
                    raise serializers.ValidationError({
                        'quantity': f"Stock insuffisant. Seulement {available_stock} disponible(s)"
                    })

            return data

        except Product.DoesNotExist:
            raise serializers.ValidationError({
                'product_id': "Produit non trouvé"
            })
