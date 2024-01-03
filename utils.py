import secrets
import string


def generate_coupon(user_id: int, tool_id: int):
    words = string.ascii_uppercase + string.digits
    coupon = ''.join(secrets.choice(words) for _ in range(31))
    return f'{user_id}{coupon}{tool_id}'[::-1]
