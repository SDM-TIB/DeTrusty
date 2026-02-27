from collections import Counter


def make_hashable(item):
    if isinstance(item, dict):
        return tuple(sorted((k, make_hashable(v)) for k, v in item.items()))
    return item


def is_equal(queue_1, queue_2):
    items_1, items_2 = [], []

    tmp = queue_1.get()
    while tmp != 'EOF':
        items_1.append(tmp)
        tmp = queue_1.get()

    tmp = queue_2.get()
    while tmp != 'EOF':
        items_2.append(tmp)
        tmp = queue_2.get()

    if len(items_1) != len(items_2):
        print(f'Size mismatch: queue_1 has {len(items_1)}, queue_2 has {len(items_2)}')
        return False

    hashable_1 = Counter(make_hashable(i) for i in items_1)
    hashable_2 = Counter(make_hashable(i) for i in items_2)

    if hashable_1 != hashable_2:
        for item in items_1:
            if make_hashable(item) not in hashable_2:
                print('Only in queue_1:', item)
        for item in items_2:
            if make_hashable(item) not in hashable_1:
                print('Only in queue_2:', item)
        return False

    return True
