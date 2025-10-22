from flask import Blueprint, request, jsonify
from models.reserva import Reserva
from tools.jwt_required import jwt_token_requerido

#Crear un módulo blueprint para implementar el servicio web de reservas
ws_reserva = Blueprint('ws_reserva', __name__)

#Instanciar la clase reserva
reserva = Reserva()

#Endpoint para registrar reservas (posiblemente con multiples viajes)
@ws_reserva.route("/reserva/registrar", methods=['POST'])
@jwt_token_requerido
def registrar():
    #Obtener los datos que se envían como parámetros de entrada (JSON)
    data = request.get_json()
    
    #Pasar los datos a variables
    pasajero_id = data.get("pasajero_id")
    fecha_reserva = data.get("fecha_reserva") #La fecha en la que el usuario desea viajar
    observacion = data.get("observacion")
    detalles_viaje = data.get("detalles_viaje")
    
    #Validar si contamos con los parámetros de email y clave
    if not all([pasajero_id, fecha_reserva, observacion, detalles_viaje]):
        return jsonify({'status': False, 'data': None, 'message': 'Faltan datos obligatorios'}), 400
    
    #Validar que detalles_viaje no sea una lista vacia
    if not isinstance(detalles_viaje, list) or not detalles_viaje:
        return jsonify({'status': False, 'data': None, 'message': 'Detalles de viaje debe ser una lista con al menos un viaje'}), 400
    
    #Registrar la reserva
    try:
        #Llamar al método reggistrar de la clase Reserva
        resultado, mensaje = reserva.registrar(pasajero_id, fecha_reserva, observacion, detalles_viaje)
        
        if resultado:
            return jsonify({'status': True, 'data': None, 'message': mensaje}), 200
        else:
            #En caso de error (no hay asientos disponibles, algún dato que no se registro, etc)
            return jsonify({'status': False, 'data': None, 'message': mensaje}), 500
            
    except Exception as e:
        #Manejo de errores internos en el servidor
        return jsonify({'status': False, 'data': None, 'message': f'Error interno:{str(e)}'}), 500
   
   
    
    
#Endpoint para cancelar viajes
@ws_reserva.route("/reserva/viaje/cancelar", methods=['POST'])
@jwt_token_requerido
def cancelar():
    #Obtener los datos que se envían como parámetros de entrada (JSON)
    data = request.get_json()
    
    #Pasar los datos a variables
    reserva_id = data.get("reserva_id")
    viaje_id = data.get("viaje_id")
    
    #Validar si contamos con los parámetros de email y clave
    if not all([reserva_id, viaje_id]):
        return jsonify({'status': False, 'data': None, 'message': 'Faltan datos obligatorios'}), 400
    
    #Cancelar viaje de la reserva
    try:
        #Llamar al método cancelar de la clase Reserva
        resultado, mensaje = reserva.cancelar(reserva_id, viaje_id)
        
        if resultado:
            return jsonify({'status': True, 'data': None, 'message': mensaje}), 200
        else:
            #En caso de error 
            return jsonify({'status': False, 'data': None, 'message': mensaje}), 500
            
    except Exception as e:
        #Manejo de errores internos en el servidor
        return jsonify({'status': False, 'data': None, 'message': f'Error interno:{str(e)}'}), 500
    