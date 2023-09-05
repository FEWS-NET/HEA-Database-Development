def b74encode(n):
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_`\"!$'()*,-+"
    if n == 0:
        return alphabet[n]
    encoded = ""
    while n > 0:
        n, r = divmod(n, len(alphabet))
        encoded = alphabet[r] + encoded
    return encoded
