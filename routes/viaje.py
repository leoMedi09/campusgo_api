from flask import Blueprint, request, jsonify
from models.viaje import Viaje
from tools.jwt_required import jwt_token_requerido

# Crear un módulo blueprint para implementar el servicio web de viajes
ws_viaje = Blueprint('ws_viaje', __name__)

# Instanciar la clase viaje
viaje = Viaje()

# Endpoint para obtener un viaje específico con usuarios reservados
@ws_viaje.route("/viaje/listar", methods=['GET'])
@jwt_token_requerido
def obtener_viaje_con_usuarios():
    """
    Endpoint que devuelve un viaje específico con los usuarios que han reservado ese viaje
    Requiere el parámetro 'id' o 'viaje_id' en la query string
    """
    try:
        # Obtener el ID del viaje desde los parámetros de la query string
        viaje_id = request.args.get('id') or request.args.get('viaje_id')
        
        if not viaje_id:
            return jsonify({
                'status': False, 
                'data': None, 
                'message': 'El parámetro "id" o "viaje_id" es requerido'
            }), 400
        
        # Validar que el ID sea un número entero
        try:
            viaje_id = int(viaje_id)
        except (ValueError, TypeError):
            return jsonify({
                'status': False, 
                'data': None, 
                'message': 'El parámetro "id" debe ser un número entero válido'
            }), 400
        
        # Obtener el viaje con sus usuarios reservados
        resultado, viaje_data = viaje.obtener_viaje_con_usuarios(viaje_id)
        
        if resultado:
            return jsonify(viaje_data), 200
        else:
            return jsonify({'status': False, 'data': None, 'message': viaje_data}), 500
            
    except Exception as e:
        return jsonify({'status': False, 'data': None, 'message': f'Error interno: {str(e)}'}), 500

