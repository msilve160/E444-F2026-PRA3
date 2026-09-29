import re
from datetime import datetime
from flask import (Flask, render_template, session, redirect,
                   url_for, flash, request)
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
bootstrap = Bootstrap(app)
moment = Moment(app)


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    email = EmailField('What is your UofT Email address?',
                       validators=[DataRequired()])
    submit = SubmitField('Submit')


def is_uoft(email):
    return email is not None and 'utoronto' in email


@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        old_name = session.get('name')
        old_email = session.get('email')
        if old_name is not None and old_name != form.name.data:
            flash('Looks like you have changed your name!')
        if old_email is not None and old_email != form.email.data:
            flash('Looks like you have changed your email!')
        session['name'] = form.name.data
        session['email'] = form.email.data
        if is_uoft(form.email.data):
            return redirect(url_for('chatroom'))
        return redirect(url_for('index'))
    return render_template('index.html', form=form,
                           name=session.get('name'),
                           email=session.get('email'),
                           current_time=datetime.utcnow())


@app.route('/chatroom')
def chatroom():
    if not is_uoft(session.get('email')):
        return redirect(url_for('index'))
    return render_template('chat.html', name=session.get('name'))


@app.route('/chat', methods=['POST'])
def chat():
    text = request.json['message'].strip()
    lower = text.lower()
    memory = session.get('memory', {})

    if m := re.search(r"my name is\s+(.+?)[.!?]*$", text, re.IGNORECASE):
        memory['name'] = m.group(1).strip()
        reply = f"Nice to meet you, {memory['name']}!"
    elif m := re.search(r"my favou?rite (\w+) is\s+(.+?)[.!?]*$", text,
                        re.IGNORECASE):
        thing, value = m.group(1).lower(), m.group(2).strip()
        memory['favorite ' + thing] = value
        reply = f"Got it, your favorite {thing} is {value}."
    elif "what is my name" in lower or "what's my name" in lower:
        if 'name' in memory:
            reply = f"Your name is {memory['name']}."
        else:
            reply = "I don't know your name yet. Tell me with 'My name is ...'."
    elif m := re.search(r"what(?: is|'s) my favou?rite (\w+)", lower):
        key = 'favorite ' + m.group(1)
        if key in memory:
            reply = f"Your {key} is {memory[key]}."
        else:
            reply = f"I don't know your {key} yet."
    elif "hello" in lower:
        reply = "Hello!"
    else:
        reply = "I don't understand."

    session['memory'] = memory  # reassign so Flask saves the change
    return {"reply": reply}


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))