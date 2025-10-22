from flask import Blueprint, request, jsonify
from models.vehiculo import Vehiculo
from tools.jwt_required import jwt_token_requerido

#Crear un modulo blueprint para implementar el servicio web de usuario (login, cambiar clave, registrar, etc)
ws_vehiculo = Blueprint('ws_vehiculo', __name__)

#Instanciar a la clase usuario
vehiculo = Vehiculo()


#Endpoint para registrar nuevos vehiculos
@ws_vehiculo.route('/vehiculo/registrar', methods=['POST'])
@jwt_token_requerido
def registrar():
    #Obtener los datos que se envian como parámetros de entrada
    data = request.get_json()
    
    #pasar los datos a variables
    #conductor_id, marca, modelo, placa, color, pasajeros
    conductor_id = data.get('conductor_id')
    marca = data.get('marca')
    modelo = data.get('modelo')
    placa = data.get('placa')
    color = data.get('color')
    pasajeros = data.get('pasajeros')
    
    #Validar si contamos con los parámetros de email y clave
    if not all([conductor_id, marca, modelo, placa, color, pasajeros]):
        return jsonify({'status': False, 'data': None, 'message': 'Faltan datos obligatorios'}), 400
    
    #Registrar al usuario
    try:
        resultado, mensaje = vehiculo.registrar(conductor_id, marca, modelo, placa, color, pasajeros)
        if resultado:
            return jsonify({'status': True, 'data': None, 'message': 'Vehiculo registrado'}), 200
        else:
            return jsonify({'status': False, 'data': None, 'message': mensaje}), 500
    except Exception as e:
        return jsonify({'status': False, 'data': None, 'message': str(e)}), 500

