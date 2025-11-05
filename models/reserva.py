from conexionBD import Conexion

class Reserva:
    def registrar(self, pasajero_id, fecha_reserva, observacion, detalles_viaje):
        try:
            #1. Abrir la conexión
            con = Conexion().open
            cursor = con.cursor()
            
            #2. Insertar en la tabla de reserva
            sql_reserva = """
                insert into reserva(pasajero_id, fecha_reserva, observacion)
                values (%s,%s,%s)
            """
            cursor.execute(sql_reserva, [pasajero_id, fecha_reserva, observacion])
            
            #3. Obtener el último ID de la reserva registrada
            reserva_id = cursor.lastrowid
            if not reserva_id:
                raise Exception("No se pudo obtener el ID de la reserva, por favor verifique")
            
            #4. Insertar en la tabla reserva_viaje, actualizar en la tabla viaje y validar la fecha de viaje
            sql_reserva_viaje = """
                insert into reserva_viaje (reserva_id, viaje_id, estado_id, asiento_id)
                values(%s,%s,%s,%s)
            """
            sql_actualizar_viaje = """
                update viaje
                set asientos_disponibles = asientos_disponibles - 1
                where id = %s and asientos_disponibles > 0
            """
            
            sql_validar_fecha = """
                select date(fecha_hora_salida) as fecha_viaje
                from viaje
                where id = %s
            """
            
            sql_validar_asiento = """
                select id, estado_id
                from asiento
                where id = %s and viaje_id = %s
            """
            
            sql_actualizar_asiento = """
                update asiento
                set estado_id = %s
                where id = %s and viaje_id = %s
            """
            
            detalles_registrados = []
            
            #5. Iterar en el json array, el cual trae los viajes seleccionados por el pasajero
            for detalle in detalles_viaje:
                viaje_id = detalle.get("viaje_id")
                estado_id = detalle.get("estado_id")
                asiento_id = detalle.get("asiento_id")
                
                # Validar que asiento_id esté presente
                if not asiento_id:
                    raise Exception(f"El asiento_id es obligatorio para el viaje ID {viaje_id}")
                
                #5.0 Validar la fecha de viaje
                cursor.execute(sql_validar_fecha, [viaje_id])
                resultado_fecha = cursor.fetchone()
                
                if not resultado_fecha:
                    raise Exception (f"El viaje ID {viaje_id} no existe")
                
                #Extraer la fecha de viaje y comparar con la fecha de reserva
                # Normalizar ambas fechas a formato YYYY-MM-DD (con guiones) para compararlas
                from datetime import datetime, date
                
                # Obtener la fecha del viaje de la BD y normalizarla a YYYY-MM-DD
                fecha_viaje_raw = resultado_fecha["fecha_viaje"]
                
                # Convertir fecha_viaje_raw a string en formato YYYY-MM-DD
                # La función date() de MySQL devuelve un objeto date de Python
                if isinstance(fecha_viaje_raw, date):
                    # Si es un objeto date, convertir directamente a YYYY-MM-DD
                    fecha_viaje_str = fecha_viaje_raw.strftime("%Y-%m-%d")
                elif isinstance(fecha_viaje_raw, datetime):
                    # Si es datetime, extraer solo la fecha y convertir a YYYY-MM-DD
                    fecha_viaje_str = fecha_viaje_raw.date().strftime("%Y-%m-%d")
                elif isinstance(fecha_viaje_raw, str):
                    # Si es string, parsear y normalizar a YYYY-MM-DD
                    fecha_str = fecha_viaje_raw.split()[0] if ' ' in fecha_viaje_raw else fecha_viaje_raw
                    try:
                        if '-' in fecha_str:
                            fecha_obj_temp = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                        elif '/' in fecha_str:
                            fecha_obj_temp = datetime.strptime(fecha_str, "%Y/%m/%d").date()
                        else:
                            # Intentar parsear como ISO
                            fecha_obj_temp = date.fromisoformat(fecha_str)
                        fecha_viaje_str = fecha_obj_temp.strftime("%Y-%m-%d")
                    except:
                        # Si falla, usar el string tal cual (esperando que ya esté en YYYY-MM-DD)
                        fecha_viaje_str = fecha_str
                else:
                    # Para cualquier otro tipo, convertir a string y parsear
                    fecha_str = str(fecha_viaje_raw).split()[0] if ' ' in str(fecha_viaje_raw) else str(fecha_viaje_raw)
                    try:
                        if hasattr(fecha_viaje_raw, 'date'):
                            fecha_obj_temp = fecha_viaje_raw.date()
                        else:
                            fecha_obj_temp = date.fromisoformat(fecha_str)
                        fecha_viaje_str = fecha_obj_temp.strftime("%Y-%m-%d")
                    except:
                        fecha_viaje_str = fecha_str
                
                # Normalizar fecha_reserva a YYYY-MM-DD (ya debería venir normalizada del endpoint)
                if '/' in fecha_reserva:
                    fecha_obj_temp = datetime.strptime(fecha_reserva, "%Y/%m/%d").date()
                    fecha_reserva_normalizada = fecha_obj_temp.strftime("%Y-%m-%d")
                elif '-' in fecha_reserva:
                    # Ya está en formato YYYY-MM-DD, solo asegurarnos de que no tenga hora
                    fecha_reserva_normalizada = fecha_reserva.split()[0] if ' ' in fecha_reserva else fecha_reserva
                else:
                    fecha_reserva_normalizada = fecha_reserva
                
                # Comparar las fechas normalizadas (ambas en formato YYYY-MM-DD con guiones)
                if fecha_viaje_str != fecha_reserva_normalizada:
                    raise Exception(f"La fecha del viaje ID {viaje_id} es el {fecha_viaje_str} no el {fecha_reserva_normalizada}" )
                
                #5.0.1 Validar que el asiento existe y no esté ya reservado para este viaje
                cursor.execute(sql_validar_asiento, [asiento_id, viaje_id])
                resultado_asiento = cursor.fetchone()
                
                if not resultado_asiento:
                    raise Exception(f"El asiento ID {asiento_id} no existe para el viaje ID {viaje_id}")
                
                # Verificar que el asiento no esté ya reservado (estado_id = 14 indica reservado)
                estado_asiento_actual = resultado_asiento.get("estado_id") if isinstance(resultado_asiento, dict) else resultado_asiento[1]
                # Si el estado_id es 14 (reservado) o 15 (ocupado), el asiento no está disponible
                # Si el estado es None, asumimos que está disponible
                if estado_asiento_actual is not None and estado_asiento_actual in [14, 15]:
                    raise Exception(f"El asiento ID {asiento_id} ya está reservado u ocupado para el viaje ID {viaje_id}")
                
                #5.1 Reducir el número de asientos
                cursor.execute(sql_actualizar_viaje, [viaje_id])
                
                #Verificar si se actualizó un registro (es decir si había asientos disponibles)
                if cursor.rowcount == 0:
                    raise Exception(f"No hay asientos disponibles en el viaje con ID {viaje_id}")
                
                #5.2 Marcar el asiento como reservado (estado_id = 14)
                cursor.execute(sql_actualizar_asiento, [estado_id, asiento_id, viaje_id])
                
                #5.3 Insertar en la tabla reserva_viaje
                cursor.execute(sql_reserva_viaje, [reserva_id, viaje_id, estado_id, asiento_id])
                
                # Guardar el detalle registrado para la respuesta
                detalles_registrados.append({
                    "viaje_id": int(viaje_id),
                    "estado_id": int(estado_id),
                    "asiento_id": int(asiento_id)
                })
            
            #6. Confirmar la transacción (Registro de la reserva, registro de la reserva viaje y la actualización de asientos disponibles)
            con.commit()
            
            #7. Obtener los datos completos de la reserva creada
            sql_consultar_reserva = """
                select id, pasajero_id, fecha_reserva, observacion, fecha_creacion
                from reserva
                where id = %s
            """
            cursor.execute(sql_consultar_reserva, [reserva_id])
            reserva_data = cursor.fetchone()
            
            # Función auxiliar para convertir fechas a string de forma segura
            def convertir_fecha(fecha):
                if fecha is None:
                    return None
                if isinstance(fecha, str):
                    return fecha
                return str(fecha)
            
            # Extraer datos de forma segura (el cursor es DictCursor, así que siempre será dict)
            if isinstance(reserva_data, dict):
                pasajero_id_resp = reserva_data.get("pasajero_id")
                fecha_reserva_resp = convertir_fecha(reserva_data.get("fecha_reserva"))
                observacion_resp = reserva_data.get("observacion") or ""
                fecha_creacion_resp = convertir_fecha(reserva_data.get("fecha_creacion"))
            else:
                # Fallback por si acaso no es dict
                pasajero_id_resp = reserva_data[1] if len(reserva_data) > 1 else None
                fecha_reserva_resp = convertir_fecha(reserva_data[2] if len(reserva_data) > 2 else None)
                observacion_resp = reserva_data[3] if len(reserva_data) > 3 else ""
                fecha_creacion_resp = convertir_fecha(reserva_data[4] if len(reserva_data) > 4 else None)
            
            # Construir la respuesta asegurando que todos los valores sean JSON serializables
            respuesta = {
                "reserva_id": int(reserva_id),
                "pasajero_id": int(pasajero_id_resp) if pasajero_id_resp is not None else None,
                "fecha_reserva": fecha_reserva_resp,
                "observacion": observacion_resp,
                "fecha_creacion": fecha_creacion_resp,
                "detalles_viaje": detalles_registrados
            }
            
            #8. Retornar una respuesta con los datos
            return True, respuesta
            
        except Exception as e:
            #9. En caso de que ocurra un error, hacer rollback y abortar toda la transacción
            if 'con' in locals():
                con.rollback()
            
            #10. Retornar el error especifico
            return False, f'Error al registrar la reserva: {str(e)}'
                
        finally:
            #11. Cerrar el cursor y la conexión
            if 'cursor' in locals():
                cursor.close()
            if 'con' in locals():
                con.close()
            
            
    def cancelar(self, reserva_id, viaje_id):
        try:
            #1. Abrir la conexión
            con = Conexion().open
            cursor = con.cursor()
            
            #2. Insertar en la tabla de reserva
            sql_reserva = """
                update reserva_viaje set estado_id=18
                where reserva_id = %s and viaje_id = %s and estado_id <> 15    
            """
            cursor.execute(sql_reserva, [reserva_id, viaje_id])
            
            #3. Validar la cancelación(Solo se debe actualizar cuando el usuario no se haya EMBARCADO)
            if cursor.rowcount == 0:
                #2. Insertar en la tabla de reserva
                sql_obtener_estado = """
                    select nombre as estado_viaje from estado where id = (select estado_id from reserva_viaje where reserva_id = %s and viaje_id = %s)
                """
                cursor.execute(sql_obtener_estado, [reserva_id, viaje_id])
                resultado_estado_viaje = cursor.fetchone()
                estado_viaje = resultado_estado_viaje['estado_viaje']
            
                raise Exception(f"No se puede cancelar un viaje cuyo estado es {estado_viaje}")
            
            #4. Actualizar los asientos disponibles del viaje
            sql_actualizar_viaje = """
                update viaje
                set asientos_disponibles = asientos_disponibles + 1
                where id = %s
            """
            cursor.execute(sql_actualizar_viaje, [viaje_id])
            
            #5. Confirmar la transacción (Actualización del estado de reserva_viaje y actualización de asientos disponibles)
            con.commit()
            
            #7. Retornar una respuesta
            return True, "Viaje anulado correctamente"
            
        except Exception as e:
            #8. En caso de que ocurra un error, hacer rollback y abortar toda la transacción
            con.rollback()
            
            #9. Retornar el error especifico
            return False, f'Error al cancelar el viaje: {str(e)}'
                
        finally:
            #10. Cerrar el cursor y la conexión
            cursor.close()
            con.close()