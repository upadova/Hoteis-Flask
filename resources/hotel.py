from models.sites import SiteModel
from flask_restful import Resource, reqparse
from models.hotel import HotelModel
from flask_jwt_extended import jwt_required
import psycopg2
from resources.filtros import normalize_params, consulta_sem_cidade, consulta_com_cidade

path_params = reqparse.RequestParser()
path_params.add_argument('cidade', type=str)
path_params.add_argument('estrelas_min', type=float)
path_params.add_argument('estrelas_max', type=float)
path_params.add_argument('diaria_min', type=float)
path_params.add_argument('diaria_max', type=float)
path_params.add_argument('limit', type=int)
path_params.add_argument('offset', type=int)


class Hoteis(Resource):
    def get(self):
        conexao = psycopg2.connect(user='upcarteira', password='90533', host='localhost', port='5432', database='upcarteira')
        cursor = conexao.cursor()
        dados = path_params.parse_args()
        dados_validos = {chave:dados[chave] for chave in dados if dados[chave] is not None}
        parametros = normalize_params(**dados_validos)

        if not parametros.get('cidade'):
            tupla = tuple([parametros[chave] for chave in parametros])
            cursor.execute(consulta_sem_cidade, tupla)
            resultado = cursor.fetchall()
        else:
            tupla = tuple([parametros[chave] for chave in parametros])
            cursor.execute(consulta_com_cidade, tupla)
            resultado = cursor.fetchall()
        hoteis = []
        print(resultado)
        if resultado:
            for linha in resultado:
                    hoteis.append({
                            'hotel_id': linha[0],
                            'nome': linha[1],
                            'estrelas': linha[2],
                            'diaria': linha[3],
                            'cidade': linha[4],
                            'site_id': linha[5]
                        })
        return {'hoteis': hoteis}


class Hotel(Resource):
    argumentos = reqparse.RequestParser()
    argumentos.add_argument('nome', type=str, required=True, help="The field 'nome' cannot be left blank")
    argumentos.add_argument('estrelas', type=float, required=True, help="The field 'nome' cannot be left blank")
    argumentos.add_argument('diaria')
    argumentos.add_argument('cidade')
    argumentos.add_argument('site_id', type=int, required=True)

    def get(self, hotel_id):
        hotel = HotelModel.find_hotel(hotel_id)
        if hotel:
            return hotel.json(), 200
        return {'message': 'Hotel {} not found'.format(hotel_id)}, 404

    @jwt_required()
    def post(self, hotel_id):
        if HotelModel.find_hotel(hotel_id):
            # bad request
            return {"message": "Hotel id {} already exists.".format(hotel_id)}, 400

        dados = Hotel.argumentos.parse_args()
        hotel = HotelModel(hotel_id, **dados)
        if not SiteModel.find_by_id(dados['site_id']):
            return {'message':'The hotel must be associate to a valid site id.'}, 400
        try:
            hotel.save_hotel()
        except:
            return {'menssage': 'An internal error ocurred trying to save hotel'}, 500
        return hotel.json(), 201  # created

    @jwt_required()
    def put(self, hotel_id):
        dados = Hotel.argumentos.parse_args()
        hotel_encontrado = HotelModel.find_hotel(hotel_id)
        if hotel_encontrado:
            try:
                hotel_encontrado.update_hotel(**dados)
                hotel_encontrado.save_hotel()
            except:
                return {'menssage': 'An internal error ocurred trying to save hotel'}, 500
            return hotel_encontrado.json(), 200
        novo_hotel = HotelModel(hotel_id, **dados)
        novo_hotel.save_hotel()
        return novo_hotel.json(), 201

    @jwt_required()
    def delete(self, hotel_id):
        hotel_encontrado = HotelModel.find_hotel(hotel_id)
        if hotel_encontrado:
            try:
                hotel_encontrado.delete_hotel()
            except:
                return {'message': 'An internal error deleted hotel'}
            return {'message': 'Hotel {} deleted'.format(hotel_id)}, 200
        return {'message': 'Hotel {} not found'.format(hotel_id)}, 400
