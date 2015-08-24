import unittest
from flask import Flask, url_for
from app.models import User, Post, Choice, db
import os


basedir = os.path.abspath(os.path.dirname(__file__))

def create_app():
    app = Flask("test", template_folder=basedir + "/../app/templates")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'opinionated-test.db')
    app.config['SERVER_NAME'] = 'localhost:5000'
    app.debug = True
    db.app = app
    db.init_app(app)
    return app

class BasicsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        from app.server import login, show_all_posts
        self.app.add_url_rule('/', 'login', login)
        self.app.add_url_rule('/home', 'show_all_posts', show_all_posts)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_login(self):
        response = self.client.get(url_for('login'))
        print self.app.url_map
        print response
        self.assertTrue('Home' in response.data)
        self.assertTrue('Profile' in response.data)
        self.assertTrue('Search by tag' in response.data)
        self.assertTrue('Post a question' in response.data)

    def test_show_all_posts(self):
        response = self.client.get('/home')
        print response
        self.assertTrue('Home' in response.data)
        self.assertTrue('Featured tags' in response.data)