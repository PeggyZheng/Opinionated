"""Models and database functions for Opinionated project."""

from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime



# This is the connection to the SQLite database; we're getting this through
# the Flask-SQLAlchemy helper library. On this, we can find the `session`
# object, where we do most of our interactions (like committing, etc.)

db = SQLAlchemy()


##############################################################################
# Model definitions

class User(db.Model):
    """User of the app"""

    __tablename__ = 'users'

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
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
    option_text_1 = db.Column(db.Text)
    option_text_2 = db.Column(db.Text)
    option_pic_1 = db.Column(db.String)
    option_pic_2 = db.Column(db.String)
    timestamp = db.Column(db.TIMESTAMP, index=True, default=datetime.utcnow() )

    author = db.relationship("User",
                       backref=db.backref("posts", order_by=timestamp))


    def __repr__(self):
        """Return the post id and description when printed"""
        return "<Post post_id=%s, description=%s>" % (self.post_id, self.description)


class Vote(db.Model):
    """Users's vote on a specific question/post"""

    __tablename__ = 'votes'

    vote_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.post_id'), nullable=False)
    vote = db.Column(db.Integer)
    timestamp = db.Column(db.TIMESTAMP, index=True, default=datetime.utcnow())

    user = db.relationship("User",
                       backref=db.backref("votes", order_by=timestamp))
    post = db.relationship("Post",
                       backref=db.backref("votes", order_by=timestamp))



    def __repr__(self):
        """Return the post id and description when printed"""
        return "<Vote vote_id=%s, vote=%s>" % (self.vote_id, self.vote)




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