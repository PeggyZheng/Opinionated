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


#######################################################################################################
#functions that handles login and logout

@app.route("/")
def login():
    """Homepage with login"""

    return render_template("login.html")

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

#######################################################################################################
#functions that render posts pages

@app.route('/home')
def show_all_posts():
    """the homepage of the site where all the posts will be shown in a table"""
    posts = Post.query.all()
    return render_template('post_list.html', posts=posts)


@app.route('/home/post/<int:post_id>')
def show_post_detail(post_id):
    """show the details of the post (post description, choices available), users' votes on it and comments;
    User can also vote on the questions"""
    post = Post.query.get(post_id)
    vote_result = count_votes(post.post_id)
    comments = Comment.query.filter_by(post_id=post_id).all()
    return render_template('post_details.html', post=post, vote_result=vote_result, comments=comments)


def count_votes(post_id):
    """this is a helper function that counts the vote on a particular questions and returns
    the result in integer(actual number of votes) and percentage(allocation)"""
    post = Post.query.get(post_id)
    if post.option_text_1:
        option_1 = len(Vote.query.filter(Vote.post_id==post_id, Vote.vote==1).all())
        option_2 = len(Vote.query.filter(Vote.post_id==post_id, Vote.vote==2).all())

    else:
        option_1 = len(Vote.query.filter(Vote.post_id==post_id, Vote.vote==3).all())
        option_2 = len(Vote.query.filter(Vote.post_id==post_id, Vote.vote==4).all())

    if option_1 == 0 and option_2 == 0:
        option_1_percent = None
        option_2_percent = None
    else:
        option_1_percent = float(option_1) / (option_1 + option_2)
        option_2_percent = float(option_2) / (option_1 + option_2)

    return option_1, option_1_percent, option_2, option_2_percent

#######################################################################################################
#functions that render users profile


@app.route('/home/user/<int:user_id>')
def user_profile(user_id):
    """this is the page that will show users' all posts, and all things they have voted on"""
    posts = Post.query.filter_by(author_id=user_id).all()
    votes = Vote.query.filter_by(user_id=user_id).all()
    my_votes = []
    for vote in votes:
        dict = {1: vote.post.option_text_1,
                2: vote.post.option_text_2,
                3: vote.post.option_pic_1,
                4: vote.post.option_pic_2}
        my_vote = dict[vote.vote]
        my_votes.append((vote, my_vote))


    return render_template("user_profile.html", posts=posts, my_votes=my_votes)

#######################################################################################################
#functions that handles votes

@app.route('/home/post/<int:post_id>/refresh', methods=['POST', 'GET'])
def process_vote(post_id):
    """this is the function that prcoess users' votes, so it updates the database and refresh the post-details
    page to show the updated votes and vote allocation"""
    vote = request.form.get('vote')
    user_id = session['loggedin']
    int_vote = int(vote)
    new_vote = Vote(user_id=user_id, post_id=post_id, vote=vote)
    db.session.add(new_vote)
    db.session.commit()

    return redirect(url_for('show_post_detail', post_id=post_id))



#######################################################################################################
#functions that handles posting a question


@app.route('/home/post')
def post_question():
    return render_template("post_question.html")

@app.route('/home/post/process', methods=['POST'])
def process_question():
    description = request.form.get('description')
    option1 = request.form.get('option1')
    option2 = request.form.get('option2')
    author_id = session['loggedin']

    new_post = Post(author_id=author_id, description=description, option_text_1=option1, option_text_2=option2)
    db.session.add(new_post)
    db.session.commit()

    flash('Your question has been posted')

    return redirect(url_for('user_profile', user_id=author_id))

#######################################################################################################
#the functions that handles comments

@app.route('/home/post/<int:post_id>/comment/refresh', methods=['POST'])
def process_comments(post_id):
    user_id = session.get('loggedin', None)
    if user_id:
        content = request.form.get('new_comment')
        post_id = post_id
        new_comment = Comment(content=content, user_id=user_id, post_id=post_id)
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('show_post_detail', post_id=post_id))

    else:
        flash("You need to login first")
        return redirect(url_for('login'))






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
