from django.db import models
from django.contrib.auth.models import User


class RichContent(models.Model):
    """MS Word-like document with multimedia support."""
    MEDIA_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('youtube', 'YouTube'),
    ]
    
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rich_contents')
    
    # Main content sections (like pages in a document)
    content = models.TextField(default='', blank=True, help_text="Main text content (HTML allowed)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.title.lower().replace(' ', '-').replace('--', '-')[:200]
        super().save(*args, **kwargs)


class MediaBlock(models.Model):
    """Multimedia block (like inserting media in MS Word)."""
    rich_content = models.ForeignKey(RichContent, on_delete=models.CASCADE, related_name='media_blocks')
    media_type = models.CharField(max_length=20, choices=RichContent.MEDIA_TYPES, default='text')
    title = models.CharField(max_length=200)
    
    # For text blocks
    content_text = models.TextField(blank=True, default='', help_text="Rich text content")
    
    # For URL-based media (YouTube, video, audio, image)
    media_url = models.URLField(blank=True, default='', help_text="URL for video/audio/image")
    
    # File upload alternative
    media_file = models.FileField(upload_to='media_blocks/', blank=True, null=True, help_text="Upload audio/video/image file")
    
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['rich_content', 'order']
    
    def __str__(self):
        return f"[{self.get_media_type_display()}] {self.title}"


class HighlightedTerm(models.Model):
    """Interactive highlighted terms in rich content."""
    rich_content = models.ForeignKey(RichContent, on_delete=models.CASCADE, related_name='terms')
    term = models.CharField(max_length=100)
    definition = models.TextField()
    language = models.CharField(max_length=10, default='bn')
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['rich_content', 'order']
    
    def __str__(self):
        return self.term


class TermMediaBlock(models.Model):
    """Media block attached to a highlighted term (image, audio, video, text, youtube)."""
    MEDIA_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('youtube', 'YouTube'),
    ]
    
    term = models.ForeignKey(HighlightedTerm, on_delete=models.CASCADE, related_name='media_blocks')
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES, default='text')
    title = models.CharField(max_length=200)
    content_text = models.TextField(blank=True, default='')
    media_url = models.URLField(blank=True, default='')
    media_file = models.FileField(upload_to='term_media/%Y/%m/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['term', 'order']
    
    def __str__(self):
        return f"[{self.get_media_type_display()}] {self.title}"


class AccordionSection(models.Model):
    """Expandable/collapsible sections (like MS Word outlines)."""
    rich_content = models.ForeignKey(RichContent, on_delete=models.CASCADE, related_name='accordion_sections')
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['rich_content', 'order']
    
    def __str__(self):
        return self.title
