from flask_jwt_extended.utils import get_jti
from flask_restful import Resource, reqparse
from models.usuario import UserModel
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from werkzeug.security import safe_str_cmp
from blacklist import BLACKLIST

atributos = reqparse.RequestParser()
atributos.add_argument('login', type=str, required=True, help="The field 'login' cannot be left blank")
atributos.add_argument('senha', type=str, required=True, help="The field 'senha' cannot be left blank")

class User(Resource):
    # /usuarios
    def get(self, user_id):
        user = UserModel.find_user(user_id)
        if user:
            return user.json(), 200  
        return {'message': 'User {} not found'.format(user_id)}, 404

    @jwt_required()
    def delete(self, user_id):
        user_encontrado = UserModel.find_user(user_id) 
        if user_encontrado:
            try:
                user_encontrado.delete_user()
            except:
                return {'message': 'An internal error deleted user'}
            return {'message': 'User {} deleted'.format(user_id)}, 200
        return {'message': 'User {} not found'.format(user_id)}, 400

class UserRegister(Resource):
    #/cadastro
    def post(self): 
        dados = atributos.parse_args()
        if UserModel.find_by_login(dados['login']):
            return {"mesage": "The login {} already exists.".format(dados['login'])},400
        
        user = UserModel(**dados)
        user.save_user()
        return {"mesage": "User {} created sucessfully!".format(dados['login'])}, 201
class UserLogin(Resource):
    
    @classmethod
    def post(cls):
        dados = atributos.parse_args()
        user = UserModel.find_by_login(dados['login'])
        if user and safe_str_cmp(user.senha, dados['senha']):
            token_de_acesso = create_access_token(identity=user.user_id)
            return {'access_token': token_de_acesso}, 200
        return{'message':'The username or password is incorrect.'}, 401

class UserLogout(Resource):
    @jwt_required()
    def post(self):
        jwt_id = get_jwt()['jti']
        BLACKLIST.add(jwt_id)
        return {'message':'Logout success.'}, 200
        