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
                insert into reserva_viaje (reserva_id, viaje_id, estado_id)
                values(%s,%s,%s)
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
            
            #5. Iterar en el json array, el cual trae los viajes seleccionados por el pasajero
            for detalle in detalles_viaje:
                viaje_id = detalle.get("viaje_id")
                estado_id = detalle.get("estado_id")
                
                #5.0 Validar la fecha de viaje
                cursor.execute(sql_validar_fecha, [viaje_id])
                resultado_fecha = cursor.fetchone()
                
                if not resultado_fecha:
                    raise Exception (f"El viaje ID {viaje_id} no existe")
                
                #Extraer la fecha de viaje y comparar con la fecha de reserva
                fecha_viaje_str = str(resultado_fecha["fecha_viaje"])
                if fecha_viaje_str != fecha_reserva:
                    raise Exception(f"La fecha del viaje ID {viaje_id} es el {fecha_viaje_str} no el {fecha_reserva}" )
                
                #5.1 Reducir el número de asientos
                cursor.execute(sql_actualizar_viaje, [viaje_id])
                
                #Verificar si se actualizó un registro (es decir si había asientos disponibles)
                if cursor.rowcount == 0:
                    raise Exception(f"No hay asientos disponibles en el viaje con ID {viaje_id}")
                
                #5.2 Insertar en la tabla reserva_viaje
                cursor.execute(sql_reserva_viaje, [reserva_id, viaje_id, estado_id])
            
            #6. Confirmar la transacción (Registro de la reserva, registro de la reserva viaje y la actualización de asientos disponibles)
            con.commit()
            
            #7. Retornar una respuesta
            return True, "Reserva y detalles registrados con exito"
            
        except Exception as e:
            #8. En caso de que ocurra un error, hacer rollback y abortar toda la transacción
            con.rollback()
            
            #9. Retornar el error especifico
            return False, f'Error al registrar la reserva: {str(e)}'
                
        finally:
            #10. Cerrar el cursor y la conexión
            cursor.close()
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
            
            #4. Obtener el último ID de la reserva registrada
            sql_actualizar_viaje = """
                update viaje
                set asientos_disponibles = asientos_disponibles + 1
                where id = %s
            """
            
            
            #6. Confirmar la transacción (Registro de la reserva, registro de la reserva viaje y la actualización de asientos disponibles)
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