from functools import wraps
from flask import request, redirect, url_for, session, flash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('loggedin'):
            flash("Please log in first")
            if request.url:
                return redirect(url_for('login', next=request.url))
            else:
                return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


