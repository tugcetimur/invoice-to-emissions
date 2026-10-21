from src.validate import is_grounded, number_candidates


def test_plain_integer_is_found():
    assert is_grounded(404, "Consumption: 404 kWh")


def test_invented_number_is_not_found():
    text = "Usage: 842 KWH\nAmount payable: EUR 210.50"
    assert not is_grounded(842000, text)


def test_comma_thousands_separator():
    assert is_grounded(3200, "Consumption: 3,200 kWh")


def test_european_number_format():
    assert is_grounded(1234.5, "Consumption: 1.234,5 kWh")
    assert is_grounded(1287.6, "Total due: EUR 1.287,60")


def test_decimal_comma():
    assert is_grounded(98.4, "Total a pagar: 98,40 EUR")


def test_ambiguous_separator_has_both_readings():
    assert number_candidates("1,234") == {1234.0, 1.234}


def test_one_or_two_digits_after_separator_is_a_decimal():
    assert number_candidates("12,5") == {12.5}
    assert not is_grounded(125, "Usage: 12,5 MWh")


def test_number_inside_a_longer_number_does_not_count():
    assert not is_grounded(842, "Customer no: 8420011")
