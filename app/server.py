"""Opinionated"""

from jinja2 import StrictUndefined
from flask_debugtoolbar import DebugToolbarExtension
from flask import Flask, render_template, redirect, request, flash, session, url_for
from models import User, Comment, Post, Vote, Choice, Tag, TagPost, connect_to_db, db
from werkzeug.utils import secure_filename
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import hashlib
import os
from flask import jsonify
import json


# define allowed file type for uploading
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

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
    user = User.query.filter_by(email=email).first()
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

    post_list = Post.get_all_posts()
    hash_files = {}
    for post in post_list:
        for choice in post.choices:
            hash_files[choice] = hashlib.sha512(str(choice.choice_id)).hexdigest()
    tags_list = generate_tag_list()
    post_id_list = [post.post_id for post in post_list]
    session["post_list"] = post_id_list

    return render_template('post_list.html', post_list=post_list, hash_files=hash_files, tags_list=tags_list)


@app.route('/home/post/<int:post_id>')
def show_post_detail(post_id):
    """show the details of the post (post description, choices available), users' votes on it and comments;
    User can also vote on the questions"""
    post = Post.get_post_by_id(post_id)
    choices = Choice.query.filter_by(post_id=post.post_id).all()
    hash_files = {}
    for choice in choices:
        hash_files[choice] = hashlib.sha512(str(choice.choice_id)).hexdigest()
    vote_dict, total_votes = count_votes(post.post_id)
    comments = Comment.query.filter_by(post_id=post_id).all()
    tags = Tag.query.filter(Tag.posts.any(post_id=post_id)).all()
    tag_list = []
    for tag in tags:
        tag_list.append(tag.tag_name)
    post_list = session.get("post_list", None)
    print post_list

    return render_template('post_details.html', post=post, choices=choices, vote_dict=vote_dict,
                           comments=comments, total_votes=total_votes, hash_files=hash_files, tag_list=tag_list,
                           post_list=post_list)


def count_votes(post_id):
    """this is a helper function that counts the vote on a particular questions and returns
    the result in integer(actual number of votes) and percentage(allocation)"""
    post = Post.get_post_by_id(post_id)
    choices = Choice.query.filter_by(post_id=post_id).all()
    vote_dict = {}
    for choice in choices:
        votes = len(Vote.query.filter_by(vote=choice.choice_id).all())
        vote_dict[choice.choice_id] = votes
    total_votes = sum(vote_dict.values())
    return vote_dict, total_votes


#######################################################################################################
# functions that render users profile


@app.route('/home/user/<int:user_id>')
def user_profile(user_id):
    """this is the page that will show users' all posts, and all things they have voted on"""
    # post_dict = {}
    posts = Post.get_posts_by_author_id(user_id)
    my_votes = Vote.query.filter_by(user_id=user_id).all()
    hash_files = {}
    for post in posts:
        choices = Choice.query.filter_by(post_id=post.post_id).all()
        for choice in choices:
            hash_files[choice] = hashlib.sha512(str(choice.choice_id)).hexdigest()
    post_id_list = [post.post_id for post in posts]
    session["post_list"] = post_id_list

    return render_template("user_profile.html", posts=posts, my_votes=my_votes, hash_files=hash_files)


#######################################################################################################
# functions that handles votes

@app.route('/home/post/<int:post_id>/refresh', methods=['POST'])
def process_vote(post_id):
    """this is the function that process users' votes, so it updates the database and refresh the post-details
    page to show the updated votes and vote allocation"""
    vote = request.form.get('vote')
    user_id = session['loggedin']
    int_vote = int(vote)
    new_vote = Vote(user_id=user_id, vote=int_vote)
    db.session.add(new_vote)
    db.session.commit()

    vote_dict, total_votes = count_votes(post_id)

    total_votes_percent = {}
    for vote in vote_dict:
        total_votes_percent[vote] = float(vote_dict[vote]) / total_votes

    return json.dumps([vote_dict, total_votes_percent, total_votes])


#######################################################################################################
# functions that handles posting a question


