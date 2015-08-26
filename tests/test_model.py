import unittest
from flask import Flask
from app.models import User, Post, Choice, Comment, Follow, Tag, TagPost, Vote, db
import os
import werkzeug.datastructures
import hashlib


basedir = os.path.abspath(os.path.dirname(__file__))

def create_app():
    app = Flask("test")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'opinionated-test.db')
    db.app = app
    db.init_app(app)
    return app

class BasicsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

class UserModelTestCase(unittest.TestCase):

    def test_set_password(self):
        u = User(email='peggy.zheng@utaccel.com', password='peggy')
        self.assertTrue(u.password_hash is not None)


    def test_password_verification(self):
        u = User(email='peggy.zheng@utaccel.com', password='peggy')
        self.assertTrue(u.verify_password('peggy'))
        self.assertFalse(u.verify_password('weibo'))


    def test_password_random_hash(self):
        u1 = User(email='peggy.zheng@utaccel.com', password='peggy')
        u2 = User(email='peggy.zheng@utaccel.com', password='peggy')
        self.assertNotEqual(u1.password_hash, u2.password_hash)

class ModelTestCase(BasicsTestCase):
    def test_create_users(self):
        """test the creation of a user with friends"""
        u1 = User.create(user_id=111, email="aaa@gmail.com", password="", user_name="lgdfv", gender="female", location="Shenzhen, China",
                        age_range=55, profile_pic="")
        u2 = User.create(user_id=112, email="aaa@gmail.com", password="", user_name="lgdfv", gender="female", location="Shenzhen, China",
                        age_range=55, friend_ids=[111], profile_pic="")

        self.assertEqual(u1.profile_pic, '')
        self.assertEqual(u2.gender, "female")
        return u1, u2

    def test_follow(self):
        """test to see when a user logged in, they should automatically follow all their friends"""
        u1, u2 = self.test_create_users()
        followeds = u2.get_all_followeds()
        followers = u1.get_all_followers()
        self.assertIn(u1, followeds.keys())
        self.assertIn(u2, followers.keys())
        self.assertTrue(u2.is_following(u1))
        self.assertFalse(u1.is_following(u2))


    """test a new post creation without filename and tags"""
    def test_create_post(self):
        """test to create a new post with file objects and make sure choices data are added to Choice table"""
        file_object1 = werkzeug.datastructures.FileStorage(filename="fileupload1.JPG")
        file_object2 = werkzeug.datastructures.FileStorage(filename="fileupload2.JPG")
        p = Post.create(author_id=1, description="test", file_name=None, tag_list=None, choice_data=[("text_choice1", file_object1), ("text_choice2", file_object2)])
        choices = Choice.get_choices_by_post_id(p.post_id)
        choices_text = [choice.choice_text for choice in choices]
        choices_file = [choice.file_name for choice in choices]
        self.assertEqual(p.author_id, 1)
        self.assertEqual(p.description, "test")
        self.assertEqual(p.file_name, None)
        self.assertIn("text_choice1", choices_text)
        self.assertIn("text_choice2", choices_text)
        self.assertEqual([p], Post.get_all_posts())
        for choice in choices:
            self.assertIn(hashlib.sha512(str(choice.choice_id)).hexdigest(), choices_file)
        return p

    def test_get_all_tags_by_post_id(self):
        file_object1 = werkzeug.datastructures.FileStorage(filename="fileupload1.JPG")
        file_object2 = werkzeug.datastructures.FileStorage(filename="fileupload2.JPG")
        p = Post.create(author_id=1, description="test", file_name=None, tag_list="food,fashion", choice_data=[("text_choice1", file_object1), ("text_choice2", file_object2)])
        tags = Tag.get_tags_by_post_id(p.post_id)
        tag_names = [str(tag.tag_name) for tag in tags]
        self.assertIn('food', tag_names)
        self.assertIn('fashion', tag_names)
        self.assertNotIn("apple", tag_names)

    def test_get_post_by_tag_name(self):
        file_object1 = werkzeug.datastructures.FileStorage(filename="fileupload1.JPG")
        file_object2 = werkzeug.datastructures.FileStorage(filename="fileupload2.JPG")
        p = Post.create(author_id=1, description="test", file_name=None, tag_list="food,fashion", choice_data=[("text_choice1", file_object1), ("text_choice2", file_object2)])
        self.assertIn(p, Post.get_posts_by_tag("food"))
        self.assertIn(p, Post.get_posts_by_tag("fashion"))
        self.assertNotIn(p, Post.get_posts_by_tag("apple"))


    def test_show_all_followed_posts(self):
        """test the show_all_followed_posts method"""
        u1, u2 = self.test_create_users()
        file_object1 = werkzeug.datastructures.FileStorage(filename="fileupload1.JPG")
        file_object2 = werkzeug.datastructures.FileStorage(filename="fileupload2.JPG")
        p1 = Post.create(author_id=u1.user_id, description="test", file_name=None, tag_list=None, choice_data=[("text_choice1", file_object1), ("text_choice2", file_object2)])
        all_followed_post = u2.followed_posts()
        self.assertIn(p1, all_followed_post)

    def test_create_vote(self):
        """test the creation of votes and check if it's correctly linked to post"""
        u1, u2 = self.test_create_users()
        p = self.test_create_post()
        choices = Choice.get_choices_by_post_id(p.post_id)
        c1, c2 = [choice.choice_id for choice in choices][0], [choice.choice_id for choice in choices][1]
        v1 = Vote.create(user_id=u1.user_id, choice_id=c1)
        v2 = Vote.create(user_id=u2.user_id, choice_id=c2)
        self.assertEqual(v1.user_id, u1.user_id)
        self.assertEqual(v2.choice_id, c2)
        self.assertIn(u1, p.get_voters())
        self.assertIn(u2, p.get_voters())
        self.assertEqual([u1, u2], p.get_voters())
        self.assertEqual(Vote.get_vote_by_post_and_user_id(p.post_id, u1.user_id), c1)
        self.assertNotEqual(Vote.get_vote_by_post_and_user_id(p.post_id, u1.user_id), c2)


    def test_count_vote(self):
        """test counting votes for a post also test"""
        u1, u2 = self.test_create_users()
        p = self.test_create_post()
        choices = Choice.get_choices_by_post_id(p.post_id)
        c1, c2 = [choice.choice_id for choice in choices][0], [choice.choice_id for choice in choices][1]
        v1 = Vote.create(user_id=u1.user_id, choice_id=c1)
        v2 = Vote.create(user_id=u2.user_id, choice_id=c2)
        vote_dict, total_votes, doughnut_chart_dict = p.count_votes()
        self.assertEqual(total_votes, 2)
        self.assertEqual({c1:1, c2:1}, vote_dict)



if __name__ == "__main__":

#
# if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    # app.debug = True


    unittest.main()
