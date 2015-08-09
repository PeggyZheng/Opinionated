"""Models and database functions for Opinionated project."""

from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import os
import hashlib



# This is the connection to the SQLite database; we're getting this through
# the Flask-SQLAlchemy helper library. On this, we can find the `session`
# object, where we do most of our interactions (like committing, etc.)

db = SQLAlchemy()

# # setup for s3
# conn = S3Connection(os.environ["AWS_ACCESS_KEY"], os.environ["AWS_SECRET_KEY"])
# bucket = conn.get_bucket(os.environ['AWS_BUCKET'])

##############################################################################
# Model definitions

class User(db.Model):
    """User of the app"""

    __tablename__ = 'users'

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_name = db.Column(db.String(64))
    email = db.Column(db.String(64), nullable=False)
    password_hash = db.Column(db.String(128))
    location = db.Column(db.String(64))
    about_me = db.Column(db.String(64))
    # member_since = db.Column(db.DateTime(), default=datetime.utcnow())
    # last_seen = db.Column(db.DateTime(), default=datetime.utcnow())

    def __repr__(self):
        """Provide helpful representation when printed"""
        return "<User user_id=%s email=%s>" % (self.user_id, self.email)

    # def ping(self):
    #     self.last_seen = datetime.utcnow()
    #     db.session.add(self)

    @property
    def password(self):
        raise AttributeError('The password is not a readable attribute')

    @password.setter
    def password(self, password):
         """generate the password hash when user set the password"""
         self.password_hash = generate_password_hash(password)


    def verify_password(self, password):
        """verify the password by comparing the entered password to the hash;
        returns True or False"""
        return check_password_hash(self.password_hash, password)


class Comment(db.Model):
    """Comments left by users for a specific post"""

    __tablename__ = 'comments'

    comment_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    content = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.post_id'), nullable=False)
    timestamp = db.Column(db.TIMESTAMP, index=True, default=datetime.utcnow())

    user = db.relationship("User",
                       backref=db.backref("comments", order_by=timestamp))

    post = db.relationship("Post",
                            backref=db.backref("comments", order_by=timestamp))

    def __repr__(self):
        """Provide helpful representation when prints"""
        return "<Comment id=%s content=%s>" % (self.comment_id, self.content)



class Post(db.Model):
    """Question posted by users that people voted on"""

    __tablename__ = 'posts'

    post_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    description = db.Column(db.Text)
    # option_text_1 = db.Column(db.Text)
    # option_text_2 = db.Column(db.Text)
    # option_pic_1 = db.Column(db.String)
    # option_pic_2 = db.Column(db.String)
    timestamp = db.Column(db.TIMESTAMP, index=True, default=datetime.utcnow() )

    author = db.relationship("User", backref=db.backref("posts", order_by=timestamp))



    def __repr__(self):
        """Return the post id and description when printed"""
        return "<Post post_id=%s, description=%s>" % (self.post_id, self.description)

    @classmethod
    def get_all_posts_id(cls, post_list=None):
        """returns a list of all posts with post id"""
        if not post_list:
            posts = cls.query.all()
        else:
            posts = post_list
        post_id_list = []
        for post in posts:
            post_id_list.append(post.post_id)
        return post_id_list

    @classmethod
    def get_all_posts_by_tag(cls, tag):
        posts = cls.query.filter(cls.tags.any(tag_name=tag)).all()
        if posts:
            post_id_list = []
            for post in posts:
                post_id_list.append(post.post_id)
            return post_id_list
        else:
            raise Exception("no post with such tag %s" % tag)





class Vote(db.Model):
    """Users' vote on a specific question/post"""

    __tablename__ = 'votes'

    vote_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    # post_id = db.Column(db.Integer, db.ForeignKey('posts.post_id'), nullable=False)
    vote = db.Column(db.Integer, db.ForeignKey('choices.choice_id'), nullable=False)
    timestamp = db.Column(db.TIMESTAMP, default=datetime.utcnow())

    user = db.relationship("User", backref=db.backref("votes", order_by=timestamp))
    # post = db.relationship("Post", backref=db.backref("votes", order_by=timestamp))

    choice = db.relationship("Choice", backref=db.backref("vote", order_by=timestamp))



    def __repr__(self):
        """Return the post id and description when printed"""
        return "<Vote vote_id=%s, vote=%s>" % (self.vote_id, self.vote)

class Choice(db.Model):
    """ Files (images, videos, audio etc) associated with specific post """

    __tablename__ = "choices"

    choice_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text_choice = db.Column(db.Text)
    file_name = db.Column(db.String(250))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.post_id'), nullable=False)

    post = db.relationship("Post", backref=db.backref("choices", order_by=choice_id))

    def __repr__(self):
        """Return the post id and description when printed"""
        return "<Choice text_choice=%s, file_name=%s, post_id=%s>" % \
               (self.text_choice, self.file_name, self.post_id)

    @classmethod
    def store_img(cls, file):
        k = Key(bucket)
        k.key = hashlib.sha512(str(self.choice_id)).hexdigest()
        k.set_contents_from_file(file)
        k.set_canned_acl('public-read')

    def retrieve_img(self, choice_list):
        hash_files = {}
        for choice in choice_list:
            hash_files[choice] = hashlib.sha512(str(choice.choice_id)).hexdigest()

    @classmethod
    def get_all_choice_by_post(cls, post_id):
        choices = cls.query.filter(cls.post_id==post_id).all()


class Tag(db.Model):
    """ Tags table """

    __tablename__ = "tags"

    tag_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tag_name = db.Column(db.String(100), nullable=False)

    posts = db.relationship("Post", secondary="tagsposts", backref=db.backref("tags", order_by=tag_id))


    def __repr__(self):
        return "<Tag tag_id=%s tag_name=%s>" % (self.tag_id, self.tag_name)

    @classmethod
    def get_all_tag_names(cls):
        """returns a list of all tag names"""
        tags = cls.query.all()
        tags_list = []
        for tag in tags:
            tag_name = tag.tag_name
            tag_name = str(tag_name)
            tags_list.append(tag_name)
        return tags_list

    @classmethod
    def get_tags_by_post_id(cls, post_id):
        tags = cls.query.filter(cls.posts.any(post_id=post_id)).all()
        return tags


class TagPost(db.Model):
    """Association table for Tages and Posts"""
    __tablename__ = "tagsposts"
    tagpost_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer,db.ForeignKey('posts.post_id'), nullable=False)
    tag_id = db.Column(db.Integer,db.ForeignKey('tags.tag_id'), nullable=False)





##############################################################################
# Helper functions

def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///opinionated.db'
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app
    connect_to_db(app)
    print "Connected to DB."