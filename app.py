from flask import Flask, render_template, redirect, session, flash

# from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegForm, LoginForm, FeedbackForm
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Unauthorized

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False


connect_db(app)

# toolbar = DebugToolbarExtension(app)


@app.route("/")
def home_page():
    return redirect("/register")


@app.route("/register", methods=["GET", "POST"])
def register_user():
    form = RegForm()
    if form.validate():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append("Username taken.  Please pick another")
            form.email.errors.append("Email already in use.  Please try again")
            return render_template("users/register.html", form=form)
        session["username"] = new_user.username
        flash("Welcome! Successfully Created Your Account!", "success")
        return redirect(f"/users/{new_user.username}")

    return render_template("users/register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login_user():
    form = LoginForm()
    if form.validate():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome Back, {user.username}!", "primary")
            session["username"] = user.username
            return redirect(f"/users/{user.username}")
        else:
            return redirect("/")

    return render_template("users/login.html", form=form)


@app.route("/secret")
def secret():
    if "username" not in session:
        flash("Please login first!", "danger")
        return redirect("/")
    return redirect("/users/<username>")


@app.route("/logout")
def logout():
    session.pop("username")
    return redirect("/")


@app.route("/users/<username>")
def user_info(username):
    if "username" not in session or username != session["username"]:
        raise Unauthorized()

    user = User.query.get(username)

    return render_template("users/user_info.html", user=user)


@app.route("/users/<username>/delete", methods=["POST"])
def delete_user(username):
    if "username" not in session or username != session["username"]:
        raise Unauthorized()
    user = User.query.get(username)
    db.session.delete(user)
    db.session.commit()
    session.pop("username")

    return redirect("/login")


@app.route("/users/<username>/feedback/add", methods=["GET", "POST"])
def add_feedback(username):
    if "username" not in session or username != session["username"]:
        raise Unauthorized()

    form = FeedbackForm()

    if form.validate():
        title = form.title.data
        content = form.content.data
        feedback = Feedback(title=title, content=content, username=username)

        db.session.add(feedback)
        db.session.commit()

        return redirect(f"/users/{feedback.username}")
    else:
        return render_template("feedback/add.html", form=form)
