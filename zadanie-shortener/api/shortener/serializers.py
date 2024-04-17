from rest_framework import serializers


class ShortenRequestSerializer(serializers.Serializer):
    url = serializers.URLField(required=True)
