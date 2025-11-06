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
       
        base_url = request.host_url.rstrip('/')

        # Leer parámetros como string y sanitizar espacios
        viaje_id = request.args.get('id', type=str)
        if viaje_id is None:
            viaje_id = request.args.get('viaje_id', type=str)
        if isinstance(viaje_id, str):
            viaje_id = viaje_id.strip()
        if viaje_id == "":
            viaje_id = None

        # Elegir si listar todos o un solo viaje
        if viaje_id is not None:
            try:
                viaje_id = int(viaje_id)
            except (ValueError, TypeError):
                return jsonify({'status': False, 'data': None, 'message': 'El parámetro "id" debe ser un número entero válido'}), 400

            resultado, data = viaje.obtener_viaje_con_usuarios(viaje_id)
        else:
            resultado, data = viaje.listar_viajes_con_usuarios()

        # Si la consulta fue exitosa, ajustar las URLs de las fotos
        if resultado:
            for v in data:
                # Si hay una foto, generar URL completa
                if v.get("foto"):
                    # Si la ruta ya comienza con "uploads", construimos URL completa
                    if v["foto"].startswith("uploads/"):
                        v["foto"] = f"{base_url}/{v['foto']}"
                    else:
                        # Si solo tiene el nombre (ej: "perfil1.jpg")
                        v["foto"] = f"{base_url}/uploads/fotos/usuarios/{v['foto']}"
                else:
                    # Si no hay foto, usar la default
                    v["foto"] = f"{base_url}/uploads/fotos/usuarios/default.png"

            return jsonify(data), 200

        else:
            return jsonify({'status': False, 'data': None, 'message': data}), 500

    except Exception as e:
        return jsonify({'status': False, 'data': None, 'message': f'Error interno: {str(e)}'}), 500




