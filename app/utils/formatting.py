def format_float(value) -> str:
    """將浮點數格式化為字串。
    小於 1 的值保留 4 位小數，大於等於 1 的值保留 2 位小數。
    非浮點數原值回傳。
    """
    if not isinstance(value, float):
        return value
    if value < 1:
        return '{:.4f}'.format(value)
    return '{:.2f}'.format(value)


def format_pct(value: float) -> str:
    """將小數轉換為百分比字串，例如 0.25 → '25.00%'。"""
    return '{:.2f}%'.format(value * 100)
