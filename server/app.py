#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        image_url = data.get('image_url')
        bio = data.get('bio')

        try:
            new_user = User(
                username=username,
                image_url=image_url,
                bio=bio
            )
            new_user.password_hash = password

            db.session.add(new_user)
            db.session.commit()

            session['user_id'] = new_user.id

            return new_user.to_dict(rules=('-recipes',)), 201

        except ValueError as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422
        except IntegrityError:
            db.session.rollback()
            return {'errors': ['Username must be unique.']}, 422
        except Exception as e:
            db.session.rollback()
            return {'errors': [f'An unexpected error occurred: {e}']}, 500


class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.filter_by(id=user_id).first()
            if user:
                return user.to_dict(rules=('-recipes',)), 200
            else:
                session.pop('user_id', None)
                return {'message': 'User not found.'}, 401
        else:
            return {'message': 'Not authorized'}, 401

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.authenticate(password):
            session['user_id'] = user.id
            return user.to_dict(rules=('-recipes',)), 200
        else:
            return {'message': 'Unauthorized'}, 401

class Logout(Resource):
    def delete(self):
        user_id = session.get('user_id')
        if user_id:
            session.pop('user_id', None)
            return {}, 204
        else:
            return {'message': 'Unauthorized'}, 401

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            recipes = Recipe.query.all()
            return [recipe.to_dict(rules=('-user._password_hash',)) for recipe in recipes], 200
        else:
            return {'message': 'Not authorized'}, 401

    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'message': 'Not authorized'}, 401

        data = request.get_json()
        title = data.get('title')
        instructions = data.get('instructions')
        minutes_to_complete = data.get('minutes_to_complete')

        try:
            new_recipe = Recipe(
                title=title,
                instructions=instructions,
                minutes_to_complete=minutes_to_complete,
                user_id=user_id
            )
            db.session.add(new_recipe)
            db.session.commit()

            return new_recipe.to_dict(rules=('-user._password_hash',)), 201

        except ValueError as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422
        except Exception as e:
            db.session.rollback()
            return {'errors': [f'An unexpected error occurred: {e}']}, 500


api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)