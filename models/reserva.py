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
                fecha_viaje_str = str(resultado_fecha["fecha_viaje"])
                if fecha_viaje_str != fecha_reserva:
                    raise Exception(f"La fecha del viaje ID {viaje_id} es el {fecha_viaje_str} no el {fecha_reserva}" )
                
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
                    "viaje_id": viaje_id,
                    "estado_id": estado_id,
                    "asiento_id": asiento_id
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
            
            # Construir la respuesta
            respuesta = {
                "reserva_id": reserva_id,
                "pasajero_id": reserva_data.get("pasajero_id") if isinstance(reserva_data, dict) else reserva_data[1],
                "fecha_reserva": str(reserva_data.get("fecha_reserva")) if isinstance(reserva_data, dict) else str(reserva_data[2]),
                "observacion": reserva_data.get("observacion") if isinstance(reserva_data, dict) else reserva_data[3],
                "fecha_creacion": str(reserva_data.get("fecha_creacion")) if isinstance(reserva_data, dict) else str(reserva_data[4]) if len(reserva_data) > 4 else None,
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