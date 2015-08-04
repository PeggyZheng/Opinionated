import unittest
import sys

from app.models import User


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



if __name__ == "__main__":
    unittest.main()