@app.route('/home/post')
def post_question():
    """This is the render the page that users can edit their questions/posts """
    tags = Tag.query.all()
    tags_list = []
    for tag in tags:
        tag_name = tag.tag_name
        tag_name = str(tag_name)
        tags_list.append(tag_name)

    return render_template("post_question.html", tags_list=tags_list)


def allowed_file(filename):
    """a helper function to see verify the file type uploaded"""
    return '.' in filename and \
           filename.lower().rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


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

    new_post = Post(author_id=author_id, description=description)
    db.session.add(new_post)
    db.session.commit()
    post_id = new_post.post_id

    process_tags(tags, post_id)
    # upload images to amazon
    choice_list = [(text_option1, fileupload1), (text_option2, fileupload2)]
    for text_choice, img_choice in choice_list:
        print 'img_choice', img_choice.filename
        if img_choice:
            if allowed_file(img_choice.filename):
                filename = secure_filename(img_choice.filename)
                new_choice = Choice(text_choice=text_choice, file_name=filename, post_id=new_post.post_id)
                db.session.add(new_choice)
                db.session.commit()

                k = Key(bucket)
                k.key = hashlib.sha512(str(new_choice.choice_id)).hexdigest()
                k.set_contents_from_file(img_choice)
                k.set_canned_acl('public-read')
            else:
                flash('the file type you uploaded is not valid')
        else:
            new_choice = Choice(text_choice=text_choice, post_id=new_post.post_id)
            db.session.add(new_choice)
            db.session.commit()

    flash('Your question has been posted')

    return redirect(url_for('user_profile', user_id=author_id))


def process_tags(tag_list, post_id):
    """the helper function to process the tags"""
    tag_list = tag_list.split(',')
    for tag in tag_list:
        tag_to_check = Tag.query.filter_by(tag_name=tag).first()
        if tag_to_check:
            tag_id = tag_to_check.tag_id
            new_tagpost = TagPost(tag_id=tag_id, post_id=post_id)
            db.session.add(new_tagpost)
            db.session.commit()
        else:
            new_tag = Tag(tag_name=tag)
            db.session.add(new_tag)
            db.session.commit()
            tag_id = new_tag.tag_id
            new_tagpost = TagPost(tag_id=tag_id, post_id=post_id)
            db.session.add(new_tagpost)
            db.session.commit()


#######################################################################################################
# the functions that handles comments

@app.route('/home/post/<int:post_id>/comment/refresh', methods=['POST'])
def process_comments(post_id):
    """process the comments the users entered """
    user_id = session.get('loggedin', None)
    user_name = User.query.get(user_id).user_name
    if user_id:
        content = request.form.get('comment')
        post_id = post_id
        new_comment = Comment(content=content, user_id=user_id, post_id=post_id)
        db.session.add(new_comment)
        db.session.commit()
        return jsonify(user_id=user_id, user_name=user_name, content=content)

    else:
        flash("You need to login first")
        return redirect(url_for('login'))


#######################################################################################################
# the functions that handle post search based on tags

def generate_tag_list():
    """the helper function that generates a list with all tag names"""
    tags = Tag.query.all()
    tags_list = []
    for tag in tags:
        tag_name = tag.tag_name
        tag_name = str(tag_name)
        tags_list.append(tag_name)
    return tags_list


#
@app.route('/home/search', methods=['GET', 'POST'])
def search_post_by_tag():
    """the function that fetch the search user enters and pass it to the corresponding post list page"""
    search = request.form.get('postsearch')
    print search
    print type(search)
    search = str(search)
    return redirect(url_for('post_by_tag', tag_name=search))


@app.route('/home/tag/<tag_name>')
def post_by_tag(tag_name):
    """the function that shows the relevant post list based on the tags the user select"""
    post_list = Post.get_posts_by_tag(tag_name)
    # TODO: Do I need to account for duplicates here?
    #for post in all_tagged_posts:
    #    if post not in post_list:
    #        post_list.append(post)
    tags_list = generate_tag_list()
    if post_list:
        post_id_list = [post.post_id for post in post_list]
        session["post_list"] = post_id_list
        return render_template('post_list_by_tag.html', post_list=post_list, tags_list=tags_list)
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
