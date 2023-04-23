import os
import requests
from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from edit_movie_form import EditMovieForm
from add_movie_form import AddMovieForm

MOVIE_DB_URL = 'https://api.themoviedb.org/3'
MOVIE_DB_IMAGE_URL = 'https://image.tmdb.org/t/p/w500'
APY_KEY = os.environ.get("APY_KEY")
APY_TOKEN = os.environ.get("APY_TOKEN")
headers = {
    'Authorization': f"Bearer {APY_TOKEN}",
}

#App setup 
app = Flask(__name__)
app.debug = True
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY #Your secret key
Bootstrap(app)

# Database
db_url = 'sqlite:///movies-collection.db'  
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

with app.app_context():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    #This line loops through all the movies
    for i in range(len(all_movies)):
        #This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i
    return render_template("index.html", all_movies=all_movies)

@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = AddMovieForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        movie_api_search_url = f"{MOVIE_DB_URL}/search/movie"
        response = requests.get(
            url=movie_api_search_url, 
            params={"api_key": APY_KEY, "query": movie_title}
        )
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=form)

@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_URL}/movie/{movie_api_id}"
        response = requests.get(
            url=movie_api_url, 
            params={"api_key": APY_KEY,"language": "en-US",},
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        new_movie = Movie(
            title= data["title"],
            year= data["release_date"].split("-")[0],
            description= data["overview"],
            rating = data['popularity'],
            ranking = data['vote_average'],
            review = data['tagline'],
            img_url= f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("rate_movie", id=new_movie.id))

@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = EditMovieForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)

@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))

if __name__ == '__main__':
    app.run(debug=True)