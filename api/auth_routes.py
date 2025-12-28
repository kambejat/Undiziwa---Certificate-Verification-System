from flask import render_template, request, session, redirect, url_for, flash
from werkzeug.security import check_password_hash
from .init import api
from models import User

@api.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        if user:
            if not user.is_active:
                flash("Your account is inactive. Please contact the administrator.", "error")
            elif check_password_hash(user.password_hash, password):
                # Set session only for active users
                session["user_id"] = user.user_id
                session["username"] = user.username
                session["role"] = user.role
                session["phone"] = user.phone
                print("SESSION AT LOGIN:", dict(session))
                return redirect(url_for("api.index"))
            else:
                flash("Invalid username or password", "error")
        else:
            flash("Invalid username or password", "error")

    return render_template('login.html')


@api.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("api.login"))
