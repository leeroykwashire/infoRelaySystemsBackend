from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Sum, Count
from datetime import datetime
from .models import User, Category, Item, Stock, GoodsReceived, GoodsIssue, GoodsReturn, StockLedger
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer, CategorySerializer, ItemSerializer, StockSerializer,
    GoodsReceivedSerializer, GoodsIssueSerializer, GoodsReturnSerializer, StockLedgerSerializer
)


# ==================== AUTHENTICATION ====================

# Custom Token View with user information
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view that returns user information along with tokens.
    POST /api/token/
    Body: {"username": "user", "password": "pass"}
    Response: {"access": "...", "refresh": "...", "user": {...}}
    """
    serializer_class = CustomTokenObtainPairSerializer


# Current User Information
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user_view(request):
    """
    Get current authenticated user information.
    GET /api/user/me/
    Response: {"id": 1, "username": "...", "role": "admin", ...}
    """
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': user.role,
        'is_admin': user.is_admin,
        'is_engineer': user.is_engineer,
        'is_active': user.is_active,
        'date_joined': user.date_joined,
    })


# ==================== PERMISSIONS ====================

# Custom permission: Only Admin users can create new users
class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users to create/modify users.
    """
    def has_permission(self, request, view):
        # Allow read operations for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Only admin can create/update/delete users
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


# UserViewSet for user management
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users.
    - List/Retrieve: Any authenticated user
    - Create/Update/Delete: Admin only
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """Optionally filter users"""
        queryset = User.objects.all().order_by('-date_joined')
        return queryset


# CategoryViewSet for category management
class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing categories.
    All authenticated users can view, admins and engineers can create/update/delete.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


# ItemViewSet for item management
class ItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing items.
    All authenticated users can view, admins and engineers can create/update/delete.
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Optionally filter items by category"""
        queryset = Item.objects.all().select_related('category')
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category__id=category)
        return queryset


# StockViewSet for viewing stock (read-only)
class StockViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ReadOnly ViewSet for viewing stock.
    Stock is updated automatically via GoodsReceived and GoodsIssue.
    """
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Optionally filter stock by item or low stock"""
        queryset = Stock.objects.all().select_related('item__category')
        
        # Filter by item
        item = self.request.query_params.get('item', None)
        if item:
            queryset = queryset.filter(item__id=item)
        
        # Filter low stock (quantity <= threshold)
        low_stock = self.request.query_params.get('low_stock', None)
        if low_stock:
            try:
                threshold = float(low_stock)
                queryset = queryset.filter(quantity__lte=threshold)
            except ValueError:
                pass
        
        return queryset


# GoodsReceivedViewSet for stock IN transactions
class GoodsReceivedViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing goods received (stock IN).
    Creates stock ledger entry automatically.
    """
    queryset = GoodsReceived.objects.all()
    serializer_class = GoodsReceivedSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Optionally filter by item or user"""
        queryset = GoodsReceived.objects.all().select_related('item', 'received_by')
        
        # Filter by item
        item = self.request.query_params.get('item', None)
        if item:
            queryset = queryset.filter(item__id=item)
        
        # Filter by user
        user = self.request.query_params.get('user', None)
        if user:
            queryset = queryset.filter(received_by__id=user)
        
        return queryset


# GoodsIssueViewSet for stock OUT transactions
class GoodsIssueViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing goods issues (stock OUT).
    Validates stock availability and creates ledger entry automatically.
    """
    queryset = GoodsIssue.objects.all()
    serializer_class = GoodsIssueSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Optionally filter by item or user"""
        queryset = GoodsIssue.objects.all().select_related('item', 'issued_by')
        
        # Filter by item
        item = self.request.query_params.get('item', None)
        if item:
            queryset = queryset.filter(item__id=item)
        
        # Filter by user
        user = self.request.query_params.get('user', None)
        if user:
            queryset = queryset.filter(issued_by__id=user)
        
        # Filter by issued_to
        issued_to = self.request.query_params.get('issued_to', None)
        if issued_to:
            queryset = queryset.filter(issued_to__icontains=issued_to)
        
        return queryset


# GoodsReturnViewSet for stock RETURN transactions
class GoodsReturnViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing goods returns (stock RETURN).
    Increases stock and creates ledger entry automatically.
    """
    queryset = GoodsReturn.objects.all()
    serializer_class = GoodsReturnSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Optionally filter by item, user, or original issue"""
        queryset = GoodsReturn.objects.all().select_related('item', 'returned_by', 'original_issue')
        
        # Filter by item
        item = self.request.query_params.get('item', None)
        if item:
            queryset = queryset.filter(item__id=item)
        
        # Filter by user
        user = self.request.query_params.get('user', None)
        if user:
            queryset = queryset.filter(returned_by__id=user)
        
        # Filter by original issue
        original_issue = self.request.query_params.get('original_issue', None)
        if original_issue:
            queryset = queryset.filter(original_issue__id=original_issue)
        
        return queryset


# StockLedgerViewSet for viewing ledger history (read-only)
class StockLedgerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ReadOnly ViewSet for viewing stock ledger (history).
    Ledger entries are created automatically by GoodsReceived and GoodsIssue.
    """
    queryset = StockLedger.objects.all()
    serializer_class = StockLedgerSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter ledger by item, user, or transaction type"""
        queryset = StockLedger.objects.all().select_related('item', 'user')
        
        # Filter by item
        item = self.request.query_params.get('item', None)
        if item:
            queryset = queryset.filter(item__id=item)
        
        # Filter by user
        user = self.request.query_params.get('user', None)
        if user:
            queryset = queryset.filter(user__id=user)
        
        # Filter by transaction type
        transaction_type = self.request.query_params.get('transaction_type', None)
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        return queryset


# ==================== REPORTS ====================

# Stock Report API - Current stock levels with filtering
class StockReportView(APIView):
    """
    Report endpoint for current stock levels.
    Allows filtering by date range and user.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get all stocks with item details
        stocks = Stock.objects.all().select_related('item__category')
        
        # Optional filters
        category = request.query_params.get('category', None)
        low_stock_threshold = request.query_params.get('low_stock', None)
        
        if category:
            stocks = stocks.filter(item__category__id=category)
        
        if low_stock_threshold:
            try:
                threshold = float(low_stock_threshold)
                stocks = stocks.filter(quantity__lte=threshold)
            except ValueError:
                pass
        
        # Prepare response data
        data = []
        for stock in stocks:
            data.append({
                'id': stock.id,
                'item_id': stock.item.id,
                'item_name': stock.item.name,
                'category': stock.item.category.name,
                'unit': stock.item.unit,
                'quantity': float(stock.quantity),
                'last_updated': stock.last_updated,
            })
        
        return Response({
            'count': len(data),
            'results': data
        })


