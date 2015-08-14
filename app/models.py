"""Models and database functions for Opinionated project."""

from flask_sqlalchemy import SQLAlchemy
from flask import flash
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

# setup for s3
conn = S3Connection(os.environ["AWS_ACCESS_KEY"], os.environ["AWS_SECRET_KEY"])
bucket = conn.get_bucket(os.environ['AWS_BUCKET'])

# define allowed file type for uploading
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    """a helper function to see verify the file type uploaded"""
    return '.' in filename and filename.lower().rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


##############################################################################
# Model definitions

class User(db.Model):
    """User of the app"""

    __tablename__ = 'users'

    user_id = db.Column(db.BigInteger, primary_key=True)
    user_name = db.Column(db.String(64))
    email = db.Column(db.String(64), nullable=False)
    password_hash = db.Column(db.String(128))
    location = db.Column(db.String(64))
    about_me = db.Column(db.String(64))
    age_range = db.Column(db.Integer)
    gender = db.Column(db.String)
    fb_user_id = db

    # todo: need to decide if only allows for facebook login, if so, we could take out the password part
    # todo: change the datatype of user_id column to big integer

    posts = db.relationship("Post", backref=db.backref("author"), cascade="all, delete, delete-orphan")
    comments = db.relationship("Comment", backref=db.backref("user"), cascade="all, delete, delete-orphan")
    votes = db.relationship("Vote", backref=db.backref("user"), cascade="all, delete, delete-orphan")

    def __repr__(self):
        """Provide helpful representation when printed"""
        return "<User user_id=%s email=%s>" % (self.user_id, self.email)

    @property
    def password(self):
        """the password is necessary field when instantiate a user, however it is not an actual column in the db
        only the password hash will be saved"""
        raise AttributeError('The password is not a readable attribute')

    @password.setter
    def password(self, password):
        """generate the password hash when user set the password"""
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """verify the password by comparing the entered password to the hash;
        returns True or False"""
        return check_password_hash(self.password_hash, password)

    @classmethod
    def create(cls, user_id, email, password, user_name, age_range, gender, location=None, about_me=None):
        new_user = cls(user_id=user_id, email=email, password=password, user_name=user_name, location=location, about_me=about_me,
                       age_range=age_range, gender=gender)

        db.session.add(new_user)
        db.session.commit()
        return new_user

    @classmethod
    def get_all_users(cls):
        return cls.query.all()

    @classmethod
    def get_user_by_id(cls, user_id):
        return cls.query.get(user_id)

    @classmethod
    def get_user_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    def get_all_friends(self):
        return [friend.friend_id for friend in self.friendships]


class Friendship(db.Model):
    """Keep track of relationship between users"""

    __tablename__ = 'friendships'

    friendship_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)

    user = db.relationship("User",
                           primaryjoin="User.user_id == Friendship.admin_id",
                           backref=db.backref("friendships", order_by=friendship_id))

    def __repr__(self):
        """A helpful representation of the relationship"""

        return "Friendship between admin_id: %s and friend_id: %s>" % (self.admin_id, self.friend_id)

    @classmethod
    def add_friendship(cls, admin_id, friend_id):
        """Insert a new friendship into the friendships table"""
        friendship = cls(admin_id=admin_id, friend_id=friend_id)
        db.session.add(friendship)
        db.session.commit()




class Comment(db.Model):
    """Comments left by users for a specific post"""

    __tablename__ = 'comments'

    comment_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    content = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.post_id'), nullable=False)
    timestamp = db.Column(db.TIMESTAMP, index=True, default=datetime.utcnow())

    def __repr__(self):
        """Provide helpful representation when prints"""
        return "<Comment id=%s content=%s>" % (self.comment_id, self.content)

    @classmethod
    def create(cls, content, user_id, post_id):
        new_comment = cls(content=content, user_id=user_id, post_id=post_id)
        db.session.add(new_comment)
        db.session.commit()
        return new_comment

    @classmethod
    def get_comments_by_post_id(cls, post_id):
        return cls.query.filter_by(post_id=post_id).all()

    @classmethod
    def get_comment_by_comment_id(cls, comment_id):
        return cls.query.get(comment_id)

    @classmethod
    def delete_by_comment_id(cls, comment_id):
        comment = cls.get_comment_by_comment_id(comment_id)
        db.session.delete(comment)
        db.session.commit()

        flash('the comment has been deleted')



