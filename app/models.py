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
POSTS_PER_PAGE = 20


def allowed_file(filename):
    """a helper function to see verify the file type uploaded"""
    return '.' in filename and filename.lower().rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def parse_location(unicode):
    location = str(unicode)
    if "," in location:
        lst = location.split(',')
        return lst[0]
    else:
        return location


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
    profile_pic = db.Column(db.String)
    # fb_user_id = db

    # todo: need to decide if only allows for facebook login, if so, we could take out the password part
    # todo: change the datatype of user_id column to big integer

    posts = db.relationship("Post", backref=db.backref("author"), cascade="all, delete, delete-orphan")
    comments = db.relationship("Comment", backref=db.backref("user"), cascade="all, delete, delete-orphan")
    votes = db.relationship("Vote", backref=db.backref("user"), cascade="all, delete, delete-orphan")
    followed = db.relationship('Follow', primaryjoin="User.user_id == Follow.follower_id", backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic', cascade='all, delete-orphan')
    followers = db.relationship('Follow', primaryjoin="User.user_id == Follow.followed_id", backref=db.backref('followed', lazy='joined'),
                               lazy='dynamic', cascade='all, delete-orphan')


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
    def create(cls, user_id, email, password, user_name, age_range, gender, profile_pic, location=None, about_me=None, friend_ids=None):
        new_user = cls(user_id=user_id, email=email, password=password, user_name=user_name, location=location, about_me=about_me,
                       age_range=age_range, gender=gender, profile_pic=profile_pic)
        db.session.add(new_user)
        db.session.commit()
        if friend_ids: # follow all facebook friends who are also users of the app automatically when log in
            for friend_id in friend_ids:
                friend  = User.get_user_by_id(friend_id)
                if friend:
                    new_user.follow(friend)

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

    # def get_all_friends(self):
    #     return [friend.friend_id for friend in self.friendships]

    def update_user_info(self, user_name=None, age_range=None, gender=None, location=None, about_me=None, profile_pic=None):
        if user_name:
            if user_name != self.user_name:
                self.user_name = user_name
        if age_range:
            if age_range != self.age_range:
                self.age_range = age_range
        if gender:
            if gender != self.gender:
                self.gender = gender
        if location:
            if location != self.location:
                self.location = location
        if about_me:
            if about_me != self.about_me:
                self.about_me = about_me
        if profile_pic:
            if profile_pic != self.profile_pic:
                self.profile_pic = profile_pic
        db.session.commit()

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower_id=self.user_id, followed_id=user.user_id)
            db.session.add(f)
            db.session.commit()

    def unfollow(self, user):
        f = Follow.query.filter_by(followed_id=user.user_id).first()
        print f
        if f:
            db.session.delete(f)
            db.session.commit()


    def is_following(self, user):
        return Follow.query.filter(Follow.followed_id==user.user_id, Follow.follower_id==self.user_id).first() is not None

    def is_followed_by(self, user):
        return Follow.query.filter_by(Follow.follower_id==user.user_id, Follow.followed_id==self.user_id).first() is not None


    def get_all_followers(self):
        """this function returns a dictionary of info about all followers with the user object as key and timestamp as
        value"""
        follows = self.followers.all() #this returns the follow object where the followed_id is self
        followers = {}
        for follow in follows:
            followers[User.get_user_by_id(follow.follower_id)] = follow.timestamp

        return followers


    def get_all_followeds(self):
        follows = self.followed.all()
        followeds = {}
        for follow in follows:
            followeds[User.get_user_by_id(follow.followed_id)] = follow.timestamp
        return followeds

    def followed_posts(self):
        """gives a list all posts of users that self has been following"""
        followeds = self.get_all_followeds() #gives a dictionary with the key as user object
        followed_ids = [followed.user_id for followed in followeds]
        posts = Post.query.filter(Post.author_id.in_(followed_ids)).order_by(Post.timestamp.desc()).all()
        return posts

    def followed_posts_pagination(self, page):
        followeds = self.get_all_followeds() #gives a dictionary with the key as user object
        followed_ids = [followed.user_id for followed in followeds]
        return Post.query.filter(Post.author_id.in_(followed_ids)).order_by(Post.timestamp.desc()).paginate(page, per_page=POSTS_PER_PAGE, error_out=False)


