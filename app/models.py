from app import db, login, app
from time import time
import jwt
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import pickle

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    password_hash = db.Column(db.String(128))
    dashboards = db.relationship('Dashboard', backref='author', lazy='dynamic')
    groups = db.relationship('Group', backref='creator', lazy='dynamic')


    # dashboard preferences
    summaries_sources = db.Column(db.LargeBinary(), index=True, default=pickle.dumps(['nat_law_review', 'jdsupra']))
    summaries_multiplier = db.Column(db.Integer, index=True, default=3)
    summaries_sectors = db.Column(db.LargeBinary(), index=True, default=pickle.dumps([]))


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')


    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)
    

    def __repr__(self):
        return '<User {}>'.format(self.username)  

class Dashboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    company_name = db.Column(db.String(64), index=True)
    display_name = db.Column(db.String(64), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Dashboard {}>'.format(self.company_name)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    name = db.Column(db.String(64), index=True)
    description = db.Column(db.String(200), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    companies = db.Column(db.LargeBinary(), index=True, default=pickle.dumps([]))

    def __repr__(self):
        return f'<Group {self.name} (ID {self.id})>'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))