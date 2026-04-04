from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

# Create custom User model with role field for Admin and Engineer distinction
class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('engineer', 'Engineer'),
    ]
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='engineer',
        help_text='User role: admin or engineer'
    )
    
    class Meta:
        db_table = 'api_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_engineer(self):
        return self.role == 'engineer'


# Category model for organizing items
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'category'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


# Item model with name, category, unit, description
class Item(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='items')
    unit = models.CharField(max_length=50, help_text='Unit of measurement (e.g., pcs, kg, liters)')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'item'
        verbose_name = 'Item'
        verbose_name_plural = 'Items'
        ordering = ['name']
        unique_together = ['name', 'category']
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"


# Stock model tracking current quantity for each item
class Stock(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name='stock')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stock'
        verbose_name = 'Stock'
        verbose_name_plural = 'Stocks'
    
    def __str__(self):
        return f"{self.item.name}: {self.quantity} {self.item.unit}"
    
    def clean(self):
        """Prevent negative stock"""
        if self.quantity < 0:
            raise ValidationError('Stock quantity cannot be negative.')


# GoodsReceived model for stock IN transactions
class GoodsReceived(models.Model):
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='goods_received')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    received_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='goods_received')
    received_date = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'goods_received'
        verbose_name = 'Goods Received'
        verbose_name_plural = 'Goods Received'
        ordering = ['-received_date']
    
    def __str__(self):
        return f"GR: {self.item.name} - {self.quantity} {self.item.unit}"
    
    def save(self, *args, **kwargs):
        """Increase stock and create ledger entry on save"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Get or create stock for this item
            stock, created = Stock.objects.get_or_create(item=self.item)
            stock.quantity += self.quantity
            stock.save()
            
            # Create stock ledger entry
            StockLedger.objects.create(
                item=self.item,
                transaction_type='IN',
                quantity=self.quantity,
                balance_after=stock.quantity,
                user=self.received_by,
                reference_type='GoodsReceived',
                reference_id=self.id,
                remarks=self.remarks
            )


# GoodsIssue model for stock OUT transactions with negative stock prevention
class GoodsIssue(models.Model):
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='goods_issues')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    issued_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='goods_issues')
    issued_to = models.CharField(max_length=200, help_text='Person or department receiving the items')
    issued_date = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'goods_issue'
        verbose_name = 'Goods Issue'
        verbose_name_plural = 'Goods Issues'
        ordering = ['-issued_date']
    
    def __str__(self):
        return f"GI: {self.item.name} - {self.quantity} {self.item.unit} to {self.issued_to}"
    
    def clean(self):
        """Prevent issuing more than available stock"""
        try:
            stock = Stock.objects.get(item=self.item)
            if stock.quantity < self.quantity:
                raise ValidationError(f'Insufficient stock. Available: {stock.quantity} {self.item.unit}')
        except Stock.DoesNotExist:
            raise ValidationError('No stock available for this item.')
    
    def save(self, *args, **kwargs):
        """Decrease stock and create ledger entry on save"""
        is_new = self.pk is None
        
        if is_new:
            # Validate stock availability
            self.clean()
        
        super().save(*args, **kwargs)
        
        if is_new:
            # Decrease stock
            stock = Stock.objects.get(item=self.item)
            stock.quantity -= self.quantity
            stock.save()
            
            # Create stock ledger entry
            StockLedger.objects.create(
                item=self.item,
                transaction_type='OUT',
                quantity=self.quantity,
                balance_after=stock.quantity,
                user=self.issued_by,
                reference_type='GoodsIssue',
                reference_id=self.id,
                remarks=f"Issued to: {self.issued_to}. {self.remarks or ''}"
            )


# StockLedger model for tracking all stock movements (history)
class StockLedger(models.Model):
    TRANSACTION_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
    ]
    
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='ledger_entries')
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ledger_entries')
    transaction_date = models.DateTimeField(auto_now_add=True)
    reference_type = models.CharField(max_length=50, help_text='GoodsReceived or GoodsIssue')
    reference_id = models.IntegerField(help_text='ID of the related transaction')
    remarks = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'stock_ledger'
        verbose_name = 'Stock Ledger'
        verbose_name_plural = 'Stock Ledger'
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"{self.transaction_type}: {self.item.name} - {self.quantity} (Balance: {self.balance_after})"
