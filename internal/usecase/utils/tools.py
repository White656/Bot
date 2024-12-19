def convert_size(size: int, unit: str) -> float:
    """
    Convert a file size from bytes into a human-readable string representation based on the provided
    unit of measurement. A specific representation, expressed in bytes, kilobytes, megabytes, gigabytes,
    or terabytes, is returned formatted to two decimal places.

    Args:
        size (int): File size in bytes to be converted.
        unit (str): Unit index indicating the conversion level (0 for bytes, 1 for kilobytes,
                    2 for megabytes, 3 for gigabytes, 4 for terabytes).

    Returns:
        str: The file size formatted as a string with the specified unit.
    """
    return float("{:.2f}".format(
        size / 1024 ** 0 if unit == 'B' else 1 if unit == 'KB' else 2 if unit == 'MB' else 3 if unit == 'GB' else 4
    ))
