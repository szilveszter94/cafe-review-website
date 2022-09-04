from flask import Flask, render_template, url_for, request, redirect, abort, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_gravatar import Gravatar
from functools import wraps
from datetime import date
from flask_bootstrap import Bootstrap
from forms import RegisterForm, LoginRegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_mail import Mail, Message

# ------------------------------------------ SET THE APPLICATION --------------------------------------------------- #

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False
db = SQLAlchemy(app)
Bootstrap(app)
current_year = date.today().year

# set smpt email server, you have to set your smtp address, email address, and password
SMTP = "YOUR EMAIL SERVICE SMTP ADDRESS"
EMAIL = "YOUR EMAIL ADDRESS"
PASSWORD = "YOUR PASSWORD"

app.config["MAIL_SERVER"] = SMTP
app.config["MAIL_PORT"] = "e.g.587"
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = EMAIL
app.config["MAIL_PASSWORD"] = PASSWORD
mail = Mail(app)

# set gravatar for automatic user avatars
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False,
                    base_url=None)
# set login manager for login users
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ------------------------------------------------- SET THE DATABASE MODELS --------------------------------------- #

# set the cafe database model
class Cafe(db.Model):
    __tablename__ = "cafe"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    country = db.Column(db.String(250), nullable=False)
    city = db.Column(db.String(250), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    coffee_price = db.Column(db.Float, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    can_pay_with_card = db.Column(db.Boolean, nullable=False)
    comments = relationship("Comment", back_populates="parent_cafe")


# set the suggest cafe database model
class Suggest(db.Model):
    __tablename__ = "suggest"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    country = db.Column(db.String(250), nullable=False)
    city = db.Column(db.String(250), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    coffee_price = db.Column(db.Float, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    can_pay_with_card = db.Column(db.Boolean, nullable=False)


# set the user database model
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    nickname = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    comments = relationship("Comment", back_populates="comment_author")

    # set token for reset user password
    def get_token(self, expires_sec=300):
        serial = Serializer(app.config['SECRET_KEY'], expires_in=expires_sec)
        return serial.dumps({"user_id": self.id}).decode("utf-8")

    # verify token for sercure reset password
    @staticmethod
    def verify_token(token):
        serial = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = serial.loads(token)["user_id"]
        except:
            return None
        return User.query.get(user_id)


# set the comment database model
class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    cafe_id = db.Column(db.Integer, db.ForeignKey("cafe.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    parent_cafe = relationship("Cafe", back_populates="comments")
    comment_author = relationship("User", back_populates="comments")
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.Text, nullable=False)


# create sql database
db.create_all()

# -------------------------------------------- FUNCTIONS ----------------------------------------------------------- #


# forgot password function, send password reset link to the user
def send_mail(user):
    token = user.get_token()
    msg = Message("Password reset request", recipients=[user.email], sender=EMAIL)
    msg.body = f''' To reset your password, please follow the link below.
    {url_for('reset_token', token=token, _external=True)}
    If you don't send a password reset request, please ignore this message.
'''
    mail.send(msg)


# manage and calculate the cafe rating
def rating_calculator(seats, has_wifi, has_toilet, has_sockets, can_take_calls, can_pay_with_card):
    rating = 0
    if seats >= 30:
        rating += 3
    elif seats >= 10:
        rating += 2
    else:
        rating += 1
    if has_wifi:
        rating += 2
    if has_toilet:
        rating += 2
    if has_sockets:
        rating += 1
    if can_take_calls:
        rating += 1
    if can_pay_with_card:
        rating += 1
    return rating


# ---------------------------------------------------- SET ALL ROUTES --------------------------------------------- #
# set the admin only route
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


# set the home page route
@app.route("/")
def home():
    # render index.html and all cafes from database
    all_cafes = Cafe.query.order_by(Cafe.rating.desc()).all()
    return render_template('index.html', year=current_user, current_user=current_user, all_cafes=all_cafes)


# set the filter route
@app.route("/sorted/<string:id>")
def sorted_cafe(id):
    # filter cafes by city
    filtered = Cafe.query.filter_by(city=id).order_by(Cafe.rating.desc())
    return render_template('index.html', current_user=current_user, all_cafes=filtered, year=current_user)


# set the city filter route
@app.route("/cities", methods=["POST", "GET"])
def cities():
    country_list = []
    city_list = []
    countries = Cafe.query.all()
    # show all cities in the database
    for i in countries:
        if i.country not in country_list:
            country_list.append(i.country)
    if request.method == "POST":
        country = request.form.get("gender")
        city_list_raw = Cafe.query.filter_by(country=country)
        for i in city_list_raw:
            if i.city not in city_list:
                city_list.append(i.city)
        city_list.sort()
        return render_template('cities.html', country_list=country_list, city_list=city_list,
                               current_user=current_user, year=current_user)

    return render_template('cities.html', country_list=country_list, city_list=city_list,
                           current_user=current_user, year=current_user)


# set the add new cafe route, only for admin
@app.route("/add", methods=["POST", "GET"])
@admin_only
def add():
    # add new cafe, get all data from the form
    if request.method == "POST":
        seats = int(request.form.get("seats"))
        has_wifi = bool(request.form.get("has_wifi"))
        has_toilet = bool(request.form.get("has_toilet"))
        has_sockets = bool(request.form.get("has_sockets"))
        can_take_calls = bool(request.form.get("can_take_calls"))
        can_pay_with_card = bool(request.form.get("can_pay_with_card"))
        rating = rating_calculator(seats, has_wifi, has_toilet, has_sockets, can_take_calls, can_pay_with_card)
        new_coffee = Cafe(
            name=request.form.get("name"),
            map_url=request.form.get("map_url"),
            latitude=request.form.get("latitude"),
            longitude=request.form.get("longitude"),
            img_url=request.form.get("img_url"),
            city=request.form.get("city"),
            country=request.form.get("country"),
            location=request.form.get("location"),
            description=request.form.get("description"),
            seats=seats,
            has_toilet=has_toilet,
            has_wifi=has_wifi,
            has_sockets=has_sockets,
            can_take_calls=can_take_calls,
            coffee_price=request.form.get("coffee_price"),
            can_pay_with_card=can_pay_with_card,
            rating=rating
        )
        db.session.add(new_coffee)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("add.html", current_user=current_user, year=current_user)


# set the suggest cafe route
@app.route("/suggest", methods=["POST", "GET"])
def suggest():
    # add new cafe suggestion, get all data from the form
    if request.method == "POST":
        seats = int(request.form.get("seats"))
        has_wifi = bool(request.form.get("has_wifi"))
        has_toilet = bool(request.form.get("has_toilet"))
        has_sockets = bool(request.form.get("has_sockets"))
        can_take_calls = bool(request.form.get("can_take_calls"))
        can_pay_with_card = bool(request.form.get("can_pay_with_card"))
        rating = rating_calculator(seats, has_wifi, has_toilet, has_sockets, can_take_calls, can_pay_with_card)
        new_coffee = Suggest(
            name=request.form.get("name"),
            map_url=request.form.get("map_url"),
            latitude=request.form.get("latitude"),
            longitude=request.form.get("longitude"),
            img_url=request.form.get("img_url"),
            city=request.form.get("city"),
            country=request.form.get("country"),
            location=request.form.get("location"),
            description=request.form.get("description"),
            seats=seats,
            has_toilet=has_toilet,
            has_wifi=has_wifi,
            has_sockets=has_sockets,
            can_take_calls=can_take_calls,
            coffee_price=request.form.get("coffee_price"),
            can_pay_with_card=can_pay_with_card,
            rating=rating
        )
        db.session.add(new_coffee)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("suggest.html", current_user=current_user, year=current_user)


# view suggested cafes, only for admin
@app.route("/suggested")
@admin_only
def suggested():
    # show all suggested cafes
    all_cafe = Suggest.query.all()
    return render_template('cafe_database.html', all_cafe=all_cafe, year=current_user)


# accept suggested cafes, only for admin
@app.route("/edit/<string:id>", methods=["POST", "GET"])
@admin_only
def edit_suggested(id):
    if request.method == "POST":
        name = request.form.get("name")
        # check if suggested cafe already exist
        if Cafe.query.filter_by(name=name).first():
            flash('This cafe already exist')
        else:
            seats = int(request.form.get("seats"))
            has_wifi = bool(request.form.get("has_wifi"))
            has_toilet = bool(request.form.get("has_toilet"))
            has_sockets = bool(request.form.get("has_sockets"))
            can_take_calls = bool(request.form.get("can_take_calls"))
            can_pay_with_card = bool(request.form.get("can_pay_with_card"))
            rating = rating_calculator(seats, has_wifi, has_toilet, has_sockets, can_take_calls, can_pay_with_card)
            new_coffee = Cafe(
                name=name,
                map_url=request.form.get("map_url"),
                latitude=request.form.get("latitude"),
                longitude=request.form.get("longitude"),
                img_url=request.form.get("img_url"),
                city=request.form.get("city"),
                country=request.form.get("country"),
                location=request.form.get("location"),
                description=request.form.get("description"),
                seats=seats,
                has_toilet=has_toilet,
                has_wifi=has_wifi,
                has_sockets=has_sockets,
                can_take_calls=can_take_calls,
                coffee_price=request.form.get("coffee_price"),
                can_pay_with_card=can_pay_with_card,
                rating=rating
            )
            db.session.add(new_coffee)
            db.session.commit()
            return redirect(url_for("delete_suggested", id=id))
    this_cafe = Suggest.query.get(id)
    return render_template("edit_suggested.html", this_cafe=this_cafe, current_user=current_user, year=current_user)


# delete suggested cafe, only for admin
@app.route("/delete_suggested/<string:id>")
@admin_only
def delete_suggested(id):
    # get the cafe by id, and delete
    this_cafe = Suggest.query.get(id)
    db.session.delete(this_cafe)
    db.session.commit()
    return redirect(url_for("suggested"))


# view users, only for admin
@app.route("/user_database")
@admin_only
def user_database():
    all_users = User.query.all()
    return render_template('user_database.html', all_users=all_users, year=current_user)


# delete users, only for admin
@app.route("/delete_user/<string:id>")
@admin_only
def delete_user(id):
    # find the user by id, and delete, if the id is not 1, because 1 is admin
    if id != str(1):
        user_comments = Comment.query.filter_by(author_id=id).all()
        selected_user = User.query.get(id)
        db.session.delete(selected_user)
        for i in user_comments:
            db.session.delete(i)
            db.session.commit()
        db.session.commit()
    else:
        return redirect(url_for("user_database"))
    return redirect(url_for("user_database"))


# delete cafe, only for admin
@app.route("/delete/<string:id>")
@admin_only
def delete(id):
    # find the cafe by id, and delete
    this_cafe = Cafe.query.get(id)
    db.session.delete(this_cafe)
    db.session.commit()
    return redirect(url_for("home"))


# edit cafe, only for admin
@app.route("/edit/<string:id>", methods=["POST", "GET"])
@admin_only
def edit(id):
    # find the cafe by id, and edit
    if request.method == "POST":
        cafe_to_update = Cafe.query.filter_by(id=id).first()
        has_toilet = bool(request.form.get("has_toilet"))
        has_wifi = bool(request.form.get("has_wifi"))
        has_sockets = bool(request.form.get("has_sockets"))
        can_take_calls = bool(request.form.get("can_take_calls"))
        can_pay_with_card = bool(request.form.get("can_pay_with_card"))
        seats = int(request.form.get("seats"))
        rating = rating_calculator(seats, has_wifi, has_toilet, has_sockets, can_take_calls, can_pay_with_card)
        cafe_to_update.has_toilet = has_toilet
        cafe_to_update.has_wifi = has_wifi
        cafe_to_update.has_sockets = has_sockets
        cafe_to_update.can_take_calls = can_take_calls
        cafe_to_update.can_pay_with_card = can_pay_with_card
        cafe_to_update.seats = seats
        cafe_to_update.name = request.form.get("name")
        cafe_to_update.map_url = request.form.get("map_url")
        cafe_to_update.longitude = request.form.get("longitude")
        cafe_to_update.latitude = request.form.get("latitude")
        cafe_to_update.img_url = request.form.get("img_url")
        cafe_to_update.location = request.form.get("location")
        cafe_to_update.city = request.form.get("city")
        cafe_to_update.country = request.form.get("country")
        cafe_to_update.description = request.form.get("description")
        cafe_to_update.coffee_price = request.form.get("coffee_price")
        cafe_to_update.rating = rating
        db.session.commit()
        return redirect(url_for("info", id=cafe_to_update.id))
    this_cafe = Cafe.query.get(id)
    return render_template("edit.html", this_cafe=this_cafe, current_user=current_user, year=current_user)


# view cafe information
@app.route("/info/<string:id>", methods=["POST", "GET"])
def info(id):
    # find the cafe by id, and show details, comments
    this_cafe = Cafe.query.get(id)
    comments = Comment.query.filter_by(cafe_id=this_cafe.id)
    if request.method == "POST":
        new_comment = Comment(
            cafe_id=this_cafe.id,
            author_id=current_user.id,
            text=request.form.get("message"),
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template("info.html", this_cafe=this_cafe, comments=comments,
                           current_user=current_user, year=current_user)


# login or register route
@app.route('/login-register', methods=["POST", "GET"])
def login_register():
    form = LoginRegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        # check if user is registered, and redirect the corresponding page
        if User.query.filter_by(email=email).first():
            return redirect(url_for("login", id=email))
        else:
            return redirect(url_for("register", id=email))
    return render_template("login-register.html", form=form, current_user=current_user, year=current_user)


# login route
@app.route('/login/<string:id>', methods=["POST", "GET"])
def login(id):
    form = LoginForm()
    form.email.data = id
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        # check if email exists
        if User.query.filter_by(email=email).first():
            user = User.query.filter_by(email=email).first()
            # check the password with flask build in function
            if check_password_hash(user.password, password) and user.email == email:
                login_user(user)
                return redirect(url_for("home"))
            else:
                flash('Password incorrect, please try again.')
                return redirect(url_for('login', id=email))
        else:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
    return render_template("login.html", form=form, current_user=current_user, year=current_user)


# register route
@app.route("/register/<string:id>", methods=["POST", "GET"])
def register(id):
    form = RegisterForm()
    form.email.data = id
    if form.validate_on_submit():
        nickname = form.nickname.data
        if User.query.filter_by(nickname=nickname).first():
            flash("Nickname already exist")
        else:
            # check if 2 passwords matches and hashing the password
            if form.password.data == form.password_check.data:
                hash_and_salted_password = generate_password_hash(
                    form.password.data,
                    method='pbkdf2:sha256',
                    salt_length=8
                )
                # create new user
                new_user = User(
                    email=form.email.data,
                    password=hash_and_salted_password,
                    nickname=form.nickname.data

                )
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                return redirect(url_for("home"))
            else:
                flash("The passwords do not match")
    return render_template("register.html", form=form, current_user=current_user, year=current_user)


# logut route
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


# forgot password route
@app.route("/forgot", methods=["POST", "GET"])
def forgot():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_mail(user)
            return redirect(url_for("home"))
    return render_template("forgot.html", form=form, year=current_user)


# forgot password reset token, for validation
@app.route("/forgot/<token>", methods=["POST", "GET"])
def reset_token(token):
    user = User.verify_token(token)
    if user is None:
        flash("That is invalid token or expired.")
        return redirect(url_for("forgot"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if form.password.data == form.password_check.data:
            hash_and_salted_password = generate_password_hash(
                form.password.data,
                method='pbkdf2:sha256',
                salt_length=8
            )
            user.password = hash_and_salted_password
            db.session.commit()
            flash("Password changed successfully, please login")
            return redirect(url_for("login", id=user.email))
    return render_template("reset_password.html", form=form, current_user=current_user, year=current_user)


# start the app
if __name__ == "__main__":
    app.run(debug=True)
