import unittest
from flask import Flask
from app.models import User, Post, Choice, db
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

    # def tearDown(self):
    #     db.session.remove()
    #     db.drop_all()
    #     self.app_context.pop()

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

class PostModelTestCase(BasicsTestCase):
    """test a new post creation without filename and tags"""
    def test_create_post(self):
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
        for choice in choices:
            self.assertIn(hashlib.sha512(str(choice.choice_id)).hexdigest(), choices_file)



if __name__ == "__main__":

#
# if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    # app.debug = True


    unittest.main()
