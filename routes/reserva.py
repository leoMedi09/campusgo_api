from flask import Blueprint, request, jsonify
from models.reserva import Reserva
from tools.jwt_required import jwt_token_requerido
from datetime import datetime, date

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
    observacion = data.get("observacion") or ""  # Observación puede estar vacía
    detalles_viaje = data.get("detalles_viaje")
    
    #Validar si contamos con los parámetros obligatorios (observacion puede estar vacía)
    if not all([pasajero_id, fecha_reserva, detalles_viaje]):
        return jsonify({'status': False, 'data': None, 'message': 'Faltan datos obligatorios: pasajero_id, fecha_reserva y detalles_viaje son requeridos'}), 400
    
    # Normalizar el formato de fecha a YYYY-MM-DD (año-mes-día con guiones)
    # Acepta tanto 2025/11/05 como 2025-11-05 y siempre convierte a 2025-11-05
    try:
        fecha_obj = None
        # Intentar convertir si viene con formato YYYY/MM/DD
        if '/' in fecha_reserva:
            fecha_obj = datetime.strptime(fecha_reserva, "%Y/%m/%d").date()
        # Si ya viene en formato YYYY-MM-DD, parsear directamente
        elif '-' in fecha_reserva:
            fecha_obj = datetime.strptime(fecha_reserva, "%Y-%m-%d").date()
        else:
            return jsonify({'status': False, 'data': None, 'message': 'Formato de fecha inválido. Use YYYY-MM-DD o YYYY/MM/DD'}), 400
        
        # SIEMPRE normalizar al formato YYYY-MM-DD (con guiones)
        fecha_reserva = fecha_obj.strftime("%Y-%m-%d")
        
        # Validar que la fecha de reserva sea del día de hoy en adelante
        fecha_hoy = date.today()
        if fecha_obj < fecha_hoy:
            return jsonify({
                'status': False, 
                'data': None, 
                'message': f'La fecha de reserva debe ser del día de hoy en adelante. Fecha enviada: {fecha_reserva}, Fecha de hoy: {fecha_hoy.strftime("%Y-%m-%d")}'
            }), 400
            
    except ValueError as e:
        return jsonify({'status': False, 'data': None, 'message': f'Formato de fecha inválido: {str(e)}. Use YYYY-MM-DD o YYYY/MM/DD'}), 400
    
    #Validar que detalles_viaje no sea una lista vacia
    if not isinstance(detalles_viaje, list) or not detalles_viaje:
        return jsonify({'status': False, 'data': None, 'message': 'Detalles de viaje debe ser una lista con al menos un viaje'}), 400
    
    #Validar que cada detalle de viaje tenga los campos requeridos
    for idx, detalle in enumerate(detalles_viaje):
        if not isinstance(detalle, dict):
            return jsonify({'status': False, 'data': None, 'message': f'El detalle de viaje #{idx + 1} no es un objeto válido'}), 400
        if not all([detalle.get("viaje_id"), detalle.get("estado_id"), detalle.get("asiento_id")]):
            return jsonify({'status': False, 'data': None, 'message': f'El detalle de viaje #{idx + 1} debe incluir viaje_id, estado_id y asiento_id'}), 400
        # Validar que los valores sean números enteros
        try:
            detalle["viaje_id"] = int(detalle["viaje_id"])
            detalle["estado_id"] = int(detalle["estado_id"])
            detalle["asiento_id"] = int(detalle["asiento_id"])
        except (ValueError, TypeError):
            return jsonify({'status': False, 'data': None, 'message': f'El detalle de viaje #{idx + 1} tiene valores inválidos (viaje_id, estado_id y asiento_id deben ser números enteros)'}), 400
    
    #Registrar la reserva
    try:
        # Validar tipos de datos
        try:
            pasajero_id = int(pasajero_id)
        except (ValueError, TypeError):
            return jsonify({'status': False, 'data': None, 'message': 'pasajero_id debe ser un número entero'}), 400
        
        #Llamar al método registrar de la clase Reserva
        resultado, respuesta = reserva.registrar(pasajero_id, fecha_reserva, observacion, detalles_viaje)
        
        if resultado:
            # Si resultado es True, respuesta contiene los datos de la reserva
            return jsonify({
                'status': True, 
                'data': respuesta, 
                'message': 'Reserva registrada exitosamente'
            }), 200
        else:
            # En caso de error (no hay asientos disponibles, algún dato que no se registro, etc)
            # respuesta contiene el mensaje de error
            return jsonify({'status': False, 'data': None, 'message': str(respuesta)}), 500
            
    except Exception as e:
        #Manejo de errores internos en el servidor
        import traceback
        error_msg = str(e)
        return jsonify({'status': False, 'data': None, 'message': f'Error interno: {error_msg}'}), 500
   
   
    
    
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


