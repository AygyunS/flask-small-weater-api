from flask import Flask, render_template, request, redirect, url_for, flash
from forms import LoginForm  # Add this line
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from dotenv import load_dotenv
import requests

import os


load_dotenv()


api_key = os.environ.get("OPENWEATHER_API_KEY")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SECRET_KEY"] = os.urandom(24)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@app.route("/")
@login_required
def index():
    main_location = current_user.main_location
    main_location_weather = get_weather_data(
        main_location, api_key, forecast_type="current"
    )
    print(main_location_weather)  # Debugging: print main_location_weather
    return render_template(
        "index.html",
        main_location=main_location,
        main_location_weather=main_location_weather,
    )


@app.route("/weather", methods=["POST"])
@login_required
def weather():
    city = request.form.get("city") or current_user.main_location
    forecast_type = request.form.get("forecast_type")

    if not city:
        flash("Please enter a city name or set your main location", "error")
        return redirect(url_for("index"))

    weather_data = get_weather_data(city, api_key, forecast_type)

    if not weather_data:
        flash("Error fetching weather data. Please try again later.", "error")
        return redirect(url_for("index"))

    print(weather_data)  # Debugging: print weather_data

    if forecast_type == "current":
        template_name = "weather_current.html"
    elif forecast_type == "week":
        template_name = "weather_week.html"
    else:
        flash("Invalid forecast type", "error")
        return redirect(url_for("index"))

    print(template_name)  # Debugging: print selected template

    return render_template(template_name, weather=weather_data)


def get_weather_data(city, api_key, forecast_type="current"):
    if forecast_type == "current":
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"
    elif forecast_type == "week":
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&appid={api_key}"
    else:
        return None

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def get_weather_data(city, api_key, forecast_type="current"):
    if forecast_type == "current":
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"
    elif forecast_type == "week":
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&appid={api_key}"
    else:
        return None

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    main_location = db.Column(db.String(120), nullable=True)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        main_location = request.form["main_location"]
        if not username or not password or not main_location:
            flash("Please fill in all fields", "error")
        else:
            new_user = User(
                username=username, password=password, main_location=main_location
            )
            db.session.add(new_user)
            db.session.commit()
            flash("User registered successfully!", "success")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()  # Create form instance
    if (
        form.validate_on_submit()
    ):  # Replace request.method == 'POST' with form.validate_on_submit()
        username = (
            form.username.data
        )  # Replace request.form['username'] with form.username.data
        password = (
            form.password.data
        )  # Replace request.form['password'] with form.password.data
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password", "error")
    return render_template(
        "login.html", form=form
    )  # Pass form instance to the template


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out", "success")
    return redirect(url_for("index"))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_db(app):
    with app.app_context():
        db.create_all()


def print_users():
    with app.app_context():
        users = User.query.all()
        print("ID | Username | Password | Main Location")
        print("------------------------------------------")
        for user in users:
            print(
                f"{user.id} | {user.username} | {user.password} | {user.main_location}"
            )


@app.route("/change_default_city", methods=["GET", "POST"])
@login_required
def change_default_city():
    if request.method == "POST":
        new_main_location = request.form["main_location"]
        if not new_main_location:
            flash("Please enter a city name", "error")
        else:
            current_user.main_location = new_main_location
            db.session.commit()
            flash("Main location updated successfully!", "success")
            return redirect(url_for("index"))
    return render_template("change_default_city.html")


if __name__ == "__main__":
    create_db(app)
    print_users()
    app.run(debug=True)
