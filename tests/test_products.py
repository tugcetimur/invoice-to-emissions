from src.products import fuel_product_check


def invoice(product):
    return f"Apex Fuels\nInvoice no: X\nDescription: {product}\nConsumption: 900 litre\n"


def test_known_diesel_name_confirms_diesel():
    assert fuel_product_check("diesel", invoice("Diesel B7")) == "confirmed"


def test_known_petrol_names_confirm_petrol():
    assert fuel_product_check("petrol", invoice("Unleaded 95")) == "confirmed"
    assert fuel_product_check("petrol", invoice("Unleaded petrol")) == "confirmed"


def test_wrong_fuel_for_the_product_is_a_contradiction():
    assert fuel_product_check("petrol", invoice("Diesel")) == "contradiction"


def test_unfamiliar_product_name_is_unknown():
    assert fuel_product_check("diesel", invoice("Gasoil (B7)")) == "unknown_product"


def test_missing_product_line_is_unknown():
    assert fuel_product_check("diesel", "Apex Fuels\nConsumption: 900 litre") == "unknown_product"


def test_supplier_name_is_not_used():
    text = "RoadStar Petrol\nDescription: Diesel\nConsumption: 900 litre"
    assert fuel_product_check("diesel", text) == "confirmed"
    assert fuel_product_check("petrol", text) == "contradiction"