# Issues Report API - Goods issued with filtering
class IssuesReportView(APIView):
    """
    Report endpoint for goods issues.
    Allows filtering by date range and user.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get all goods issues
        issues = GoodsIssue.objects.all().select_related('item', 'issued_by')
        
        # Filter by date range
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                issues = issues.filter(issued_date__gte=start)
            except ValueError:
                pass
        
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d')
                issues = issues.filter(issued_date__lte=end)
            except ValueError:
                pass
        
        # Filter by user
        user = request.query_params.get('user', None)
        if user:
            issues = issues.filter(issued_by__id=user)
        
        # Filter by item
        item = request.query_params.get('item', None)
        if item:
            issues = issues.filter(item__id=item)
        
        # Prepare response data
        data = []
        total_quantity = 0
        
        for issue in issues:
            data.append({
                'id': issue.id,
                'item_name': issue.item.name,
                'item_unit': issue.item.unit,
                'quantity': float(issue.quantity),
                'issued_by': issue.issued_by.username,
                'issued_to': issue.issued_to,
                'issued_date': issue.issued_date,
                'remarks': issue.remarks,
            })
            total_quantity += float(issue.quantity)
        
        return Response({
            'count': len(data),
            'total_quantity_issued': total_quantity,
            'results': data
        })


# Ledger Report API - Stock movement history with filtering
class LedgerReportView(APIView):
    """
    Report endpoint for stock ledger (complete history).
    Allows filtering by date range, user, and transaction type.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get all ledger entries
        ledger = StockLedger.objects.all().select_related('item', 'user')
        
        # Filter by date range
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                ledger = ledger.filter(transaction_date__gte=start)
            except ValueError:
                pass
        
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d')
                ledger = ledger.filter(transaction_date__lte=end)
            except ValueError:
                pass
        
        # Filter by user
        user = request.query_params.get('user', None)
        if user:
            ledger = ledger.filter(user__id=user)
        
        # Filter by item
        item = request.query_params.get('item', None)
        if item:
            ledger = ledger.filter(item__id=item)
        
        # Filter by transaction type
        transaction_type = request.query_params.get('transaction_type', None)
        if transaction_type:
            ledger = ledger.filter(transaction_type=transaction_type)
        
        # Prepare response data
        data = []
        for entry in ledger:
            data.append({
                'id': entry.id,
                'item_name': entry.item.name,
                'item_unit': entry.item.unit,
                'transaction_type': entry.transaction_type,
                'transaction_type_display': entry.get_transaction_type_display(),
                'quantity': float(entry.quantity),
                'balance_after': float(entry.balance_after),
                'user': entry.user.username,
                'transaction_date': entry.transaction_date,
                'reference_type': entry.reference_type,
                'reference_id': entry.reference_id,
                'remarks': entry.remarks,
            })
        
        return Response({
            'count': len(data),
            'results': data
        })

