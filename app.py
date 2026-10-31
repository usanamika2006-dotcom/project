import os
import secrets
import smtplib
from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from email.message import EmailMessage
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from sqlalchemy import func
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from models import (
    db, User, Product, ProductVariant, Plan, Subscription, SubscriptionItem,
    Quotation, QuotationItem, TaxRule, Discount, Invoice, InvoiceItem,
    Payment, Notification,
)


BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, instance_path=str(BASE_DIR / "instance"))
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", secrets.token_hex(32)),
    SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", f"sqlite:///{app.instance_path}/brightloop.db"),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)
Path(app.instance_path).mkdir(parents=True, exist_ok=True)
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

ROLE_HOME = {"admin": "admin_dashboard", "staff": "staff_dashboard", "customer": "customer_dashboard"}
CURRENCY = os.environ.get("CURRENCY_SYMBOL", "₹")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def role_required(*roles):
    def decorate(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorate


def money(value):
    try:
        return Decimal(str(value or 0)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


def form_money(key, default="0"):
    value = Decimal(request.form.get(key, default).strip())
    if not value.is_finite() or value < 0:
        raise ValueError(f"{key.replace('_', ' ').title()} must be a non-negative amount.")
    return value.quantize(Decimal("0.01"))


def form_date(key, default=None):
    raw = request.form.get(key, "").strip()
    return date.fromisoformat(raw) if raw else default


def parse_int(key, default=1, minimum=1):
    value = int(request.form.get(key, default))
    if value < minimum:
        raise ValueError(f"{key.replace('_', ' ').title()} must be at least {minimum}.")
    return value


def safe_commit():
    try:
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        g.db_failed = True
        app.logger.exception("Database operation failed")
        flash("The change could not be saved. Check the values and try again.", "error")
        return False


def notify(user_id, message, kind="info"):
    db.session.add(Notification(user_id=user_id, message=message, notification_type=kind))


def send_password_reset_email(user, reset_url):
    host = os.environ.get("SMTP_HOST")
    if not host:
        app.logger.warning("Password reset requested for %s but SMTP_HOST is not configured.", user.email)
        return False
    message = EmailMessage()
    message["Subject"] = "Reset your Memzo password"
    message["From"] = os.environ.get("MAIL_FROM", os.environ.get("SMTP_USER", "no-reply@brightloop.local"))
    message["To"] = user.email
    message.set_content(f"Use this link within one hour to reset your Memzo password:\n\n{reset_url}\n\nIf you did not request this, ignore this message.")
    try:
        with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", "587")), timeout=10) as server:
            server.starttls()
            smtp_user, smtp_password = os.environ.get("SMTP_USER"), os.environ.get("SMTP_PASSWORD")
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(message)
        return True
    except (OSError, smtplib.SMTPException, ValueError):
        app.logger.exception("Password reset email delivery failed.")
        return False


def cycle_end(start, cycle):
    if cycle == "daily":
        return start + timedelta(days=1)
    if cycle == "weekly":
        return start + timedelta(days=7)
    months = 12 if cycle == "yearly" else 1
    target_month = start.month - 1 + months
    year, month = start.year + target_month // 12, target_month % 12 + 1
    return date(year, month, min(start.day, monthrange(year, month)[1]))


def active_tax_rate():
    rules = TaxRule.query.filter_by(is_active=True).all()
    return sum((money(rule.tax_percentage) for rule in rules), Decimal("0")) / Decimal("100")


def eligible_discount(subtotal, quantity):
    today = date.today()
    candidates = Discount.query.filter_by(is_active=True).all()
    eligible = []
    for discount in candidates:
        if discount.start_date and discount.start_date > today:
            continue
        if discount.end_date and discount.end_date < today:
            continue
        if discount.usage_limit is not None and discount.used_count >= discount.usage_limit:
            continue
        if quantity < discount.minimum_quantity or subtotal < money(discount.minimum_purchase):
            continue
        value = money(discount.discount_value)
        amount = subtotal * value / Decimal("100") if discount.discount_type == "percentage" else value
        eligible.append((min(subtotal, amount).quantize(Decimal("0.01")), discount))
    return max(eligible, key=lambda pair: pair[0]) if eligible else (Decimal("0.00"), None)


def make_invoice(customer, plan, quantity, subscription=None, status="Confirmed", discount_amount=Decimal("0.00"), is_renewal=False):
    today = date.today()
    subtotal = money(plan.price) * quantity
    taxable = max(Decimal("0.00"), subtotal - discount_amount)
    tax = (taxable * active_tax_rate()).quantize(Decimal("0.01"))
    invoice = Invoice(
        invoice_number=f"BL-{today:%y%m%d}-{secrets.token_hex(3).upper()}",
        subscription=subscription, customer_id=customer.user_id,
        invoice_date=today, due_date=today + timedelta(days=14),
        subtotal=subtotal, tax_amount=tax, discount_amount=discount_amount,
        total_amount=taxable + tax, status=status, is_renewal=is_renewal,
    )
    db.session.add(invoice)
    db.session.flush()
    db.session.add(InvoiceItem(
        invoice_id=invoice.invoice_id, product_id=plan.product_id,
        quantity=quantity, unit_price=money(plan.price), tax_amount=tax,
        total_amount=taxable + tax,
    ))
    return invoice


def successful_payment_total(invoice):
    return sum((money(payment.amount) for payment in invoice.payments if payment.status == "successful"), Decimal("0.00"))


def settle_invoice(invoice):
    invoice.status = "Paid"
    subscription = invoice.subscription
    if not subscription:
        return
    subscription.status = "Active"
    if subscription.is_paused:
        subscription.is_paused = False
    if invoice.is_renewal and not invoice.renewal_applied:
        renewal_start = max(subscription.expiry_date, date.today())
        subscription.expiry_date = cycle_end(renewal_start, subscription.plan.billing_cycle)
        invoice.renewal_applied = True


def customer_scope(query, field):
    if current_user.role == "customer":
        return query.filter(field == current_user.user_id)
    return query


@app.context_processor
def shared_context():
    return {"currency": CURRENCY, "csrf_token": session.setdefault("csrf_token", secrets.token_hex(24)),
            "now_year": date.today().year,
            "unread_count": Notification.query.filter_by(user_id=current_user.user_id, is_read=False).count() if current_user.is_authenticated else 0}


@app.before_request
def protect_post_forms():
    if request.method == "POST":
        expected = session.get("csrf_token")
        provided = request.form.get("csrf_token")
        if not expected or not provided or not secrets.compare_digest(expected, provided):
            abort(400, description="Invalid form token. Refresh the page and try again.")


@app.route("/")
def index():
    products = Product.query.filter_by(is_published=True, is_active=True).order_by(Product.product_name).limit(3).all()
    return render_template("index.html", products=products)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name, email = request.form.get("name", "").strip(), request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if len(name) < 2 or "@" not in email or len(password) < 10:
            flash("Enter your name, a valid email, and a password of at least 10 characters.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
        else:
            user = User(name=name, email=email, role="customer", phone=request.form.get("phone", "").strip())
            user.set_password(password)
            db.session.add(user)
            if safe_commit():
                login_user(user)
                flash("Your account is ready.", "success")
                return redirect(url_for("customer_dashboard"))
    return render_template("auth/register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(request.form.get("password", "")):
            login_user(user, remember=bool(request.form.get("remember")))
            return redirect(url_for(ROLE_HOME[user.role]))
        flash("Email or password is incorrect.", "error")
    return render_template("auth/login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("index"))


@app.route("/setup", methods=["GET", "POST"])
def first_admin_setup():
    if User.query.filter_by(role="admin").first():
        abort(404)
    if request.method == "POST":
        name, email, password = request.form.get("name", "").strip(), request.form.get("email", "").strip().lower(), request.form.get("password", "")
        if len(name) < 2 or "@" not in email or len(password) < 12:
            flash("Provide a name, valid email, and password with at least 12 characters.", "error")
        elif User.query.filter_by(email=email).first():
            flash("That email is already in use.", "error")
        else:
            admin = User(name=name, email=email, role="admin")
            admin.set_password(password)
            db.session.add(admin)
            if safe_commit():
                login_user(admin)
                return redirect(url_for("admin_dashboard"))
    return render_template("auth/setup.html")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_reset_nonce = secrets.token_urlsafe(32)
            if safe_commit():
                serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
                token = serializer.dumps({"user_id": user.user_id, "nonce": user.password_reset_nonce}, salt="brightloop-password-reset")
                send_password_reset_email(user, url_for("reset_password", token=token, _external=True))
        flash("If an account matches that email, password reset instructions will be sent.", "info")
        return redirect(url_for("login"))
    return render_template("auth/forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    try:
        payload = serializer.loads(token, salt="brightloop-password-reset", max_age=3600)
        user = db.session.get(User, int(payload.get("user_id", 0)))
        if not user or not user.password_reset_nonce or not secrets.compare_digest(user.password_reset_nonce, str(payload.get("nonce", ""))):
            raise BadSignature("Expired or already used token")
    except (BadSignature, SignatureExpired, ValueError, TypeError):
        flash("This password reset link is invalid or has expired. Request a new one.", "error")
        return redirect(url_for("forgot_password"))
    if request.method == "POST":
        password = request.form.get("password", "")
        if len(password) < 10:
            flash("Use a password with at least 10 characters.", "error")
        else:
            user.set_password(password)
            user.password_reset_nonce = None
            if safe_commit():
                flash("Your password has been updated. Sign in with your new password.", "success")
                return redirect(url_for("login"))
    return render_template("auth/reset_password.html")


@app.get("/products")
def products():
    items = Product.query.filter_by(is_published=True, is_active=True)
    search = request.args.get("q", "").strip()
    if search:
        items = items.filter(Product.product_name.ilike(f"%{search}%"))
    return render_template("products.html", products=items.order_by(Product.product_name).all(), search=search)


@app.get("/products/<int:product_id>")
def product_detail(product_id):
    product = Product.query.filter_by(product_id=product_id, is_published=True, is_active=True).first_or_404()
    plans = Plan.query.filter_by(product_id=product_id, is_active=True).all()
    return render_template("product_detail.html", product=product, plans=plans)


@app.route("/checkout/<int:plan_id>", methods=["GET", "POST"])
@login_required
def checkout(plan_id):
    if current_user.role != "customer":
        abort(403)
    plan = Plan.query.join(Product).filter(Plan.plan_id == plan_id, Plan.is_active.is_(True), Product.is_published.is_(True), Product.is_active.is_(True)).first_or_404()
    existing_subscription = Subscription.query.filter(
        Subscription.customer_id == current_user.user_id,
        Subscription.plan_id == plan.plan_id,
        Subscription.status.in_(["Confirmed", "Active"]),
        Subscription.expiry_date >= date.today(),
    ).first()
    if existing_subscription:
        flash("You already have a current subscription to this plan.", "info")
        return redirect(url_for("customer_section", section="subscriptions"))
    if request.method == "POST":
        try:
            quantity = parse_int("quantity", plan.minimum_quantity, plan.minimum_quantity)
            if plan.available_from and plan.available_from > date.today():
                raise ValueError("This plan is not available yet.")
            if plan.available_until and plan.available_until < date.today():
                raise ValueError("This plan is no longer available.")
            outcome = request.form.get("payment_result", "successful")
            if outcome not in {"successful", "pending", "failed"}:
                raise ValueError("Select a valid simulated payment result.")
            today = date.today()
            subscription = None
            if outcome != "failed":
                subscription = Subscription(customer_id=current_user.user_id, plan_id=plan.plan_id,
                    start_date=today, expiry_date=cycle_end(today, plan.billing_cycle),
                    status="Active" if outcome == "successful" else "Confirmed", quantity=quantity)
                db.session.add(subscription)
                db.session.flush()
                subtotal = money(plan.price) * quantity
                tax = (subtotal * active_tax_rate()).quantize(Decimal("0.01"))
                db.session.add(SubscriptionItem(subscription_id=subscription.subscription_id,
                    product_id=plan.product_id, quantity=quantity, unit_price=money(plan.price),
                    tax_amount=tax, total_amount=subtotal + tax))
            subtotal = money(plan.price) * quantity
            discount_amount, discount = eligible_discount(subtotal, quantity)
            invoice = make_invoice(current_user, plan, quantity, subscription, discount_amount=discount_amount)
            payment = Payment(invoice_id=invoice.invoice_id, customer_id=current_user.user_id,
                amount=money(invoice.total_amount), payment_method=request.form.get("payment_method", "simulated"),
                transaction_reference=f"SIM-{secrets.token_hex(5).upper()}", status=outcome,
                notes="Simulated payment; no payment gateway was contacted.")
            db.session.add(payment)
            if outcome == "successful":
                settle_invoice(invoice)
                if discount:
                    discount.used_count += 1
            notify(current_user.user_id, f"Invoice {invoice.invoice_number} is ready to review.", "invoice")
            if subscription:
                notify(current_user.user_id, f"Your {plan.product.product_name} subscription is {subscription.status.lower()}.", "subscription")
            notify(current_user.user_id, f"Payment {outcome} for invoice {invoice.invoice_number}.", "payment")
            if safe_commit():
                flash("Purchase complete." if outcome == "successful" else f"Payment marked {outcome}.", "success" if outcome == "successful" else "info")
                return redirect(url_for("customer_section", section="invoices"))
        except (ValueError, InvalidOperation) as exc:
            db.session.rollback()
            flash(str(exc), "error")
    subtotal = money(plan.price) * plan.minimum_quantity
    discount_amount, _discount = eligible_discount(subtotal, plan.minimum_quantity)
    tax_amount = ((subtotal - discount_amount) * active_tax_rate()).quantize(Decimal("0.01"))
    return render_template("checkout.html", plan=plan, discount_amount=discount_amount,
        checkout_total=subtotal - discount_amount + tax_amount, estimated_tax=tax_amount)


def dashboard_data(role):
    base = {"customers": User.query.filter_by(role="customer").count(),
            "subscriptions": Subscription.query.filter_by(status="Active").count(),
            "invoices": Invoice.query.filter(Invoice.status != "Paid").count(),
            "revenue": db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter_by(status="successful").scalar() or 0}
    if role == "customer":
        base.update(subscriptions=Subscription.query.filter_by(customer_id=current_user.user_id).count(),
                    invoices=Invoice.query.filter_by(customer_id=current_user.user_id).count(),
                    payments=Payment.query.filter_by(customer_id=current_user.user_id, status="successful").count())
    return base


@app.get("/admin")
@role_required("admin")
def admin_dashboard():
    return render_template("admin/admin_dashboard.html", stats=dashboard_data("admin"),
        greeting="YOUR BUSINESS, AT A GLANCE", heading="A brighter overview",
        subheading="Here is what is happening across Brightloop today.",
        recent=Invoice.query.order_by(Invoice.invoice_date.desc()).limit(6).all())


@app.get("/staff")
@role_required("staff")
def staff_dashboard():
    return render_template("staff/staff_dashboard.html", stats=dashboard_data("staff"),
        greeting="YOUR WORKSPACE", heading="Good work starts here",
        subheading="Stay on top of customer operations and daily activity.",
        recent=Invoice.query.order_by(Invoice.invoice_date.desc()).limit(6).all())


@app.get("/customer")
@role_required("customer")
def customer_dashboard():
    return render_template("customer/customer_dashboard.html", stats=dashboard_data("customer"),
        greeting="YOUR BRIGHTLOOP ACCOUNT", heading="Your workspace, in one place",
        subheading="A clear view of your products, subscriptions, and payments.",
        subscriptions=Subscription.query.filter_by(customer_id=current_user.user_id).order_by(Subscription.start_date.desc()).limit(5).all(),
        invoices=Invoice.query.filter_by(customer_id=current_user.user_id).order_by(Invoice.invoice_date.desc()).limit(5).all())


ADMIN_SECTIONS = {"products", "plans", "staff", "customers", "subscriptions", "quotations", "invoices", "discounts", "payments", "reports", "settings", "taxes", "variants"}
STAFF_SECTIONS = {"customers", "subscriptions", "quotations", "invoices", "payments", "notifications", "profile"}


def section_rows(section):
    models = {"products": Product, "plans": Plan, "staff": User, "customers": User,
        "subscriptions": Subscription, "quotations": Quotation, "invoices": Invoice,
        "discounts": Discount, "payments": Payment, "taxes": TaxRule, "variants": ProductVariant}
    if section == "staff":
        return User.query.filter_by(role="staff").order_by(User.name).all()
    if section == "customers":
        return User.query.filter_by(role="customer").order_by(User.name).all()
    model = models.get(section)
    if not model:
        return []
    query = model.query
    if section == "subscriptions" and current_user.role == "staff":
        query = query.filter(Subscription.status != "Draft")
    if section == "payments" and current_user.role == "customer":
        query = query.filter_by(customer_id=current_user.user_id)
    return query.order_by(model.query.column_descriptions[0]["entity"].__mapper__.primary_key[0].desc()).limit(200).all()


def admin_page(section):
    if section not in ADMIN_SECTIONS:
        abort(404)
    if section == "reports":
        try:
            start = date.fromisoformat(request.args["start"]) if request.args.get("start") else None
            end = date.fromisoformat(request.args["end"]) if request.args.get("end") else None
            if start and end and end < start:
                raise ValueError
        except ValueError:
            flash("Choose a valid report date range.", "error")
            start = end = None
        invoice_query = Invoice.query
        if start:
            invoice_query = invoice_query.filter(Invoice.invoice_date >= start)
        if end:
            invoice_query = invoice_query.filter(Invoice.invoice_date <= end)
        stats = {"revenue": db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter_by(status="successful").filter(
                    *([Payment.payment_date >= datetime.combine(start, datetime.min.time())] if start else []),
                    *([Payment.payment_date < datetime.combine(end + timedelta(days=1), datetime.min.time())] if end else [])).scalar() or 0,
                 "paid_invoices": invoice_query.filter_by(status="Paid").count(),
                 "overdue": invoice_query.filter(Invoice.status.in_(["Draft", "Confirmed"]), Invoice.due_date < date.today()).count(),
                 "active_subscriptions": Subscription.query.filter_by(status="Active").count(),
                 "upcoming_renewals": Subscription.query.filter(Subscription.status == "Active", Subscription.expiry_date >= date.today(), Subscription.expiry_date <= date.today() + timedelta(days=7)).count()}
        return render_template("admin/admin_reports.html", stats=stats, start=start, end=end)
    if section == "settings":
        return render_template("admin/admin_settings.html", tax_rules=TaxRule.query.all())
    template = f"admin/admin_{section}.html" if section in {"products", "plans", "staff", "customers", "subscriptions", "quotations", "invoices", "discounts", "payments"} else "management.html"
    return render_template(template, section=section, rows=section_rows(section),
        products=Product.query.order_by(Product.product_name).all(), customers=User.query.filter_by(role="customer").all(),
        plans=Plan.query.all(), title=section.replace("_", " ").title())


@app.route("/admin/products/<int:product_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_product(product_id):
    product = db.get_or_404(Product, product_id)
    if request.method == "POST":
        action = request.form.get("action", "save")
        if action in {"activate", "deactivate"}:
            product.is_active = action == "activate"
        else:
            name = request.form.get("product_name", "").strip()
            if len(name) < 2:
                flash("Product name must contain at least two characters.", "error")
                return render_template("admin/record_edit.html", record=product, section="products", products=[])
            try:
                product.product_name = name
                product.product_type = request.form.get("product_type", "Software").strip()
                product.sales_price = form_money("sales_price")
                product.cost_price = form_money("cost_price")
                product.description = request.form.get("description", "").strip()
                product.notes = request.form.get("notes", "").strip()
                product.is_published = bool(request.form.get("is_published"))
                product.is_active = bool(request.form.get("is_active"))
            except (ValueError, InvalidOperation) as exc:
                flash(str(exc), "error")
                return render_template("admin/record_edit.html", record=product, section="products", products=[])
        if safe_commit():
            flash("Product updated.", "success")
            return redirect(url_for("admin_section", section="products"))
    return render_template("admin/record_edit.html", record=product, section="products", products=[])


@app.route("/admin/plans/<int:plan_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_plan(plan_id):
    plan = db.get_or_404(Plan, plan_id)
    products = Product.query.order_by(Product.product_name).all()
    if request.method == "POST":
        try:
            name = request.form.get("plan_name", "").strip()
            product = db.session.get(Product, int(request.form["product_id"]))
            cycle = request.form.get("billing_cycle", "")
            start_date, end_date = form_date("available_from"), form_date("available_until")
            if len(name) < 2 or not product or cycle not in {"daily", "weekly", "monthly", "yearly"}:
                raise ValueError("Enter a plan name, product, and valid billing cycle.")
            if start_date and end_date and end_date < start_date:
                raise ValueError("Availability end date must be after the start date.")
            plan.plan_name = name
            plan.product_id = product.product_id
            plan.billing_cycle = cycle
            plan.price = form_money("price")
            plan.minimum_quantity = parse_int("minimum_quantity")
            plan.available_from, plan.available_until = start_date, end_date
            plan.auto_close = bool(request.form.get("auto_close"))
            plan.allow_early_close = bool(request.form.get("allow_early_close"))
            plan.allow_pause = bool(request.form.get("allow_pause"))
            plan.allow_renew = bool(request.form.get("allow_renew"))
            plan.is_active = bool(request.form.get("is_active"))
        except (ValueError, KeyError, InvalidOperation) as exc:
            flash(str(exc), "error")
            return render_template("admin/record_edit.html", record=plan, section="plans", products=products)
        if safe_commit():
            flash("Plan updated.", "success")
            return redirect(url_for("admin_section", section="plans"))
    return render_template("admin/record_edit.html", record=plan, section="plans", products=products)


@app.route("/manage/customers/<int:user_id>/edit", methods=["GET", "POST"])
@role_required("admin", "staff")
def edit_customer(user_id):
    customer = User.query.filter_by(user_id=user_id, role="customer").first_or_404()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        duplicate = User.query.filter(User.email == email, User.user_id != customer.user_id).first()
        if len(name) < 2 or "@" not in email:
            flash("Enter a customer name and valid email address.", "error")
        elif duplicate:
            flash("That email address is already in use.", "error")
        else:
            customer.name, customer.email = name, email
            customer.phone = request.form.get("phone", "").strip()
            if safe_commit():
                flash("Customer details updated.", "success")
                return redirect(url_for("admin_section", section="customers") if current_user.role == "admin" else url_for("staff_section", section="customers"))
    return render_template("customer_edit.html", customer=customer)


@app.route("/admin/<section>", methods=["GET", "POST"])
@role_required("admin")
def admin_section(section):
    if request.method == "GET":
        return admin_page(section)
    if section not in ADMIN_SECTIONS:
        abort(404)
    action = request.form.get("action", "create")
    g.db_failed = False
    try:
        if action in {"toggle", "delete"}:
            record_id = int(request.form.get("record_id", "0"))
            model = {"products": Product, "plans": Plan, "staff": User, "customers": User,
                     "subscriptions": Subscription, "discounts": Discount, "taxes": TaxRule, "variants": ProductVariant}.get(section)
            record = db.session.get(model, record_id) if model else None
            if not record or (section == "staff" and record.role != "staff") or (section == "customers" and record.role != "customer"):
                abort(404)
            if action == "delete" and section in {"plans", "products", "variants", "discounts", "taxes"}:
                db.session.delete(record)
            elif section == "products":
                record.is_published = not record.is_published
            elif hasattr(record, "is_active"):
                record.is_active = not record.is_active
            elif section == "subscriptions":
                record.status = request.form.get("status", "Closed")
            else:
                abort(400)
            safe_commit()
        elif section == "products":
            product = Product(product_name=request.form.get("product_name", "").strip(),
                product_type=request.form.get("product_type", "Software").strip(), description=request.form.get("description", "").strip(),
                sales_price=form_money("sales_price"), cost_price=form_money("cost_price"), notes=request.form.get("notes", "").strip(),
                is_published=bool(request.form.get("is_published")))
            if not product.product_name: raise ValueError("Product name is required.")
            db.session.add(product); safe_commit()
        elif section == "plans":
            product_id = int(request.form["product_id"])
            product = db.session.get(Product, product_id)
            if not product: raise ValueError("Choose a valid product.")
            plan = Plan(product_id=product_id, plan_name=request.form.get("plan_name", "").strip(),
                billing_cycle=request.form.get("billing_cycle", "monthly"), price=form_money("price"),
                minimum_quantity=parse_int("minimum_quantity"), available_from=form_date("available_from"),
                available_until=form_date("available_until"), auto_close=bool(request.form.get("auto_close")),
                allow_early_close=bool(request.form.get("allow_early_close")), allow_pause=bool(request.form.get("allow_pause")),
                allow_renew=bool(request.form.get("allow_renew")))
            if not plan.plan_name or plan.billing_cycle not in {"daily", "weekly", "monthly", "yearly"}: raise ValueError("Enter a plan name and valid billing cycle.")
            if plan.available_from and plan.available_until and plan.available_until < plan.available_from:
                raise ValueError("Plan availability end date must be after its start date.")
            db.session.add(plan); safe_commit()
        elif section == "staff":
            name, email, password = request.form.get("name", "").strip(), request.form.get("email", "").strip().lower(), request.form.get("password", "")
            if len(name) < 2 or "@" not in email or len(password) < 10: raise ValueError("Enter a name, valid email, and password of at least 10 characters.")
            if User.query.filter_by(email=email).first(): raise ValueError("That email is already registered.")
            user = User(name=name, email=email, role="staff", phone=request.form.get("phone", "").strip()); user.set_password(password)
            db.session.add(user); safe_commit()
        elif section == "subscriptions":
            customer = db.session.get(User, int(request.form["customer_id"]))
            plan = db.session.get(Plan, int(request.form["plan_id"]))
            if not customer or customer.role != "customer" or not plan: raise ValueError("Choose a valid customer and plan.")
            quantity = parse_int("quantity", plan.minimum_quantity, plan.minimum_quantity)
            start = form_date("start_date", date.today()); end = form_date("expiry_date", cycle_end(start, plan.billing_cycle))
            if end <= start: raise ValueError("Expiry date must be after start date.")
            subscription = Subscription(customer_id=customer.user_id, plan_id=plan.plan_id, start_date=start, expiry_date=end,
                status=request.form.get("status", "Confirmed"), quantity=quantity)
            if subscription.status not in {"Draft", "Quotation", "Confirmed", "Active", "Closed"}: raise ValueError("Invalid subscription status.")
            db.session.add(subscription)
            notify(customer.user_id, f"A {plan.product.product_name} subscription was created with status {subscription.status.lower()}.", "subscription")
            safe_commit()
        elif section == "discounts":
            discount = Discount(discount_name=request.form.get("discount_name", "").strip(), discount_type=request.form.get("discount_type", "fixed"),
                discount_value=form_money("discount_value"), minimum_purchase=form_money("minimum_purchase"), minimum_quantity=parse_int("minimum_quantity"),
                start_date=form_date("start_date"), end_date=form_date("end_date"), usage_limit=int(request.form["usage_limit"]) if request.form.get("usage_limit") else None,
                is_active=bool(request.form.get("is_active")))
            if not discount.discount_name or discount.discount_type not in {"fixed", "percentage"}: raise ValueError("Enter a discount name and valid type.")
            if discount.discount_type == "percentage" and discount.discount_value > 100: raise ValueError("Percentage discounts cannot exceed 100%.")
            if discount.start_date and discount.end_date and discount.end_date < discount.start_date:
                raise ValueError("Discount end date must be after its start date.")
            db.session.add(discount); safe_commit()
        elif section == "taxes":
            rule = TaxRule(tax_name=request.form.get("tax_name", "").strip(), tax_percentage=form_money("tax_percentage"), is_active=bool(request.form.get("is_active")))
            if not rule.tax_name or rule.tax_percentage > 100: raise ValueError("Enter a tax name and a percentage up to 100.")
            db.session.add(rule); safe_commit()
        elif section == "variants":
            variant = ProductVariant(product_id=int(request.form["product_id"]), name=request.form.get("name", "").strip(),
                description=request.form.get("description", "").strip(), price_delta=form_money("price_delta"))
            if not variant.name: raise ValueError("Variant name is required.")
            db.session.add(variant); safe_commit()
        elif section == "quotations":
            if action == "status":
                quotation = db.session.get(Quotation, int(request.form["quotation_id"]))
                status = request.form.get("status")
                if not quotation or status not in {"Draft", "Sent", "Accepted", "Rejected", "Expired"}:
                    raise ValueError("Choose a quotation and valid status.")
                quotation.status = status
                notify(quotation.customer_id, f"Quotation QT-{quotation.quotation_id:05d} is now {status.lower()}.", "quotation")
                safe_commit()
            else:
                customer = db.session.get(User, int(request.form["customer_id"]))
                plan = db.session.get(Plan, int(request.form["plan_id"]))
                quantity = parse_int("quantity")
                if not customer or customer.role != "customer" or not plan: raise ValueError("Choose a valid customer and plan.")
                subtotal = money(plan.price) * quantity
                tax = (subtotal * active_tax_rate()).quantize(Decimal("0.01"))
                valid_until = form_date("valid_until", date.today() + timedelta(days=14))
                if valid_until < date.today(): raise ValueError("Quotation validity date cannot be in the past.")
                quotation = Quotation(customer_id=customer.user_id, quotation_date=date.today(),
                    valid_until=valid_until, total_amount=subtotal + tax, status="Draft")
                db.session.add(quotation); db.session.flush()
                db.session.add(QuotationItem(quotation_id=quotation.quotation_id, product_id=plan.product_id, quantity=quantity,
                    unit_price=money(plan.price), tax_amount=tax, total_amount=subtotal + tax))
                notify(customer.user_id, f"A quotation has been prepared for {plan.product.product_name}.", "quotation")
                safe_commit()
        elif section == "invoices":
            invoice = db.session.get(Invoice, int(request.form["invoice_id"]))
            status = request.form.get("status")
            if not invoice or status not in {"Draft", "Confirmed", "Paid", "Cancelled"}: raise ValueError("Choose an invoice and valid status.")
            if status == "Paid" and successful_payment_total(invoice) < money(invoice.total_amount):
                raise ValueError("Record successful payments for the full invoice amount before marking it paid.")
            if status == "Paid":
                settle_invoice(invoice)
            else:
                invoice.status = status
            notify(invoice.customer_id, f"Invoice {invoice.invoice_number} was updated to {status.lower()}.", "invoice")
            safe_commit()
        elif section == "payments":
            invoice = db.session.get(Invoice, int(request.form["invoice_id"]))
            if not invoice: raise ValueError("Choose a valid invoice.")
            if invoice.status == "Paid": raise ValueError("This invoice is already paid.")
            amount = form_money("amount")
            payment = Payment(invoice_id=invoice.invoice_id, customer_id=invoice.customer_id, amount=amount,
                payment_method=request.form.get("payment_method", "manual"), transaction_reference=request.form.get("transaction_reference", "").strip(),
                status=request.form.get("status", "successful"), notes=request.form.get("notes", "").strip())
            if payment.status not in {"successful", "pending", "failed"}: raise ValueError("Invalid payment status.")
            db.session.add(payment)
            if payment.status == "successful":
                paid = sum((money(p.amount) for p in invoice.payments if p.status == "successful"), Decimal("0")) + amount
                if paid >= money(invoice.total_amount): settle_invoice(invoice)
            notify(invoice.customer_id, f"A payment update was recorded for invoice {invoice.invoice_number}.", "payment")
            safe_commit()
        else:
            abort(405)
        if not g.db_failed:
            flash("Changes saved.", "success")
    except (ValueError, KeyError, TypeError, InvalidOperation) as exc:
        db.session.rollback()
        flash(str(exc) or "Check the submitted values.", "error")
    return redirect(url_for("admin_section", section=section))


@app.route("/staff/<section>", methods=["GET", "POST"])
@role_required("staff")
def staff_section(section):
    if section not in STAFF_SECTIONS: abort(404)
    if section == "profile":
        return profile_page("staff")
    if section == "notifications":
        return notifications_page("staff")
    if request.method == "POST":
        if section == "invoices":
            invoice = db.session.get(Invoice, int(request.form.get("invoice_id", 0)))
            if not invoice: abort(404)
            status = request.form.get("status", invoice.status)
            if status not in {"Draft", "Confirmed", "Paid", "Cancelled"}:
                abort(400)
            if status == "Paid" and successful_payment_total(invoice) < money(invoice.total_amount):
                flash("Successful payments covering the full invoice amount are required before marking it paid.", "error")
            else:
                if status == "Paid": settle_invoice(invoice)
                else: invoice.status = status
                notify(invoice.customer_id, f"Invoice {invoice.invoice_number} was updated to {invoice.status.lower()}.", "invoice")
                safe_commit(); flash("Invoice updated.", "success")
        elif section == "subscriptions":
            subscription = db.session.get(Subscription, int(request.form.get("subscription_id", 0)))
            if not subscription: abort(404)
            status = request.form.get("status")
            if status not in {"Draft", "Quotation", "Confirmed", "Active", "Closed"}: abort(400)
            subscription.status = status
            notify(subscription.customer_id, f"Your subscription is now {status.lower()}.", "subscription")
            safe_commit(); flash("Subscription updated.", "success")
        elif section == "payments":
            return create_staff_payment()
        elif section == "quotations":
            if request.form.get("action") == "status":
                return update_staff_quotation()
            return create_staff_quotation()
        return redirect(url_for("staff_section", section=section))
    template = f"staff/staff_{section}.html"
    return render_template(template, section=section, rows=section_rows(section), title=section.title(),
        products=Product.query.all(), customers=User.query.filter_by(role="customer").all(), plans=Plan.query.all(), invoices=Invoice.query.all())


def create_staff_payment():
    try:
        invoice = db.session.get(Invoice, int(request.form["invoice_id"]))
        if not invoice: raise ValueError("Choose a valid invoice.")
        if invoice.status == "Paid": raise ValueError("This invoice is already paid.")
        payment = Payment(invoice_id=invoice.invoice_id, customer_id=invoice.customer_id, amount=form_money("amount"),
            payment_method=request.form.get("payment_method", "manual"), transaction_reference=request.form.get("transaction_reference", "").strip(),
            status=request.form.get("status", "successful"), notes=request.form.get("notes", "").strip())
        if payment.status not in {"successful", "pending", "failed"}: raise ValueError("Invalid payment status.")
        db.session.add(payment)
        if payment.status == "successful":
            paid = successful_payment_total(invoice) + money(payment.amount)
            if paid >= money(invoice.total_amount): settle_invoice(invoice)
        notify(invoice.customer_id, f"A payment update was recorded for invoice {invoice.invoice_number}.", "payment")
        if safe_commit(): flash("Payment recorded.", "success")
    except (ValueError, KeyError, InvalidOperation) as exc:
        db.session.rollback(); flash(str(exc), "error")
    return redirect(url_for("staff_section", section="payments"))


def create_staff_quotation():
    try:
        customer, plan = db.session.get(User, int(request.form["customer_id"])), db.session.get(Plan, int(request.form["plan_id"]))
        quantity = parse_int("quantity")
        if not customer or customer.role != "customer" or not plan: raise ValueError("Choose a valid customer and plan.")
        subtotal = money(plan.price) * quantity
        tax = (subtotal * active_tax_rate()).quantize(Decimal("0.01"))
        valid_until = form_date("valid_until", date.today() + timedelta(days=14))
        if valid_until < date.today(): raise ValueError("Quotation validity date cannot be in the past.")
        quote = Quotation(customer_id=customer.user_id, quotation_date=date.today(), valid_until=valid_until, total_amount=subtotal + tax)
        db.session.add(quote); db.session.flush()
        db.session.add(QuotationItem(quotation_id=quote.quotation_id, product_id=plan.product_id, quantity=quantity, unit_price=money(plan.price), tax_amount=tax, total_amount=subtotal + tax))
        notify(customer.user_id, "A quotation has been prepared for you.", "quotation")
        if safe_commit(): flash("Quotation created.", "success")
    except (ValueError, KeyError, InvalidOperation) as exc:
        db.session.rollback(); flash(str(exc), "error")
    return redirect(url_for("staff_section", section="quotations"))


def update_staff_quotation():
    quote = db.session.get(Quotation, int(request.form.get("quotation_id", 0)))
    status = request.form.get("status")
    if not quote or status not in {"Draft", "Sent", "Accepted", "Rejected", "Expired"}:
        flash("Choose a quotation and valid status.", "error")
    else:
        quote.status = status
        notify(quote.customer_id, f"Quotation QT-{quote.quotation_id:05d} is now {status.lower()}.", "quotation")
        if safe_commit(): flash("Quotation updated.", "success")
    return redirect(url_for("staff_section", section="quotations"))


@app.route("/customer/<section>", methods=["GET", "POST"])
@role_required("customer")
def customer_section(section):
    allowed = {"subscriptions", "invoices", "payments", "notifications", "profile"}
    if section not in allowed: abort(404)
    if section == "profile": return profile_page("customer")
    if section == "notifications": return notifications_page("customer")
    if request.method == "POST":
        if section != "subscriptions": abort(405)
        subscription = Subscription.query.filter_by(
            subscription_id=int(request.form.get("subscription_id", 0)),
            customer_id=current_user.user_id,
        ).first_or_404()
        action = request.form.get("action")
        try:
            if action == "pause":
                if not subscription.plan.allow_pause or subscription.status != "Active":
                    raise ValueError("This subscription cannot be paused right now.")
                subscription.is_paused = True
            elif action == "resume":
                if not subscription.plan.allow_pause or not subscription.is_paused:
                    raise ValueError("This subscription cannot be resumed right now.")
                subscription.is_paused = False
            elif action == "close":
                if not subscription.plan.allow_early_close or subscription.status == "Closed":
                    raise ValueError("Early closure is not available for this plan.")
                subscription.status = "Closed"
                subscription.is_paused = False
            elif action == "renew":
                if not subscription.plan.allow_renew or subscription.is_paused or subscription.status == "Closed":
                    raise ValueError("This subscription cannot be renewed right now.")
                pending_renewal = Invoice.query.filter_by(subscription_id=subscription.subscription_id, is_renewal=True).filter(
                    Invoice.status != "Paid").first()
                if pending_renewal:
                    raise ValueError("A renewal invoice is already awaiting payment. Contact the team to complete it.")
                outcome = request.form.get("payment_result", "successful")
                if outcome not in {"successful", "pending", "failed"}:
                    raise ValueError("Select a valid simulated payment result.")
                amount = money(subscription.plan.price) * subscription.quantity
                discount_amount, discount = eligible_discount(amount, subscription.quantity)
                invoice = make_invoice(current_user, subscription.plan, subscription.quantity,
                    subscription, discount_amount=discount_amount, is_renewal=True)
                db.session.flush()
                payment = Payment(invoice_id=invoice.invoice_id, customer_id=current_user.user_id,
                    amount=money(invoice.total_amount), payment_method="simulated",
                    transaction_reference=f"SIM-{secrets.token_hex(5).upper()}", status=outcome,
                    notes="Simulated renewal payment; no payment gateway was contacted.")
                db.session.add(payment)
                if outcome == "successful":
                    settle_invoice(invoice)
                    if discount:
                        discount.used_count += 1
                elif outcome == "pending":
                    subscription.status = "Confirmed"
                notify(current_user.user_id, f"Renewal payment {outcome} for {subscription.plan.product.product_name}.", "subscription")
            else:
                raise ValueError("Unknown subscription action.")
            if safe_commit():
                flash("Subscription updated.", "success")
        except (ValueError, InvalidOperation) as exc:
            db.session.rollback()
            flash(str(exc), "error")
        return redirect(url_for("customer_section", section="subscriptions"))
    model_map = {"subscriptions": Subscription, "invoices": Invoice, "payments": Payment}
    model = model_map[section]
    field = model.customer_id
    rows = customer_scope(model.query, field).order_by(model.query.column_descriptions[0]["entity"].__mapper__.primary_key[0].desc()).all()
    return render_template(f"customer/customer_{section}.html", section=f"customer_{section}", rows=rows, title=section.replace("_", " ").title())


def profile_page(role):
    if request.method == "POST":
        name, phone = request.form.get("name", "").strip(), request.form.get("phone", "").strip()
        password = request.form.get("new_password", "")
        if len(name) < 2: flash("Name must contain at least two characters.", "error")
        elif password and (len(password) < 10 or not current_user.check_password(request.form.get("current_password", ""))):
            flash("Enter your current password and a new password with at least 10 characters.", "error")
        else:
            current_user.name, current_user.phone = name, phone
            if password: current_user.set_password(password)
            if safe_commit(): flash("Profile updated.", "success")
    return render_template(f"{role}/{role}_profile.html" if role in {"customer", "staff"} else "profile.html")


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    return profile_page(current_user.role)


@app.route("/notifications", methods=["GET", "POST"])
@login_required
def notifications_page(role=None):
    if request.method == "POST":
        notification = db.session.get(Notification, int(request.form.get("notification_id", 0)))
        if notification and notification.user_id == current_user.user_id:
            notification.is_read = True; safe_commit()
        return redirect(request.referrer or url_for("index"))
    rows = Notification.query.filter_by(user_id=current_user.user_id).order_by(Notification.created_at.desc()).all()
    template_role = role or current_user.role
    template = "staff/staff_notifications.html" if template_role == "staff" else "customer/customer_notifications.html"
    return render_template(template, notifications=rows)


@app.route("/invoice/<int:invoice_id>")
@login_required
def invoice_detail(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    if current_user.role == "customer" and invoice.customer_id != current_user.user_id: abort(403)
    if current_user.role not in {"admin", "staff", "customer"}: abort(403)
    return render_template("invoice_detail.html", invoice=invoice)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.errorhandler(403)
def forbidden(_error):
    return render_template("error.html", code=403, message="You do not have permission to access this page."), 403


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, message="We couldn't find that page."), 404


@app.cli.command("create-admin")
def create_admin_command():
    """Create an administrator from environment variables for deployment setup."""
    email, password = os.environ.get("ADMIN_EMAIL", "").strip().lower(), os.environ.get("ADMIN_PASSWORD", "")
    if not email or len(password) < 12:
        raise SystemExit("Set ADMIN_EMAIL and an ADMIN_PASSWORD of at least 12 characters.")
    if User.query.filter_by(email=email).first():
        raise SystemExit("That email already exists.")
    admin = User(name=os.environ.get("ADMIN_NAME", "Administrator"), email=email, role="admin")
    admin.set_password(password); db.session.add(admin); db.session.commit()
    print("Administrator account created.")


@app.cli.command("process-renewals")
def process_renewals_command():
    """Close expired auto-close subscriptions and notify customers of renewals due within seven days."""
    today = date.today()
    now = datetime.utcnow()
    candidates = Subscription.query.filter(Subscription.status == "Active").all()
    changed = 0
    for subscription in candidates:
        if subscription.expiry_date < today and subscription.plan.auto_close:
            subscription.status = "Closed"
            subscription.is_paused = False
            notify(subscription.customer_id,
                f"Your {subscription.plan.product.product_name} subscription closed at the end of its term.", "subscription")
            changed += 1
        elif not subscription.is_paused and today <= subscription.expiry_date <= today + timedelta(days=7):
            message = f"Your {subscription.plan.product.product_name} subscription renews on {subscription.expiry_date:%b %d, %Y}."
            recent = Notification.query.filter_by(user_id=subscription.customer_id, message=message).filter(
                Notification.created_at >= now - timedelta(days=7)).first()
            if not recent:
                notify(subscription.customer_id, message, "renewal")
                changed += 1
    db.session.commit()
    print(f"Processed subscription reminders; {changed} update(s) created.")


with app.app_context():
    db.create_all()
    if not TaxRule.query.first():
        db.session.add(TaxRule(tax_name="Sales tax", tax_percentage=Decimal("0.00"), is_active=False))
        db.session.commit()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
