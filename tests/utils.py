def is_equal(queue_1, queue_2):
    if queue_1.qsize() == queue_2.qsize():
        tmp_1 = queue_1.get()
        tmp_2 = queue_2.get()
        while tmp_1 != 'EOF':
            if tmp_1 != tmp_2:
                print('tuple1', tmp_1)
                print('tuple2', tmp_2)
                return False
            tmp_1 = queue_1.get()
            tmp_2 = queue_2.get()
        return True
    else:
        return False
