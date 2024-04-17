def bytesto(data, to, bsize=1024):
    a = {"k": 1, "m": 2, "g": 3, "t": 4, "p": 5, "e": 6}
    r = float(data)
    for i in range(a[to]):
        r = r / bsize

    return r


def flatten(items, seqtypes=(list, tuple)):
    try:
        for i, x in enumerate(items):
            while isinstance(x, seqtypes):
                items[i : i + 1] = x  # noqa: E203
                x = items[i]
    except IndexError:
        pass
    return items


def by_chunk(items, chunk_size=1000):
    bucket = []
    for item in items:
        if len(bucket) >= chunk_size:
            yield bucket
            bucket = []
        bucket.append(item)
    yield bucket
