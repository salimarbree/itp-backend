from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import RichContent, MediaBlock, HighlightedTerm, TermMediaBlock, AccordionSection
from .serializers import (
    RichContentListSerializer,
    RichContentDetailSerializer,
    RichContentCreateSerializer,
    MediaBlockSerializer,
    MediaBlockUpdateSerializer,
    HighlightedTermSerializer,
    HighlightedTermCreateSerializer,
    AccordionSectionSerializer,
    AccordionSectionCreateSerializer,
    TermMediaBlockSerializer,
    TermMediaBlockCreateSerializer,
)


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Only author can edit, anyone can read published content."""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            if obj.is_published:
                return True
            return obj.author == request.user
        return obj.author == request.user


class RichContentViewSet(viewsets.ModelViewSet):
    """
    MS Word-like content editor API.
    Create documents with text, audio, video, YouTube, and images.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'title', 'updated_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RichContentDetailSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return RichContentCreateSerializer
        return RichContentListSerializer
    
    def get_queryset(self):
        queryset = RichContent.objects.select_related('author').prefetch_related(
            'media_blocks', 'terms__media_blocks', 'accordion_sections'
        )
        if not self.request.user.is_authenticated:
            return queryset.filter(is_published=True)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish the content."""
        content = self.get_object()
        content.is_published = True
        content.save()
        return Response({'message': 'Content published', 'is_published': True})
    
    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """Unpublish the content."""
        content = self.get_object()
        content.is_published = False
        content.save()
        return Response({'message': 'Content unpublished', 'is_published': False})
    
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """Get preview data for the interactive teaching platform."""
        content = self.get_object()
        
        media_blocks = content.media_blocks.all()
        media_items = []
        for block in media_blocks:
            # Get file URL if uploaded file exists
            file_url = None
            if block.media_file:
                file_url = request.build_absolute_uri(block.media_file.url)
            
            media_items.append({
                'id': block.media_type,
                'label': block.title,
                'icon': {
                    'text': 'A',
                    'image': '🖼',
                    'audio': '🔊',
                    'video': '🎬',
                    'youtube': '▶'
                }.get(block.media_type, '📄'),
                'color': {
                    'text': '#6366f1',
                    'image': '#ec4899',
                    'audio': '#f59e0b',
                    'video': '#ef4444',
                    'youtube': '#ef4444'
                }.get(block.media_type, '#6366f1'),
                'content_text': block.content_text,
                'media_url': block.media_url,
                'file_url': file_url,
                'media_type': block.media_type,
                'media_type_display': block.get_media_type_display()
            })
        
        terms = []
        for term in content.terms.all():
            term_media_blocks = []
            for media_block in term.media_blocks.all():
                media_file_url = None
                if media_block.media_file:
                    media_file_url = request.build_absolute_uri(media_block.media_file.url)
                
                term_media_blocks.append({
                    'id': media_block.id,
                    'media_type': media_block.media_type,
                    'media_type_display': media_block.get_media_type_display(),
                    'title': media_block.title,
                    'content_text': media_block.content_text,
                    'media_url': media_block.media_url,
                    'file_url': media_file_url,
                    'order': media_block.order,
                })
            
            terms.append({
                'id': term.id,
                'term': term.term,
                'definition': term.definition,
                'language': term.language,
                'order': term.order,
                'media_blocks': term_media_blocks
            })
        
        accordion = []
        for section in content.accordion_sections.all():
            accordion.append({
                'id': f"section-{section.id}",
                'title': section.title,
                'content': section.content
            })
        
        return Response({
            'title': content.title,
            'content': content.content,
            'media_blocks': media_items,
            'terms': terms,
            'accordion_sections': accordion
        })


class MediaBlockViewSet(viewsets.ModelViewSet):
    """API for managing individual media blocks."""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return MediaBlockUpdateSerializer
        return MediaBlockSerializer
    
    def get_queryset(self):
        content_id = self.kwargs.get('content_pk')
        return MediaBlock.objects.filter(rich_content_id=content_id)
    
    def perform_create(self, serializer):
        content_id = self.kwargs.get('content_pk')
        rich_content = RichContent.objects.get(id=content_id)
        serializer.save(rich_content=rich_content)


class HighlightedTermViewSet(viewsets.ModelViewSet):
    """API for managing highlighted terms."""
    serializer_class = HighlightedTermSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return HighlightedTermCreateSerializer
        return HighlightedTermSerializer
    
    def get_queryset(self):
        content_id = self.kwargs.get('content_pk')
        return HighlightedTerm.objects.filter(rich_content_id=content_id)
    
    def perform_create(self, serializer):
        content_id = self.kwargs.get('content_pk')
        rich_content = RichContent.objects.get(id=content_id)
        serializer.save(rich_content=rich_content)


class AccordionSectionViewSet(viewsets.ModelViewSet):
    """API for managing accordion sections."""
    serializer_class = AccordionSectionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AccordionSectionCreateSerializer
        return AccordionSectionSerializer

    def get_queryset(self):
        content_id = self.kwargs.get('content_pk')
        return AccordionSection.objects.filter(rich_content_id=content_id)

    def perform_create(self, serializer):
        content_id = self.kwargs.get('content_pk')
        rich_content = RichContent.objects.get(id=content_id)
        serializer.save(rich_content=rich_content)


class TermMediaBlockViewSet(viewsets.ModelViewSet):
    """API for managing media blocks attached to highlighted terms."""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TermMediaBlockCreateSerializer
        return TermMediaBlockSerializer

    def get_queryset(self):
        term_id = self.kwargs.get('term_pk')
        return TermMediaBlock.objects.filter(term_id=term_id)

    def perform_create(self, serializer):
        term_id = self.kwargs.get('term_pk')
        term = HighlightedTerm.objects.get(id=term_id)
        serializer.save(term=term)
