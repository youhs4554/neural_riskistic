from collections import deque

def int_to_bytes(number):
    return number.to_bytes(length=(8 + (number + (number < 0)).bit_length()) // 8, byteorder='big', signed=True)

def int_from_bytes(binary_data):
    return int.from_bytes(binary_data, byteorder='big', signed=True)

def rotate(d, n=1):
    """
    @param d: input python dictionary
    @param n: number of times to rotate it; default:1

    @return do: output dict rotated n times
    ex: d = {34: 'apple', 65: 'ball', 32: 'cat', 78: 'dog'}
        rotate(d, 1) -> {34: 'dog', 65: 'apple', 32: 'ball', 78: 'cat'}
    """

    # Get the values of the dict and put them into a deque collection that contains a rotate method
    do = deque(d.values())
    do.rotate(n)  # rotate the values by n
    do = dict(zip(d.keys(), do))  # recombine the keys and values

    return do
