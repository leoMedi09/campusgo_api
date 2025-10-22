from flask import Blueprint, request, jsonify
from models.entrada import Entrada
from tools.jwt_required import jwt_token_requerido

# Crear blueprint
ws_entrada = Blueprint('ws_entrada', __name__)

# Instancia del modelo
entrada = Entrada()

# 🎟️ Endpoint para comprar entrada
@ws_entrada.route('/entrada/comprar', methods=['POST'])
@jwt_token_requerido
def comprar_entrada():
    data = request.get_json()

    usuario_id = data.get("usuario_id")        # puede venir del token si lo deseas
    evento_id = data.get("evento_id")
    tipo_entrada_id = data.get("tipo_entrada_id")
    cantidad = data.get("cantidad")
    metodo_pago = data.get("metodo_pago")

    # 🧠 Validar campos obligatorios
    if not all([usuario_id, evento_id, tipo_entrada_id, cantidad, metodo_pago]):
        return jsonify({
            "status": False,
            "data": None,
            "message": "Faltan datos obligatorios."
        }), 400

    try:
        cantidad = int(cantidad)
        if cantidad <= 0:
            return jsonify({
                "status": False,
                "data": None,
                "message": "La cantidad debe ser mayor que 0."
            }), 400
    except ValueError:
        return jsonify({
            "status": False,
            "data": None,
            "message": "La cantidad debe ser un número entero válido."
        }), 400

    # Llamar al método del modelo
    resultado, mensaje = entrada.comprar(usuario_id, evento_id, tipo_entrada_id, cantidad, metodo_pago)

    if resultado:
        return jsonify({
            "status": True,
            "data": None,
            "message": mensaje
        }), 200
    else:
        return jsonify({
            "status": False,
            "data": None,
            "message": mensaje
        }), 400
