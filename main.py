from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
from dotenv import dotenv_values

MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
database_url = "https://www.themoviedb.org/3"
config = {
    **dotenv_values(".env.secret")
}
api_key = config["API_KEY"]

headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {api_key}"
}

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

##CREATE DB
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


##CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

with app.app_context():
    db.create_all()

class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all() # convert to python list
    
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i;
    db.session.commit()
    
    return render_template("index.html", movies=all_movies)

# Adding the Update functionality
@app.route("/edit/<int:r_id>", methods=["GET", "POST"])
def rate_movie(r_id):
    form = RateMovieForm()
    movie_id = r_id
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)

@app.route("/delete/<int:d_id>")
def delete_movie(d_id):
    movie_id = d_id
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))


class TitleForm(FlaskForm):
    title = StringField("Movie Title")
    submit = SubmitField("Done")

@app.route("/title", methods=["GET", "POST"])
def get_movie_title():
    title_form = TitleForm()
    if title_form.validate_on_submit():
        movie_title = title_form.title.data
        query = movie_title.replace(" ", "%20")
        response = requests.get(
            url=f"https://api.themoviedb.org/3/search/movie?query={query}&include_adult=false&language=en-US&page=1",
            headers=headers
        )
        movies_list = response.json()["results"]
        return render_template("select.html", movies=movies_list)
    return render_template("add.html", form=title_form)

@app.route("/add/<int:m_id>", methods=["GET", "POST"])
def add_movie(m_id):
    movie_id = m_id
    print("m_id: ", movie_id)
    response = requests.get(
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US",
        headers=headers
    )
    data = response.json()
    
    new_movie = Movie(
        title = data["title"], 
        img_url = f"{MOVIE_DB_IMAGE_URL}/{data['poster_path']}",  
        year = data["release_date"].split("-")[0],
        description = data["overview"],
    )
    
    db.session.add(new_movie)
    db.session.commit()
    
    return redirect(url_for("rate_movie", r_id=new_movie.id))

if __name__ == '__main__':
    app.run(debug=True)