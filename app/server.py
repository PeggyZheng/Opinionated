"""Opinionated"""

from jinja2 import StrictUndefined
from flask_debugtoolbar import DebugToolbarExtension
from flask import Flask, render_template, redirect, request, flash, session, url_for
from models import User, Comment, Post, Vote, Choice, Tag, connect_to_db
from boto.s3.connection import S3Connection
import os
from flask import jsonify
import json



app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails silently.
# This is horrible. Fix this so that, instead, it raises an error.
app.jinja_env.undefined = StrictUndefined

# setup for s3
conn = S3Connection(os.environ["AWS_ACCESS_KEY"], os.environ["AWS_SECRET_KEY"])
bucket = conn.get_bucket(os.environ['AWS_BUCKET'])


#######################################################################################################
# functions that handles login and logout

@app.route("/")
def login():
    """Homepage with login"""

    return render_template("login.html")


@app.route('/login', methods=['POST'])
def login_user():
    """login page for user"""
    email = request.form.get('email')
    password = request.form.get('password')
    user = User.get_user_by_email(email)
    verify_password = user.verify_password(password)

    if user:
        if verify_password:
            flash("Logged in")
            session['loggedin'] = user.user_id
            return redirect(url_for('show_all_posts'))
    else:
        flash("Your email or password is wrong, please re-enter")
        return redirect(url_for('login'))


@app.route('/logout')
def logout_user():
    """Log out the user; remove the user from the session and flash a notification message"""
    session.pop('loggedin', None)

    flash("You have logged out")
    return redirect(url_for('login'))


#######################################################################################################
# functions that render posts pages

@app.route('/home', methods=['GET', 'POST'])
def show_all_posts():
    """the homepage of the site where all the posts will be shown in a table"""

    posts = Post.get_all_posts()
    # hash_files = {}
    # for post in posts:
    #     for choice in post.choices:
    #         hash_files[choice] = hashlib.sha512(str(choice.choice_id)).hexdigest()
    tag_names = [str(tag.tag_name) for tag in Tag.get_all_tags()]
    session["post_ids"] = [post.post_id for post in posts]

    return render_template('post_list.html', posts=posts, tag_names=tag_names)


@app.route('/home/post/<int:post_id>')
def show_post_detail(post_id):
    """show the details of the post (post description, choices available), users' votes on it and comments;
    User can also vote on the questions"""
    post = Post.get_post_by_id(post_id)
    choices = Choice.get_choices_by_post_id(post_id)
    # hash_files = {}
    # for choice in choices:
    #     hash_files[choice] = hashlib.sha512(str(choice.choice_id)).hexdigest()
    vote_dict, total_votes = post.count_votes()
    comments = Comment.get_comments_by_post_id(post_id)
    tag_names = [tag.tag_name for tag in Tag.get_tags_by_post_id(post_id)]
    post_ids = session.get("post_ids", None)
    print vote_dict
    print total_votes

    return render_template('post_details.html', post=post, choices=choices, vote_dict=vote_dict,
                           comments=comments, total_votes=total_votes, tag_names=tag_names,
                           post_ids=post_ids)





#######################################################################################################
# functions that render users profile


@app.route('/home/user/<int:user_id>')
def user_profile(user_id):
    """this is the page that will show users' all posts, and all things they have voted on"""
    # post_dict = {}
    posts = Post.get_posts_by_author_id(user_id)
    votes = Vote.get_votes_by_user_id(user_id)
    # hash_files = {}
    # for post in posts:
    #     choices = Choice.get_choices_by_post_id(post.post_id)
    #     for choice in choices:
    #         hash_files[choice] = hashlib.sha512(str(choice.choice_id)).hexdigest()
    session["post_ids"] = [post.post_id for post in posts]

    return render_template("user_profile.html", posts=posts, votes=votes)


#######################################################################################################
# functions that handles votes

@app.route('/home/post/<int:post_id>/refresh', methods=['POST'])
def process_vote(post_id):
    """this is the function that process users' votes, so it updates the database and refresh the post-details
    page to show the updated votes and vote allocation"""
    choice_id = request.form.get("choice_id")
    user_id = session['loggedin']
    Vote.create(user_id=user_id, choice_id=choice_id)

    post = Post.get_post_by_id(post_id)
    vote_dict, total_votes = post.count_votes()

    total_votes_percent = {}
    for vote in vote_dict:
        total_votes_percent[vote] = float(vote_dict[vote]) / total_votes

    return json.dumps([vote_dict, total_votes_percent, total_votes])


#######################################################################################################
# functions that handles posting a question


@app.route('/home/post')
def post_question():
    """This is the render the page that users can edit their questions/posts """
    tag_names = [str(tag.tag_name) for tag in Tag.get_all_tags()]
    return render_template("post_question.html", tag_names=tag_names)





@app.route('/home/post/process', methods=['POST'])
def process_question():
    """Process the questions that user added, and updated the database"""
    description = request.form.get('description')
    text_option1 = request.form.get('option1')
    text_option2 = request.form.get('option2')
    fileupload1 = request.files.get('fileupload1')
    fileupload2 = request.files.get('fileupload2')
    author_id = session['loggedin']
    tags = request.form.get('hidden_tags')

    choice_data = [(text_option1, fileupload1), (text_option2, fileupload2)]

    Post.create(author_id=author_id, description=description, tag_list=tags, choice_data=choice_data)

    return redirect(url_for('user_profile', user_id=author_id))


#######################################################################################################
# the functions that handles comments

@app.route('/home/post/<int:post_id>/comment/refresh', methods=['POST'])
def process_comments(post_id):
    """process the comments the users entered """
    user_id = session.get('loggedin', None)
    user_name = User.get_user_by_id(user_id).user_name
    if user_id:
        content = request.form.get('comment')
        Comment.create(content=content, user_id=user_id, post_id=post_id)
        return jsonify(user_id=user_id, user_name=user_name, content=content)

    else:
        flash("You need to login first")
        return redirect(url_for('login'))


#######################################################################################################

#
@app.route('/home/search', methods=['GET', 'POST'])
def search_post_by_tag():
    """the function that fetch the search user enters and pass it to the corresponding post list page"""
    search = request.form.get('postsearch')
    return redirect(url_for('post_by_tag', tag_name=str(search)))


@app.route('/home/tag/<tag_name>')
def post_by_tag(tag_name):
    """the function that shows the relevant post list based on the tags the user select"""
    posts = Post.get_posts_by_tag(tag_name)
    tag_names= [str(tag.tag_name) for tag in Tag.get_all_tags()]

    if posts:
        post_ids = [post.post_id for post in posts]
        # hash_files = {}
        # for post in posts:
        #     choices = Choice.get_choices_by_post_id(post.post_id)
        #     for choice in choices:
        #         hash_files[choice] = hashlib.sha512(str(choice.choice_id)).hexdigest()
        session["post_ids"] = post_ids
        return render_template('post_list_by_tag.html', posts=posts, tag_names=tag_names)
    else:
        flash('your search returns no relevant posts')
        return redirect(url_for('show_all_posts'))


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run()
