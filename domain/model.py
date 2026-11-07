from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from domain import errors


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BaseEntity(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def _touch(self) -> None:
        self.updated_at = utc_now()


class Customer(BaseEntity):
    id: int
    email: EmailStr
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    country: str = Field(pattern=r"^[A-Z]{2}$")   # ISO code: "GR", "DE", "US"
    active: bool = True

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def change_email(self, new_email: str) -> None:
        self.email = new_email
        self._touch()

    def deactivate(self) -> None:
        self.active = False
        self._touch()


Currency = Literal["EUR", "USD", "GBP"]


class Product(BaseEntity):
    id: int
    sku: str = Field(pattern=r"^[A-Z]{3}-\d{4}$")    # stock keeping unit code e.g. "MUG-0001"
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    price: Decimal = Field(gt=0, decimal_places=2)
    currency: Currency
    stock: int = Field(ge=0)
    active: bool = True

    @property
    def in_stock(self) -> bool:
        return self.stock > 0

    def can_fulfil(self, quantity: int) -> bool:
        return self.active and 0 < quantity <= self.stock

    def reserve(self, quantity: int) -> None:
        if not self.active:
            raise errors.InactiveProductError(self.id)
        if not self.can_fulfil(quantity):
            raise errors.OutOfStockError(self.id, requested=quantity, available=self.stock)
        self.stock -= quantity
        self._touch()

    def restock(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Restock quantity must be positive")
        self.stock += quantity
        self._touch()

    def adjust_price(self, factor: Decimal) -> None:
        if factor <= 0:
            raise ValueError("Price factor must be positive")
        self.price = (self.price * factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self._touch()

    def discontinue(self) -> None:
        self.active = False
        self._touch()


class OrderItem(BaseModel):
    product_id: int
    sku: str
    unit_price: Decimal = Field(gt=0, decimal_places=2)
    currency: Currency
    quantity: int = Field(gt=0)

    model_config = ConfigDict(validate_assignment=True)

    # constructor - takes the existing product and makes it an order item
    @classmethod
    def from_product(cls, product: Product, quantity: int) -> "OrderItem":
        product.reserve(quantity)
        return cls(
            product_id=product.id,
            sku=product.sku,
            unit_price=product.price,
            currency=product.currency,
            quantity=quantity,
        )

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


class Order(BaseEntity):
    id: int
    customer_id: int
    currency: Currency
    items: list[OrderItem] = Field(default_factory=list)

    def add_item(self, item: OrderItem) -> None:
        if item.currency != self.currency:
            raise errors.CurrencyMismatchError(self.id, expected=self.currency, got=item.currency)
        self.items.append(item)
        self._touch()

    def get_total(self) -> Decimal:
        return sum((item.subtotal for item in self.items), Decimal("0"))

    def is_empty(self) -> bool:
        return not self.items