# class Friendship(db.Model):
#     """Keep track of relationship between users"""
#
#     __tablename__ = 'friendships'
#
#     friendship_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
#     admin_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
#     friend_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
#
#     user = db.relationship("User",
#                            primaryjoin="User.user_id == Friendship.admin_id",
#                            backref=db.backref("friendships", order_by=friendship_id))
#
#     def __repr__(self):
#         """A helpful representation of the relationship"""
#
#         return "Friendship between admin_id: %s and friend_id: %s>" % (self.admin_id, self.friend_id)
#
#     @classmethod
#     def add_friendship(cls, admin_id, friend_id):
#         """Insert a new friendship into the friendships table"""
#         friendship = cls(admin_id=admin_id, friend_id=friend_id)
#         db.session.add(friendship)
#         db.session.commit()

class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.BigInteger, db.ForeignKey('users.user_id'), primary_key=True)
    followed_id = db.Column(db.BigInteger, db.ForeignKey('users.user_id'), primary_key=True)
    timestamp = db.Column(db.TIMESTAMP, index=True, default=datetime.utcnow())

    @classmethod
    def get_follow_by_follower_id(cls, user_id):
        return cls.query.filter(cls.follower_id==user_id).all()

    @classmethod
    def get_follow_by_followed_id(cls, user_id):
        return cls.query.filter(cls.followed_id==user_id).all()



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
    state = db.Column(db.Integer) # this can be null (undecided) or a specific choice id
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
        return new_post


    def update_decision(self, choice_id):
        self.state = choice_id
        db.session.commit()


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

        flash('Your post has been deleted')


    @classmethod
    def get_all_posts(cls):
        return cls.query.order_by(Post.timestamp.desc()).all()

    @classmethod
    def get_all_posts_pagination(cls, page):
        return cls.query.order_by(Post.timestamp.desc()).paginate(page, per_page=POSTS_PER_PAGE, error_out=False)


    @classmethod
    def get_post_by_id(cls, post_id):
        return cls.query.filter_by(post_id=post_id).first()

    @classmethod
    def get_posts_by_author_id(cls, author_id):
        return cls.query.filter_by(author_id=author_id).order_by(Post.timestamp.desc()).all()

    @classmethod
    def get_posts_by_tag(cls, tag):
        return cls.query.filter(cls.tags.any(tag_name=tag)).order_by(Post.timestamp.desc()).all()

    @classmethod
    def get_posts_by_tag_pagination(cls, tag, page):
        return cls.query.filter(cls.tags.any(tag_name=tag)).order_by(Post.timestamp.desc()).paginate(page, per_page=POSTS_PER_PAGE, error_out=False)

    def count_votes(self):
        choices = Choice.get_choices_by_post_id(self.post_id)
        vote_dict = {}  # vote count dictionary that maps choice to number of votes
        doughnut_chart_dict = self.doughnut_chart()
        for choice in choices:
            vote_dict[choice.choice_id] = len(choice.get_votes())
        total_votes = sum(vote_dict.values())
        return vote_dict, total_votes, doughnut_chart_dict

    def get_voters(self):
        voters = db.session.query(User).join(Vote).join(Choice).filter(Vote.choice_id==Choice.choice_id, Vote.user_id==User.user_id, self.post_id==Choice.post_id).all()
        return voters


    def doughnut_chart(self):
        choices = Choice.get_choices_by_post_id(self.post_id)
        chart_lst = [["Choice", "Votes"]]
        for choice in choices:
             if choice.choice_text:
                 chart_lst.append([str(choice.choice_text), len(choice.get_votes())])
             else:
                 index = choices.index(choice)
                 key = "choice" + str(index + 1)
                 chart_lst.append([key, len(choice.get_votes())])

        return chart_lst

    def bar_chart_gender(self):
        choices = Choice.get_choices_by_post_id(self.post_id)
        chart_lst = [["Choices", {"role": 'annotation'}]]
        voters = self.get_voters() # the voters for this post
        female_voters = set([voter for voter in voters if voter.gender=="female"])
        male_voters = set([voter for voter in voters if voter.gender=="male"])
        choice_dict = {}
        for choice in choices:
            if choice.choice_text:
                text = str(choice.choice_text)
            else:
                text = "choice " + str(choices.index(choice) + 1)
            chart_lst[0].insert(choices.index(choice) + 1, text)
            voters = set(choice.get_voters())
            female = len(female_voters.intersection(voters))
            male = len(male_voters.intersection(voters))
            choice_dict[choices.index(choice)] = (female, male)

        chart_lst.append(["Female", choice_dict[0][0], choice_dict[1][0], ""])
        chart_lst.append(["Male", choice_dict[0][1], choice_dict[1][1], ""])

        return chart_lst


    # todo: this method may need to be replaced by a new table between user and post to achieve better performance

    def count_votes_by_location(self):
        choices = Choice.get_choices_by_post_id(self.post_id)
        chart_lst = [["City"]]
        voters = self.get_voters()
        location_dict = {} # a dictionary with key as location, and a set of user objects as values
        for voter in voters:
            location = parse_location(voter.location)
            if location not in location_dict and location != None:
                location_dict[location] = set([voter])
            elif location in location_dict:
                location_dict[location].add(voter)
        print location_dict, "this is the location dict"

        for choice in choices:
            if choice.choice_text:
                text = str(choice.choice_text)
            else:
                text = "choice" + str(choices.index(choice) + 1)
            chart_lst[0].insert(choices.index(choice) + 1, text)

        for location in location_dict:
            temp_list = [location]
            for choice in choices:
                voters = set(choice.get_voters())
                count = len(location_dict[location].intersection(voters))
                temp_list.append(count)

            chart_lst.append(temp_list)
        return chart_lst

    def count_votes_by_age(self):
        choices = Choice.get_choices_by_post_id(self.post_id)
        chart_lst = [["Age group"]]
        voters = self.get_voters()
        age_dict = {}
        for voter in voters:
            age = str(voter.age_range)
            if age not in age_dict and age != None:
                age_dict[age] = set([voter])
            elif age in age_dict:
                age_dict[age].add(voter)
        for choice in choices:
            if choice.choice_text:
                text = str(choice.choice_text)
            else:
                text = "choice" + str(choices.index(choice) + 1)
            chart_lst[0].insert(choices.index(choice) + 1, text)

        for age in age_dict:
            temp_list = [age]
            for choice in choices:
                voters = set(choice.get_voters())
                count = len(age_dict[age].intersection(voters))
                temp_list.append(count)
            chart_lst.append(temp_list)
        return chart_lst



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
        return cls.query.filter_by(user_id=user_id).order_by(Vote.timestamp.desc()).all()

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

    @classmethod
    def get_choice_by_id(cls, choice_id):
        return cls.query.get(choice_id)

    def get_voters(self):
        voters = db.session.query(User).join(Vote).filter(Vote.choice_id==self.choice_id, Vote.user_id==User.user_id).all()
        return voters


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
    @classmethod
    def sort_all_tags_by_popularity(cls):
        all_tags = cls.get_all_tags()
        count_dict = {}
        for tag in all_tags:
            count = len(tag.posts)
            if count in count_dict:
                count_dict[count].append(tag)
            else:
                count_dict[count] = [tag]
        all_counts_sorted = sorted(count_dict.keys(), reverse=True)
        sorted_tag_list = []
        for count in all_counts_sorted:
            sorted_tag_list.extend(count_dict[count])
        return sorted_tag_list

    @classmethod
    def get_most_popular_tags(cls, n):
        """the argument n decides how many tags you want"""
        all_sorted_tags = cls.sort_all_tags_by_popularity()
        return all_sorted_tags[:n]


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
