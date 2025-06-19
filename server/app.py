#!/usr/bin/env python3

from flask import Flask, request, session
from flask_restful import Api, Resource
from flask_migrate import Migrate
from models import db, User, Recipe

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'

db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)

class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        image_url = data.get('image_url')
        bio = data.get('bio')
        if not username or not password:
            return {"error": "Username and password required"}, 422
        if User.query.filter_by(username=username).first():
            return {"error": "Username already exists"}, 422
        user = User(username=username, image_url=image_url, bio=bio)
        user.password_hash = password
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return user.serialize(), 201

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return user.serialize(), 200
        return {'error': 'Invalid username or password'}, 401

class Logout(Resource):
    def delete(self):
        if 'user_id' in session and session['user_id']:
            session.pop('user_id')
            return {}, 204
        return {'error': 'No active session'}, 401

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {}, 401
        user = User.query.get(user_id)
        if not user:
            return {}, 401
        return user.serialize(), 200

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {"error": "Unauthorized"}, 401
        recipes = Recipe.query.filter_by(user_id=user_id).all()
        return [r.serialize() for r in recipes], 200

    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return {"error": "Unauthorized"}, 401
        data = request.get_json()
        title = data.get("title")
        instructions = data.get("instructions")
        minutes_to_complete = data.get("minutes_to_complete")
        errors = []
        if not title:
            errors.append("Title is required.")
        if not instructions or len(instructions) < 50:
            errors.append("Instructions must be at least 50 characters long.")
        if errors:
            return {"errors": errors}, 422
        recipe = Recipe(
            title=title,
            instructions=instructions,
            minutes_to_complete=minutes_to_complete,
            user_id=user_id
        )
        db.session.add(recipe)
        db.session.commit()
        return recipe.serialize(), 201

api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session')
api.add_resource(RecipeIndex, '/recipes')

if __name__ == "__main__":
    app.run(debug=True)