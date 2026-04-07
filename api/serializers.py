from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Category, Item, Stock, GoodsReceived, GoodsIssue, StockLedger


# Custom JWT Token Serializer to include user information
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that includes user role and details in the token response.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims to the token
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        token['is_admin'] = user.is_admin
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user information to the response
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'is_admin': self.user.is_admin,
            'is_engineer': self.user.is_engineer,
        }
        
        return data


# UserSerializer for creating and managing users
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'role', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']
        extra_kwargs = {
            'email': {'required': True},
        }
    
    def validate_email(self, value):
        """Ensure email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_role(self, value):
        """Ensure role is either admin or engineer"""
        if value not in ['admin', 'engineer']:
            raise serializers.ValidationError("Role must be either 'admin' or 'engineer'.")
        return value
    
    def create(self, validated_data):
        """Create user with hashed password"""
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  # Hash the password
        user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user, handling password hashing if provided"""
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


# CategorySerializer for category management
class CategorySerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'items_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_items_count(self, obj):
        """Return count of items in this category"""
        return obj.items.count()


# ItemSerializer for item management
class ItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    current_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Item
        fields = ['id', 'name', 'category', 'category_name', 'unit', 'description', 'current_stock', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_current_stock(self, obj):
        """Return current stock quantity if exists"""
        try:
            return float(obj.stock.quantity)
        except Stock.DoesNotExist:
            return 0.0


# StockSerializer for read-only stock viewing
class StockSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_unit = serializers.CharField(source='item.unit', read_only=True)
    category_name = serializers.CharField(source='item.category.name', read_only=True)
    
    class Meta:
        model = Stock
        fields = ['id', 'item', 'item_name', 'item_unit', 'category_name', 'quantity', 'last_updated']
        read_only_fields = ['id', 'item', 'quantity', 'last_updated']


# GoodsReceivedSerializer for stock IN transactions
class GoodsReceivedSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    received_by_username = serializers.CharField(source='received_by.username', read_only=True)
    
    class Meta:
        model = GoodsReceived
        fields = ['id', 'item', 'item_name', 'quantity', 'received_by', 'received_by_username', 'received_date', 'remarks']
        read_only_fields = ['id', 'received_by', 'received_date']
    
    def validate_quantity(self, value):
        """Ensure quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value
    
    def create(self, validated_data):
        """Set received_by to current user"""
        validated_data['received_by'] = self.context['request'].user
        return super().create(validated_data)


# GoodsIssueSerializer for stock OUT transactions
class GoodsIssueSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    issued_by_username = serializers.CharField(source='issued_by.username', read_only=True)
    available_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = GoodsIssue
        fields = ['id', 'item', 'item_name', 'quantity', 'issued_by', 'issued_by_username', 'issued_to', 'issued_date', 'remarks', 'available_stock']
        read_only_fields = ['id', 'issued_by', 'issued_date']
    
    def get_available_stock(self, obj):
        """Return available stock for the item"""
        try:
            return float(obj.item.stock.quantity)
        except Stock.DoesNotExist:
            return 0.0
    
    def validate_quantity(self, value):
        """Ensure quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value
    
    def validate(self, data):
        """Check if sufficient stock is available"""
        item = data.get('item')
        quantity = data.get('quantity')
        
        try:
            stock = Stock.objects.get(item=item)
            if stock.quantity < quantity:
                raise serializers.ValidationError({
                    'quantity': f'Insufficient stock. Available: {stock.quantity} {item.unit}'
                })
        except Stock.DoesNotExist:
            raise serializers.ValidationError({
                'item': 'No stock available for this item.'
            })
        
        return data
    
    def create(self, validated_data):
        """Set issued_by to current user"""
        validated_data['issued_by'] = self.context['request'].user
        return super().create(validated_data)


# StockLedgerSerializer for read-only ledger viewing
class StockLedgerSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_unit = serializers.CharField(source='item.unit', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    
    class Meta:
        model = StockLedger
        fields = [
            'id', 'item', 'item_name', 'item_unit', 'transaction_type', 'transaction_type_display',
            'quantity', 'balance_after', 'user', 'user_username', 'transaction_date',
            'reference_type', 'reference_id', 'remarks'
        ]
        read_only_fields = ('id',)
