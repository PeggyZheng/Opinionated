"""Opinionated"""

from jinja2 import StrictUndefined
from flask_debugtoolbar import DebugToolbarExtension
from flask import Flask, render_template, redirect, request, flash, session, url_for
from models import User, Comment, Post, Vote, connect_to_db, db


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails silently.
# This is horrible. Fix this so that, instead, it raises an error.
app.jinja_env.undefined = StrictUndefined



@app.route("/")
def login():
    """Homepage with login"""

    return render_template("login.html")


# @app.route("/users")
# def user_list():
#     """Show list of users."""
#
#     users = User.query.all()
#     return render_template("user_list.html", users=users)
#
# @app.route("/movies")
# def movie_list():
#     """Show list of movies."""
#     movies = Movie.query.order_by(Movie.title).all()
#     return render_template("movie_list.html", movies=movies)
#
#
@app.route('/login', methods=['POST'])
def login_user():
    """login page for user"""
    email = request.form.get('email')
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first()
    verify_password = user.verify_password(password)

    if user and verify_password:
        flash("Logged in")
        session['loggedin'] = user.user_id
        return redirect(url_for('show_all_posts'))
    else:
        flash("Your email or password is wrong, please re-enter")
        return redirect(url_for('login'))



@app.route('/logout')
def logout_user():
    """Log out the user; remove the user from the session and flash a notificatio message"""
    session.pop('loggedin', None)

    flash("You have logged out")
    return redirect(url_for('login'))

@app.route('/home')
def show_all_posts():
    """the homepage of the site where all the posts will be shown in a table"""
    posts = Post.query.all()
    return render_template('post_list.html', posts=posts)


@app.route('/home/<int:post_id>')
def show_post_detail(post_id):
    """show the details of the post and users' votes on it"""
    post = Post.query.get(post_id)
    vote_result = count_votes(post.post_id)
    return render_template('post_details.html', post=post, vote_result=vote_result)


def count_votes(post_id):
    post = Post.query.get(post_id)
    if post.option_text_1:
        option_1 = len(Vote.query.filter(Vote.post_id==post_id, Vote.vote==1).all())
        option_2 = len(Vote.query.filter(Vote.post_id==post_id, Vote.vote==2).all())

    else:
        option_1 = len(Vote.query.filter(Vote.post_id==post_id, Vote.vote==3).all())
        option_2 = len(Vote.query.filter(Vote.post_id==post_id, Vote.vote==4).all())

    option_1_percent = float(option_1) / (option_1 + option_2)
    option_2_percent = float(option_2) / (option_1 + option_2)

    return option_1, option_1_percent, option_2, option_2_percent

@app.route('/home/<int:post_id>/refresh', methods=['POST', 'GET'])
def process_vote(post_id):
    vote = request.form.get('vote')
    user_id = session['loggedin']
    int_vote = int(vote)
    new_vote = Vote(user_id=user_id, post_id=post_id, vote=vote)
    db.session.add(new_vote)
    db.session.commit()

    return redirect(url_for('show_post_detail', post_id=post_id))


# @app.route('/')
# def process_question():

#
# @app.route('/users/<int:user_id>')
# def show_user_details(user_id):
#     """show the details of the users, include its user id, age, zipcode and movies that they rate"""
#     user = User.query.get(user_id)
#     score_and_title = db.session.query(Movie.movie_id, Movie.title, Rating.score).join(Rating).filter(Rating.user_id==user_id).order_by(Movie.title).all()
#     return render_template('user_profile.html', user=user, score_and_title=score_and_title)
#
# @app.route('/movies/<int:movie_id>')
# def show_movie_details(movie_id):
#     """show the details of the movies that include the a dropdown menu that allows the users to
#     update/add their ratings and show the all the ratings for that specific movie"""
#     movie = Movie.query.get(movie_id)
#     ratings = movie.ratings
#
#
#
#     user_id = session.get("loggedin")
#
#     if user_id:
#         user_rating = Rating.query.filter_by(
#             movie_id=movie_id, user_id=user_id).first()
#
#     else:
#         user_rating = None
#
#     # Get average rating of movie
#
#     rating_scores = [r.score for r in movie.ratings]
#     avg_rating = float(sum(rating_scores)) / len(rating_scores)
#
#     prediction = None
#
#     # Prediction code: only predict if the user hasn't rated it.
#     print "user id is", user_id
#     if user_id:
#         user = User.query.get(user_id)
#         print "user is", user
#         if user:
#             print "this is where we generate prediction"
#             prediction = user.predict_rating(movie)
#     print "This is a test to see prediction", prediction
#     beratement = add_eye_prediction(prediction, user_rating, movie)
#
#     return render_template(
#         "movie_profile.html",
#         movie=movie,
#         user_rating=user_rating,
#         average=avg_rating,
#         prediction=prediction,
#         ratings=ratings,
#         beratement=beratement
#         )
#
# def add_eye_prediction(prediction, user_rating, movie):
#
#     if prediction:
#         # User hasn't scored; use our prediction if we made one
#         effective_rating = prediction
#
#     elif user_rating:
#         # User has already scored for real; use that
#         effective_rating = user_rating.score
#
#     else:
#         # User hasn't scored, and we couldn't get a prediction
#         effective_rating = None
#
#     # Get the eye's rating, either by predicting or using real rating
#
#     the_eye = User.query.filter_by(email="the-eye@of-judgment.com").one()
#     eye_rating = Rating.query.filter_by(
#         user_id=the_eye.user_id, movie_id=movie.movie_id).first()
#
#     if eye_rating is None:
#         eye_rating = the_eye.predict_rating(movie)
#
#     else:
#         eye_rating = eye_rating.score
#
#     if eye_rating and effective_rating:
#         difference = abs(eye_rating - effective_rating)
#
#     else:
#         # We couldn't get an eye rating, so we'll skip difference
#         difference = None
#
#     BERATEMENT_MESSAGES = [
#         "I suppose you don't have such bad taste after all.",
#         "I regret every decision that I've ever made that has brought me" +
#             " to listen to your opinion.",
#         "Words fail me, as your taste in movies has clearly failed you.",
#         "That movie is great. For a clown to watch. Idiot.",
#         "Words cannot express the awfulness of your taste."
#     ]
#
#     if difference is not None:
#         beratement = BERATEMENT_MESSAGES[int(difference)]
#
#     else:
#         beratement = None
#
#     return beratement
#
# @app.route('/movies/<int:movie_id>', methods=['POST'])
# def update_movie_rating(movie_id):
#     """update the ratings for a particular movie and particular users and update the db"""
#     score = int(request.form.get('score'))
#     if session.get('loggedin', None):
#         user_id = session['loggedin']
#         has_rated = Rating.query.filter_by(user_id=user_id, movie_id=movie_id).first()
#         if has_rated:
#             has_rated.score = score
#         else:
#             movie_rating = Rating(movie_id=movie_id, user_id=user_id, score=score)
#             db.session.add(movie_rating)
#
#         db.session.commit()
#         flash('Your rating has been added/updated')
#
#         return redirect(url_for('show_movie_details', movie_id=movie_id))
#     else:
#         flash('You need to login first')
#         return redirect(url_for('index'))



if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run()
