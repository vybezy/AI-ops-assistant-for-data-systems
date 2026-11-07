class BaseError(Exception):
    pass


class OutOfStockError(BaseError):
    def __init__(self, product_id: int, requested: int, available: int) -> None:
        super().__init__(f"Product {product_id}: requested {requested}, only {available} in stock.")
        self.product_id = product_id
        self.requested = requested
        self.available = available


class InactiveProductError(BaseError):
    def __init__(self, product_id: int) -> None:
        super().__init__(f"Product {product_id} is discontinued.")
        self.product_id = product_id


class CurrencyMismatchError(BaseError):
    def __init__(self, order_id: int, expected: str, got: str) -> None:
        super().__init__(f"Order {order_id}: expected currency {expected}, got {got}.")
        self.order_id = order_id
        self.expected = expected
        self.got = got


class EmptyOrderError(BaseError):
    def __init__(self, order_id: int) -> None:
        super().__init__(f"Order {order_id} is empty.")
        self.order_id = order_id