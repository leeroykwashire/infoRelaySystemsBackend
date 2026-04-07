from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import (
    CustomTokenObtainPairView, current_user_view,
    UserViewSet, CategoryViewSet, ItemViewSet, StockViewSet,
    GoodsReceivedViewSet, GoodsIssueViewSet, GoodsReturnViewSet, StockLedgerViewSet,
    StockReportView, IssuesReportView, LedgerReportView
)

# Create DefaultRouter for automatic URL routing
router = DefaultRouter()

# Register viewsets with the router
router.register(r'users', UserViewSet, basename='user')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'items', ItemViewSet, basename='item')
router.register(r'stocks', StockViewSet, basename='stock')
router.register(r'goods-received', GoodsReceivedViewSet, basename='goods-received')
router.register(r'goods-issues', GoodsIssueViewSet, basename='goods-issue')
router.register(r'goods-returns', GoodsReturnViewSet, basename='goods-return')
router.register(r'ledger', StockLedgerViewSet, basename='ledger')

# URL patterns
urlpatterns = [
    # Authentication endpoints (JWT)
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('user/me/', current_user_view, name='current_user'),
    
    # Router URLs
    path('', include(router.urls)),
    
    # Report endpoints (manual paths)
    path('reports/stock/', StockReportView.as_view(), name='report-stock'),
    path('reports/issues/', IssuesReportView.as_view(), name='report-issues'),
    path('reports/ledger/', LedgerReportView.as_view(), name='report-ledger'),
]
