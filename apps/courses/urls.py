from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RichContentViewSet, MediaBlockViewSet, HighlightedTermViewSet, AccordionSectionViewSet, TermMediaBlockViewSet

router = DefaultRouter()
router.register(r'', RichContentViewSet, basename='rich-content')

urlpatterns = [
    path('', include(router.urls)),
    # Nested routes for media blocks
    path('<int:content_pk>/media/', MediaBlockViewSet.as_view({
        'get': 'list', 'post': 'create'
    })),
    path('<int:content_pk>/media/<int:pk>/', MediaBlockViewSet.as_view({
        'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
    })),
    # Nested routes for highlighted terms
    path('<int:content_pk>/terms/', HighlightedTermViewSet.as_view({
        'get': 'list', 'post': 'create'
    })),
    path('<int:content_pk>/terms/<int:pk>/', HighlightedTermViewSet.as_view({
        'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
    })),
    # Nested routes for term media blocks
    path('<int:content_pk>/terms/<int:term_pk>/media/', TermMediaBlockViewSet.as_view({
        'get': 'list', 'post': 'create'
    })),
    path('<int:content_pk>/terms/<int:term_pk>/media/<int:pk>/', TermMediaBlockViewSet.as_view({
        'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
    })),
    # Nested routes for accordion sections
    path('<int:content_pk>/sections/', AccordionSectionViewSet.as_view({
        'get': 'list', 'post': 'create'
    })),
    path('<int:content_pk>/sections/<int:pk>/', AccordionSectionViewSet.as_view({
        'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
    })),
]
