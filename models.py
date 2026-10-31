from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    password_reset_nonce = db.Column(db.String(80))
    role = db.Column(db.String(20), nullable=False, default="customer")
    phone = db.Column(db.String(40))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    id = property(lambda self: self.user_id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.password_reset_nonce = None

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    __tablename__ = "products"
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, default="")
    product_type = db.Column(db.String(80), default="Software")
    sales_price = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    cost_price = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    notes = db.Column(db.Text, default="")
    image = db.Column(db.String(300))
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    plans = db.relationship("Plan", back_populates="product", cascade="all, delete-orphan")


class ProductVariant(db.Model):
    __tablename__ = "product_variants"
    variant_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.product_id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(250), default="")
    price_delta = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)


class Plan(db.Model):
    __tablename__ = "plans"
    plan_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.product_id"), nullable=False)
    plan_name = db.Column(db.String(120), nullable=False)
    billing_cycle = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    minimum_quantity = db.Column(db.Integer, default=1, nullable=False)
    available_from = db.Column(db.Date)
    available_until = db.Column(db.Date)
    auto_close = db.Column(db.Boolean, default=False, nullable=False)
    allow_early_close = db.Column(db.Boolean, default=True, nullable=False)
    allow_pause = db.Column(db.Boolean, default=False, nullable=False)
    allow_renew = db.Column(db.Boolean, default=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    product = db.relationship("Product", back_populates="plans")


class Subscription(db.Model):
    __tablename__ = "subscriptions"
    subscription_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.plan_id"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="Draft", nullable=False)
    payment_terms = db.Column(db.String(100), default="Due on receipt")
    quantity = db.Column(db.Integer, default=1, nullable=False)
    is_paused = db.Column(db.Boolean, default=False, nullable=False)
    customer = db.relationship("User", foreign_keys=[customer_id])
    plan = db.relationship("Plan")
    items = db.relationship("SubscriptionItem", back_populates="subscription", cascade="all, delete-orphan")
    invoices = db.relationship("Invoice", back_populates="subscription")


class SubscriptionItem(db.Model):
    __tablename__ = "subscription_items"
    item_id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey("subscriptions.subscription_id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.product_id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    subscription = db.relationship("Subscription", back_populates="items")
    product = db.relationship("Product")


class Quotation(db.Model):
    __tablename__ = "quotations"
    quotation_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    quotation_date = db.Column(db.Date, nullable=False)
    valid_until = db.Column(db.Date, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    status = db.Column(db.String(20), default="Draft", nullable=False)
    customer = db.relationship("User")
    items = db.relationship("QuotationItem", back_populates="quotation", cascade="all, delete-orphan")


class QuotationItem(db.Model):
    __tablename__ = "quotation_items"
    item_id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey("quotations.quotation_id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.product_id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    quotation = db.relationship("Quotation", back_populates="items")
    product = db.relationship("Product")


class TaxRule(db.Model):
    __tablename__ = "tax_rules"
    tax_id = db.Column(db.Integer, primary_key=True)
    tax_name = db.Column(db.String(100), nullable=False)
    tax_percentage = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True, nullable=False)


class Discount(db.Model):
    __tablename__ = "discounts"
    discount_id = db.Column(db.Integer, primary_key=True)
    discount_name = db.Column(db.String(120), nullable=False)
    discount_type = db.Column(db.String(20), nullable=False)
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    minimum_purchase = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    minimum_quantity = db.Column(db.Integer, default=1, nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    usage_limit = db.Column(db.Integer)
    used_count = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)


class Invoice(db.Model):
    __tablename__ = "invoices"
    invoice_id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(30), unique=True, nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey("subscriptions.subscription_id"))
    customer_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    invoice_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    tax_amount = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    discount_amount = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    status = db.Column(db.String(20), default="Draft", nullable=False)
    is_renewal = db.Column(db.Boolean, default=False, nullable=False)
    renewal_applied = db.Column(db.Boolean, default=False, nullable=False)
    customer = db.relationship("User")
    subscription = db.relationship("Subscription", back_populates="invoices")
    items = db.relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(db.Model):
    __tablename__ = "invoice_items"
    item_id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.invoice_id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.product_id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    invoice = db.relationship("Invoice", back_populates="items")
    product = db.relationship("Product")


class Payment(db.Model):
    __tablename__ = "payments"
    payment_id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.invoice_id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(40), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    transaction_reference = db.Column(db.String(100))
    status = db.Column(db.String(20), default="Pending", nullable=False)
    notes = db.Column(db.Text, default="")
    invoice = db.relationship("Invoice", back_populates="payments")
    customer = db.relationship("User")


class Notification(db.Model):
    __tablename__ = "notifications"
    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    message = db.Column(db.String(300), nullable=False)
    notification_type = db.Column(db.String(40), default="info")
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship("User")
