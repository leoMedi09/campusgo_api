from flask import Blueprint, request, jsonify
from models.viaje import Viaje
from tools.jwt_required import jwt_token_requerido

# Crear un módulo blueprint para implementar el servicio web de viajes
ws_viaje = Blueprint('ws_viaje', __name__)

# Instanciar la clase viaje
viaje = Viaje()

# Endpoint flexible: lista todos los viajes con usuarios; si envías id, devuelve solo ese viaje
@ws_viaje.route("/viaje/listar", methods=['GET'])
@jwt_token_requerido
def listar_o_obtener_viajes_con_usuarios():
    try:
        viaje_id = request.args.get('id') or request.args.get('viaje_id')

        if viaje_id is not None:
            try:
                viaje_id = int(viaje_id)
            except (ValueError, TypeError):
                return jsonify({'status': False, 'data': None, 'message': 'El parámetro "id" debe ser un número entero válido'}), 400

            resultado, data = viaje.obtener_viaje_con_usuarios(viaje_id)
        else:
            resultado, data = viaje.listar_viajes_con_usuarios()

        if resultado:
            return jsonify(data), 200
        else:
            return jsonify({'status': False, 'data': None, 'message': data}), 500

    except Exception as e:
        return jsonify({'status': False, 'data': None, 'message': f'Error interno: {str(e)}'}), 500