#Endpoint para buscar/filtrar viajes
@ws_reserva.route("/viajes/filtrar", methods=['POST'])
@jwt_token_requerido
def buscar_viajes():
    #Obtener los datos que se envían como parámetros de entrada (JSON)
    data = request.get_json() or {}
    
    #Pasar los datos a variables    
    campo_busqueda = data.get("campo_busqueda", "")
    texto_busqueda = data.get("texto_busqueda", "")
    asientos_disponibles = data.get("asientos_disponibles")
    sin_restricciones = data.get("sin_restricciones", False)
    desde = data.get("desde")
    hasta = data.get("hasta")
    
    # Normalizar fechas a formato YYYY-MM-DD (con guiones) - SIEMPRE
    try:
        if desde:
            # Convertir cualquier formato a YYYY-MM-DD
            if '/' in desde:
                fecha_obj = datetime.strptime(desde, "%Y/%m/%d").date()
                desde = fecha_obj.strftime("%Y-%m-%d")  # Formato con guiones
            elif '-' in desde:
                # Validar formato y normalizar
                fecha_obj = datetime.strptime(desde.split()[0], "%Y-%m-%d").date()
                desde = fecha_obj.strftime("%Y-%m-%d")  # Asegurar formato con guiones
            else:
                return jsonify({'status': False, 'data': None, 'message': 'Formato de fecha "desde" inválido. Use YYYY-MM-DD o YYYY/MM/DD'}), 400
        
        if hasta:
            # Convertir cualquier formato a YYYY-MM-DD
            if '/' in hasta:
                fecha_obj = datetime.strptime(hasta, "%Y/%m/%d").date()
                hasta = fecha_obj.strftime("%Y-%m-%d")  # Formato con guiones
            elif '-' in hasta:
                # Validar formato y normalizar
                fecha_obj = datetime.strptime(hasta.split()[0], "%Y-%m-%d").date()
                hasta = fecha_obj.strftime("%Y-%m-%d")  # Asegurar formato con guiones
            else:
                return jsonify({'status': False, 'data': None, 'message': 'Formato de fecha "hasta" inválido. Use YYYY-MM-DD o YYYY/MM/DD'}), 400
    except ValueError as e:
        return jsonify({'status': False, 'data': None, 'message': f'Formato de fecha inválido: {str(e)}. Use YYYY-MM-DD o YYYY/MM/DD'}), 400
    
    # Validar que si se proporciona "desde", también se pueda validar "hasta"
    if desde and hasta:
        try:
            fecha_desde = datetime.strptime(desde, "%Y-%m-%d").date()
            fecha_hasta = datetime.strptime(hasta, "%Y-%m-%d").date()
            if fecha_hasta < fecha_desde:
                return jsonify({'status': False, 'data': None, 'message': 'La fecha "hasta" debe ser mayor o igual a la fecha "desde"'}), 400
        except:
            pass
    
    #Buscar viajes
    try:
        # Debug: imprimir los parámetros que se van a pasar al modelo
        print(f"[DEBUG ROUTE] desde: {desde}, hasta: {hasta}")
        print(f"[DEBUG ROUTE] asientos_disponibles: {asientos_disponibles}, sin_restricciones: {sin_restricciones}")
        
        resultado, viajes = reserva.buscar_viajes(
            campo_busqueda=campo_busqueda,
            texto_busqueda=texto_busqueda,
            asientos_disponibles=asientos_disponibles,
            sin_restricciones=sin_restricciones,
            desde=desde,
            hasta=hasta
        )
        
        if resultado:
            return jsonify({
                'status': True,
                'data': viajes,
                'message': f'Se encontraron {len(viajes)} viaje(s)'
            }), 200
        else:
            return jsonify({'status': False, 'data': None, 'message': viajes}), 500
            
    except Exception as e:
        return jsonify({'status': False, 'data': None, 'message': f'Error interno: {str(e)}'}), 500
    