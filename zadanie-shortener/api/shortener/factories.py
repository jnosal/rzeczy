import factory


class ShortenedUrlFactory(factory.django.DjangoModelFactory):
    signature = factory.Sequence(lambda n: "test%s" % n)
    url = factory.Sequence(lambda n: "https://www.test%s.com" % n)

    class Meta:
        model = "shortener.ShortenedUrl"
