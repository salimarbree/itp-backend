from rest_framework import serializers
from django.contrib.auth.models import User
from .models import RichContent, MediaBlock, HighlightedTerm, TermMediaBlock, AccordionSection


class MediaBlockSerializer(serializers.ModelSerializer):
    media_type_display = serializers.CharField(source='get_media_type_display', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaBlock
        fields = ['id', 'media_type', 'media_type_display', 'title', 'content_text', 'media_url', 'media_file', 'file_url', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_file_url(self, obj):
        if obj.media_file:
            request = self.context.get('request') if self.context else None
            if request:
                return request.build_absolute_uri(obj.media_file.url)
            return obj.media_file.url
        return None


class MediaBlockCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaBlock
        fields = ['media_type', 'title', 'content_text', 'media_url', 'order']


class TermMediaBlockSerializer(serializers.ModelSerializer):
    media_type_display = serializers.CharField(source='get_media_type_display', read_only=True)
    
    class Meta:
        model = TermMediaBlock
        fields = ['id', 'media_type', 'media_type_display', 'title', 'content_text', 'media_url', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class TermMediaBlockCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermMediaBlock
        fields = ['media_type', 'title', 'content_text', 'media_url', 'media_file', 'order']


class HighlightedTermSerializer(serializers.ModelSerializer):
    media_blocks = serializers.SerializerMethodField()

    class Meta:
        model = HighlightedTerm
        fields = ['id', 'term', 'definition', 'language', 'order', 'media_blocks']
        read_only_fields = ['id']

    def get_media_blocks(self, obj):
        blocks = obj.media_blocks.all()
        result = []
        for b in blocks:
            request = self.context.get('request') if self.context else None
            file_url = None
            if b.media_file:
                if request:
                    file_url = request.build_absolute_uri(b.media_file.url)
                else:
                    file_url = b.media_file.url
            result.append({
                'id': b.id,
                'media_type': b.media_type,
                'media_type_display': b.get_media_type_display(),
                'title': b.title,
                'content_text': b.content_text,
                'media_url': b.media_url,
                'file_url': file_url,
                'order': b.order,
            })
        return result


class HighlightedTermCreateSerializer(serializers.ModelSerializer):
    media_blocks = TermMediaBlockCreateSerializer(many=True, required=False)

    class Meta:
        model = HighlightedTerm
        fields = ['term', 'definition', 'language', 'order', 'media_blocks']


class AccordionSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccordionSection
        fields = ['id', 'title', 'content', 'order']
        read_only_fields = ['id']


class AccordionSectionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccordionSection
        fields = ['title', 'content', 'order']


class RichContentListSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    media_blocks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RichContent
        fields = ['id', 'title', 'slug', 'author', 'author_name', 
                  'media_blocks_count', 'is_published', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'author', 'created_at', 'updated_at']
    
    def get_media_blocks_count(self, obj):
        return obj.media_blocks.count()


class RichContentDetailSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    media_blocks = MediaBlockSerializer(many=True, read_only=True)
    terms = HighlightedTermSerializer(many=True, read_only=True)
    accordion_sections = AccordionSectionSerializer(many=True, read_only=True)
    
    class Meta:
        model = RichContent
        fields = ['id', 'title', 'slug', 'author', 'author_name', 'content',
                  'media_blocks', 'terms', 'accordion_sections',
                  'is_published', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'author', 'created_at', 'updated_at']


class RichContentCreateSerializer(serializers.ModelSerializer):
    media_blocks = MediaBlockCreateSerializer(many=True, required=False)
    terms = HighlightedTermCreateSerializer(many=True, required=False)
    accordion_sections = AccordionSectionCreateSerializer(many=True, required=False)
    
    class Meta:
        model = RichContent
        fields = ['id', 'title', 'slug', 'content', 'is_published', 'media_blocks', 'terms', 'accordion_sections', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        media_blocks_data = validated_data.pop('media_blocks', [])
        terms_data = validated_data.pop('terms', [])
        accordion_data = validated_data.pop('accordion_sections', [])

        rich_content = RichContent.objects.create(**validated_data)

        for block_data in media_blocks_data:
            MediaBlock.objects.create(rich_content=rich_content, **block_data)

        for term_data in terms_data:
            term_media_blocks_data = term_data.pop('media_blocks', [])
            term = HighlightedTerm.objects.create(rich_content=rich_content, **term_data)
            for term_block_data in term_media_blocks_data:
                TermMediaBlock.objects.create(term=term, **term_block_data)

        for section_data in accordion_data:
            AccordionSection.objects.create(rich_content=rich_content, **section_data)

        return rich_content

    def to_representation(self, instance):
        # Return detail serializer output so frontend gets IDs for media_blocks and terms
        detail = RichContentDetailSerializer(instance, context=self.context)
        return detail.data

    def update(self, instance, validated_data):
        media_blocks_data = validated_data.pop('media_blocks', None)
        terms_data = validated_data.pop('terms', None)
        accordion_data = validated_data.pop('accordion_sections', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if media_blocks_data is not None:
            instance.media_blocks.all().delete()
            for block_data in media_blocks_data:
                MediaBlock.objects.create(rich_content=instance, **block_data)

        if terms_data is not None:
            instance.terms.all().delete()
            for term_data in terms_data:
                term_media_blocks_data = term_data.pop('media_blocks', [])
                term = HighlightedTerm.objects.create(rich_content=instance, **term_data)
                for term_block_data in term_media_blocks_data:
                    TermMediaBlock.objects.create(term=term, **term_block_data)

        if accordion_data is not None:
            instance.accordion_sections.all().delete()
            for section_data in accordion_data:
                AccordionSection.objects.create(rich_content=instance, **section_data)

        return instance


class MediaBlockUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaBlock
        fields = ['media_type', 'title', 'content_text', 'media_url', 'media_file', 'order']
