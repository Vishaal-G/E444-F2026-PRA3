import re

from flask import (Flask, render_template, session, redirect, url_for, flash,
                   request)
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, SubmitField
from wtforms.validators import DataRequired, Email

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'

bootstrap = Bootstrap(app)
moment = Moment(app)


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    email = EmailField('What is your UofT Email address?',
                       validators=[DataRequired(), Email()])
    submit = SubmitField('Submit')


@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            flash('Looks like you have changed your name!')
        old_email = session.get('email')
        if old_email is not None and old_email != form.email.data:
            flash('Looks like you have changed your email!')
        session['name'] = form.name.data
        session['email'] = form.email.data
        if 'utoronto' in form.email.data:
            return redirect(url_for('chatbot'))
        return redirect(url_for('index'))
    email = session.get('email')
    is_uoft = email is not None and 'utoronto' in email
    return render_template('index.html', form=form, name=session.get('name'),
                           email=email, is_uoft=is_uoft)


@app.route('/chatbot')
def chatbot():
    email = session.get('email')
    if email is None or 'utoronto' not in email:
        return redirect(url_for('index'))
    return render_template('chat.html', name=session.get('name'))


@app.route('/chat', methods=['POST'])
def chat():
    message = request.json['message'].strip()
    text = message.lower().rstrip('.!?')
    # Facts the user tells the bot live in the signed session cookie,
    # so they persist across requests from the same browser.
    memory = session.get('memory', {})

    tell = re.match(r"^my (.+?) is (.+)$", text)
    ask = re.match(r"^what(?: is|'s) my (.+)$", text)
    if tell:
        key = tell.group(1)
        value = message.rstrip('.!?')[tell.start(2):]
        memory[key] = value
        session['memory'] = memory
        if key == 'name':
            reply = 'Nice to meet you, {}!'.format(value)
        else:
            reply = "Got it, I'll remember your {} is {}.".format(key, value)
    elif ask:
        key = ask.group(1)
        if key in memory:
            reply = 'Your {} is {}.'.format(key, memory[key])
        else:
            reply = "I don't know your {} yet.".format(key)
    elif 'hello' in text:
        reply = 'Hello!'
    else:
        reply = "I don't understand."

    return {'reply': reply}


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))