class Post(db.Model):
    """Question posted by users that people voted on"""

    __tablename__ = 'posts'

    post_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    description = db.Column(db.Text)
    file_name = db.Column(db.String(250))  # user can also upload a file in question body
    timestamp = db.Column(db.TIMESTAMP, index=True, default=datetime.utcnow())

    comments = db.relationship("Comment", backref=db.backref("post"), cascade="all, delete, delete-orphan")
    choices = db.relationship("Choice", backref=db.backref("post"), cascade="all, delete, delete-orphan")
    tagposts = db.relationship("TagPost", backref=db.backref("post"), cascade="all, delete, delete-orphan")

    def __repr__(self):
        """Return the post id and description when printed"""
        return "<Post post_id=%s, description=%s>" % (self.post_id, self.description)

    @classmethod
    def create(cls, author_id, description, file_name, tag_list, choice_data):
        # create the post first
        # upload image to aws s3

        new_post = cls(author_id=author_id, description=description)
        db.session.add(new_post)
        db.session.commit()

        if file_name:
            k1 = Key(bucket)
            k1.key = hashlib.sha512(str(new_post.post_id)).hexdigest()
            k1.set_contents_from_file(file_name)
            k1.set_canned_acl('public-read')
            new_post.file_name = k1.key
            db.session.commit()

        # if specified tags, create tags
        if tag_list:
            tag_names = tag_list.split(',')
            for tag_name in tag_names:
                tag = Tag.get_tag_by_name(tag_name)
                if not tag:  # create a new tag if tag doesn't already exist
                    tag = Tag.create(tag_name=tag_name)
                TagPost.create(tag_id=tag.tag_id, post_id=new_post.post_id)

        # create choices
        for choice_text, choice_file in choice_data:
            if choice_file:
                if allowed_file(choice_file.filename):
                    new_choice = Choice.create(choice_text=choice_text, post_id=new_post.post_id)

                    # upload image to aws s3
                    k = Key(bucket)
                    k.key = hashlib.sha512(str(new_choice.choice_id)).hexdigest()
                    k.set_contents_from_file(choice_file)
                    k.set_canned_acl('public-read')

                    # stored the hashed file id as url
                    new_choice.file_name = k.key
                    db.session.commit()

                else:
                    flash('the file type you uploaded is not valid')
            else:
                Choice.create(choice_text=choice_text, post_id=new_post.post_id)

        flash('Your question has been posted')


    @classmethod
    def delete_by_post_id(cls, post_id):
        # deleting the images from aws for the choices
        choices = Choice.get_choices_by_post_id(post_id)
        for choice in choices:
            k = Key(bucket)
            k.key = hashlib.sha512(str(choice.choice_id)).hexdigest()
            bucket.delete_key(k)

        post = cls.get_post_by_id(post_id)
        #deleting the image from the post description from aws
        k1 = Key(bucket)
        k1.key = hashlib.sha512(str(post.post_id)).hexdigest()
        bucket.delete_key(k1)

        db.session.delete(post)
        db.session.commit()


        #TODO: NEED TO REMOVE THE FILES FROM AWS as well

        flash('Your post has been deleted')


    @classmethod
    def get_all_posts(cls):
        return cls.query.all()

    @classmethod
    def get_post_by_id(cls, post_id):
        return cls.query.filter_by(post_id=post_id).first()

    @classmethod
    def get_posts_by_author_id(cls, author_id):
        return cls.query.filter_by(author_id=author_id).all()

    @classmethod
    def get_posts_by_tag(cls, tag):
        return cls.query.filter(cls.tags.any(tag_name=tag)).all()

    def count_votes(self):
        choices = Choice.get_choices_by_post_id(self.post_id)
        vote_dict = {}  # vote count dictionary that maps choice to number of votes
        for choice in choices:
            vote_dict[choice.choice_id] = len(choice.get_votes())
        total_votes = sum(vote_dict.values())
        return vote_dict, total_votes

    # todo: this method may need to be replaced by a new table between user and post to achieve better performance

    def check_choice_on_post_by_user_id(self, user_id):
        choice = db.session.query(Choice.choice_id).join(Vote).filter(Choice.post_id==self.post_id, Vote.user_id==user_id).first()
        if choice:
            # the vote will give you a tuple, so we need to use index to grab out the element
            return choice[0]

