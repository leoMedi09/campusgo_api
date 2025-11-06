from flask import Blueprint, request, jsonify
from models.viaje import Viaje
from tools.jwt_required import jwt_token_requerido

# Crear un módulo blueprint para implementar el servicio web de viajes
ws_viaje = Blueprint('ws_viaje', __name__)

# Instanciar la clase viaje
viaje = Viaje()

# Endpoint para listar viajes con usuarios reservados
@ws_viaje.route("/viaje/listar", methods=['GET'])
@jwt_token_requerido
def listar_viajes_con_usuarios():
    """
    Endpoint que devuelve la lista de viajes con los usuarios que han reservado cada viaje
    """
    try:
        resultado, viajes = viaje.listar_viajes_con_usuarios()
        
        if resultado:
            return jsonify(viajes), 200
        else:
            return jsonify({'status': False, 'data': None, 'message': viajes}), 500
            
    except Exception as e:
        return jsonify({'status': False, 'data': None, 'message': f'Error interno: {str(e)}'}), 500

