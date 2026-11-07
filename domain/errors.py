class BaseError(Exception):
    pass


class OutOfStockError(BaseError):
    def __init__(self, product_id: int, requested: int, available: int) -> None:
        super().__init__(f"Product {product_id}: requested {requested}, only {available} in stock.")
        self.product_id = product_id
        self.requested = requested
        self.available = available


class InactiveProductError(BaseError):
    def __init__(self, product_id:int) -> None:
        super().__init__(f"Product {product_id} is discontinued.")
        self.product_id = product_id