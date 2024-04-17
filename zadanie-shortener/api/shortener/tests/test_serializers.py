from ..serializers import ShortenRequestSerializer


def test_ShortenRequestSerializer_is_invalid_when_url_missing():
    serializer = ShortenRequestSerializer(data={})

    assert serializer.is_valid() is False
    error_properties = sorted(serializer.errors.keys())
    assert error_properties == ["url"]


def test_ShortenRequestSerializer_is_invalid_whenn_non_valid_url_provided():
    serializer = ShortenRequestSerializer(data={"url": "invlaid"})

    assert serializer.is_valid() is False
    error_properties = sorted(serializer.errors.keys())
    assert error_properties == ["url"]


def test_ShortenRequestSerializer_is_invalid_invalid():
    serializer = ShortenRequestSerializer(data={"url": "https://www.google.com"})

    assert serializer.is_valid() is True
