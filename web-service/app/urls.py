from django.urls import path
from .views import purchase, signup
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('purchase/', purchase, name='purchase'),
    path('signup/', signup, name='signup'),
]
