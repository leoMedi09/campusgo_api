from flask import Blueprint, request, jsonify
from datetime import datetime
from models.evento import Evento  # Correcto: instanciamos la clase Evento
from tools.jwt_required import jwt_token_requerido

# Crear un módulo para implementar el servicio web de reservas
ws_evento = Blueprint('ws_evento', __name__)  # Corregí el nombre del Blueprint

# Instanciar la clase Evento
evento = Evento()  # Cambié la instancia a Evento()

@ws_evento.route('/evento/crear', methods=['POST'])
@jwt_token_requerido
def crear():
    data = request.get_json()

    titulo = data.get("titulo")
    descripcion = data.get("descripcion")
    fechaInicio = data.get("fecha_inicio")
    fechaFin = data.get("fecha_fin")
    lugar = data.get("lugar")
    tipos_entrada = data.get("tipo_entrada")

    # 1️⃣ Validar campos obligatorios
    if not all([titulo, descripcion, fechaInicio, fechaFin, lugar, tipos_entrada]):
        return jsonify({
            'status': False,
            'data': None,
            'message': 'Faltan datos obligatorios.'
        }), 400

    # 2️⃣ Validar que tipo_entrada sea una lista con elementos
    if not isinstance(tipos_entrada, list) or len(tipos_entrada) == 0:
        return jsonify({
            'status': False,
            'data': None,
            'message': 'El campo tipo_entrada debe contener al menos un tipo válido.'
        }), 400

    # 3️⃣ Validar formato y lógica de fechas
    try:
        fechaInicio_dt = datetime.strptime(fechaInicio, '%Y-%m-%d %H:%M:%S')
        fechaFin_dt = datetime.strptime(fechaFin, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({
            'status': False,
            'data': None,
            'message': 'Formato de fecha incorrecto. Usa YYYY-MM-DD HH:MM:SS.'
        }), 400

    if fechaFin_dt <= fechaInicio_dt:
        return jsonify({
            'status': False,
            'data': None,
            'message': 'La fecha de fin debe ser posterior a la fecha de inicio.'
        }), 400

    # 4️⃣ Validar estructura interna de cada tipo_entrada
    for idx, tipo in enumerate(tipos_entrada, start=1):
        if not all([
            tipo.get("nombre_tipo"),
            tipo.get("precio") is not None,
            tipo.get("capacidad_total"),
            tipo.get("limite_por_persona")
        ]):
            return jsonify({
                'status': False,
                'data': None,
                'message': f'El tipo de entrada #{idx} no tiene todos los campos requeridos.'
            }), 400
        
        # Validar valores numéricos
        if tipo["precio"] <= 0 or tipo["capacidad_total"] <= 0 or tipo["limite_por_persona"] <= 0:
            return jsonify({
                'status': False,
                'data': None,
                'message': f'El tipo de entrada #{idx} tiene valores no válidos (deben ser > 0).'
            }), 400

    # 5️⃣ Intentar crear el evento
    try:
        resultado, mensaje = evento.registrar(titulo, descripcion, fechaInicio_dt, fechaFin_dt, lugar, tipos_entrada)
        if resultado:
            return jsonify({
                'status': True,
                'data': None,
                'message': mensaje
            }), 201
        else:
            return jsonify({
                'status': False,
                'data': None,
                'message': mensaje
            }), 500

    except Exception as e:
        return jsonify({
            'status': False,
            'data': None,
            'message': f'Error interno: {str(e)}'
        }), 500
        
        
@ws_evento.route('/evento/consultar', methods=['GET'])
@jwt_token_requerido  # Asegúrate de tener este decorador para la validación del JWT
def consultar_eventos():
    try:
        # Llamar al modelo para obtener los eventos activos
        resultado, eventos = Evento.consultar()  # Usamos la función consultar que ya definimos

        if resultado:
            return jsonify({
                'status': True,
                'data': eventos,
                'message': 'Eventos consultados exitosamente'
            }), 200
        else:
            return jsonify({
                'status': False,
                'data': None,
                'message': 'No se encontraron eventos activos'
            }), 404

    except Exception as e:
        return jsonify({
            'status': False,
            'data': None,
            'message': f'Error interno: {str(e)}'
        }), 500