class Vote(db.Model):
    """
    Users' vote on a specific question/post;
    a vote is mapping to a choice and a user
    """

    __tablename__ = 'votes'

    vote_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    choice_id = db.Column(db.Integer, db.ForeignKey('choices.choice_id'), nullable=False)
    timestamp = db.Column(db.TIMESTAMP, default=datetime.utcnow())

    def __repr__(self):
        """Return the post id and description when printed"""
        return "<Vote vote_id=%s, choice_id=%s>" % (self.vote_id, self.choice_id)

    @classmethod
    def create(cls, user_id, choice_id):
        new_vote = cls(user_id=user_id, choice_id=choice_id)
        db.session.add(new_vote)
        db.session.commit()
        return new_vote

    @classmethod
    def get_votes_by_user_id(cls, user_id):
        return cls.query.filter_by(user_id=user_id).all()

    @classmethod
    def get_votes_by_post_id(cls, post_id):
        choices = Choice.get_choices_by_post_id(post_id)
        list_of_votes = [choice.votes for choice in choices]
        votes = [vote for votes in list_of_votes for vote in votes]

        return votes

    @classmethod
    def get_vote_by_post_and_user_id(cls, post_id, user_id):
        vote = db.session.query(Vote.vote_id).join(Choice).filter(Choice.post_id==post_id, Vote.user_id==user_id).first()
        if vote:
            return vote[0]


    @classmethod
    def get_vote_by_vote_id(cls, vote_id):
        return cls.query.get(vote_id)


    @classmethod
    def update_vote(cls, vote_id, new_choice):
        vote = cls.get_vote_by_vote_id(vote_id)
        vote.choice_id = new_choice
        db.session.commit()

class Choice(db.Model):
    """ Files (images, videos, audio etc) associated with specific post """

    __tablename__ = "choices"

    choice_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    choice_text = db.Column(db.Text)
    file_name = db.Column(db.String(250))  # this is in fact the image url
    post_id = db.Column(db.Integer, db.ForeignKey('posts.post_id'), nullable=False)

    votes = db.relationship("Vote", backref=db.backref("choice"), cascade="all, delete, delete-orphan")

    def __repr__(self):
        """Return the post id and description when printed"""
        return "<Choice choice_text=%s, file_name=%s, post_id=%s>" % \
               (self.choice_text, self.file_name, self.post_id)

    @classmethod
    def create(cls, choice_text, post_id, file_name=None):
        new_choice = cls(choice_text=choice_text, post_id=post_id, file_name=file_name)
        db.session.add(new_choice)
        db.session.commit()
        return new_choice

    @classmethod
    def get_choices_by_post_id(cls, post_id):
        return cls.query.filter_by(post_id=post_id).all()

    def get_votes(self):
        return Vote.query.filter_by(choice_id=self.choice_id).all()


class Tag(db.Model):
    """ Tags table """

    __tablename__ = "tags"

    tag_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tag_name = db.Column(db.String(100),
                         nullable=False)  # TODO: Turn the data type into db.text, otherwise it needs cast

    posts = db.relationship("Post", secondary="tagsposts", backref=db.backref("tags", order_by=tag_id))

    def __repr__(self):
        return "<Tag tag_id=%s tag_name=%s>" % (self.tag_id, self.tag_name)

    @classmethod
    def create(cls, tag_name):
        new_tag = cls(tag_name=tag_name)
        db.session.add(new_tag)
        db.session.commit()
        return new_tag

    @classmethod
    def get_tags_by_post_id(cls, post_id):
        return cls.query.filter(cls.posts.any(post_id=post_id)).all()

    @classmethod
    def get_all_tags(cls):
        return cls.query.all()

    @classmethod
    def get_tag_by_name(cls, tag_name):
        return cls.query.filter_by(tag_name=tag_name).first()


class TagPost(db.Model):
    """Association table for Tages and Posts"""
    __tablename__ = "tagsposts"
    tagpost_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.post_id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.tag_id'), nullable=False)

    @classmethod
    def create(cls, post_id, tag_id):
        new_tagpost = cls(post_id=post_id, tag_id=tag_id)
        db.session.add(new_tagpost)
        db.session.commit()
        return new_tagpost



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
