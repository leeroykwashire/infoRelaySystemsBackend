from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Category, Item, Stock, GoodsReceived, GoodsIssue, StockLedger


# Custom User Admin with role field
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    # Add role field to the admin form
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )


# Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at', 'updated_at']
    search_fields = ['name', 'description']
    list_filter = ['created_at']
    ordering = ['name']


# Item Admin
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'unit', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    autocomplete_fields = ['category']


# Stock Admin (read-only)
@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['item', 'quantity', 'last_updated']
    list_filter = ['last_updated']
    search_fields = ['item__name']
    ordering = ['-last_updated']
    readonly_fields = ['item', 'quantity', 'last_updated']
    
    def has_add_permission(self, request):
        """Disable add - stock is created automatically"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable delete - maintain data integrity"""
        return False


# GoodsReceived Admin
@admin.register(GoodsReceived)
class GoodsReceivedAdmin(admin.ModelAdmin):
    list_display = ['item', 'quantity', 'received_by', 'received_date']
    list_filter = ['received_date', 'received_by']
    search_fields = ['item__name', 'remarks']
    ordering = ['-received_date']
    readonly_fields = ['received_date']
    autocomplete_fields = ['item', 'received_by']


# GoodsIssue Admin
@admin.register(GoodsIssue)
class GoodsIssueAdmin(admin.ModelAdmin):
    list_display = ['item', 'quantity', 'issued_by', 'issued_to', 'issued_date']
    list_filter = ['issued_date', 'issued_by']
    search_fields = ['item__name', 'issued_to', 'remarks']
    ordering = ['-issued_date']
    readonly_fields = ['issued_date']
    autocomplete_fields = ['item', 'issued_by']


# StockLedger Admin (read-only)
@admin.register(StockLedger)
class StockLedgerAdmin(admin.ModelAdmin):
    list_display = ['item', 'transaction_type', 'quantity', 'balance_after', 'user', 'transaction_date']
    list_filter = ['transaction_type', 'transaction_date', 'user']
    search_fields = ['item__name', 'remarks']
    ordering = ['-transaction_date']
    readonly_fields = ['item', 'transaction_type', 'quantity', 'balance_after', 'user', 'transaction_date', 'reference_type', 'reference_id', 'remarks']
    
    def has_add_permission(self, request):
        """Disable add - ledger entries are created automatically"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable delete - maintain audit trail"""
        return False

