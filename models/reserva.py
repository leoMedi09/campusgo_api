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
    
    def buscar_viajes(self, campo_busqueda="", texto_busqueda="", asientos_disponibles=None, sin_restricciones=False, desde=None, hasta=None):
        """
        Buscar viajes con filtros
        
        Args:
            campo_busqueda: Campo por el cual buscar (ej: "destino", "origen")
            texto_busqueda: Texto a buscar
            asientos_disponibles: True si solo mostrar viajes con asientos disponibles
            sin_restricciones: True si solo mostrar viajes sin restricciones
            desde: Fecha desde (formato YYYY-MM-DD)
            hasta: Fecha hasta (formato YYYY-MM-DD)
        """
        try:
            con = Conexion().open
            cursor = con.cursor()
            
            # Construir la consulta SQL base
            # Incluir todas las columnas necesarias para la respuesta
            sql = """
                SELECT 
                    v.id as viaje_id,
                    v.fecha_hora_salida,
                    v.fecha_hora_llegada,
                    COALESCE(v.punto_partida, v.origen) as punto_partida,
                    v.destino,
                    v.lat_partida,
                    v.lng_partida,
                    v.lat_destino,
                    v.lng_destino,
                    v.asientos_disponibles,
                    COALESCE(v.asientos_ofertados, v.asientos_disponibles) as asientos_ofertados,
                    v.precio,
                    v.vehiculo_id,
                    ve.marca,
                    ve.modelo,
                    ve.placa,
                    ve.color,
                    ve.id as vehiculo_id_detalle,
                    v.restricciones,
                    v.estado_id,
                    e.nombre as estado
                FROM viaje v
                INNER JOIN vehiculo ve ON v.vehiculo_id = ve.id
                LEFT JOIN estado e ON v.estado_id = e.id
                WHERE 1=1
            """
            
            params = []
            
            # Filtro por rango de fechas
            # La columna fecha_hora_salida en la BD está almacenada en formato DD-MM-YYYY HH:MM:SS (string)
            # La fecha viene en formato YYYY-MM-DD desde el endpoint (ej: 2025-11-05)
            # Necesitamos convertir fecha_hora_salida de DD-MM-YYYY a DATE para comparar correctamente
            if desde:
                # Convertir fecha_hora_salida de formato DD-MM-YYYY HH:MM:SS a DATE
                # y comparar con la fecha "desde" en formato YYYY-MM-DD
                sql += " AND DATE(STR_TO_DATE(v.fecha_hora_salida, '%%d-%%m-%%Y %%H:%%i:%%s')) >= STR_TO_DATE(%s, '%%Y-%%m-%%d')"
                params.append(desde)
            
            if hasta:
                # Convertir fecha_hora_salida de formato DD-MM-YYYY HH:MM:SS a DATE
                # y comparar con la fecha "hasta" en formato YYYY-MM-DD
                sql += " AND DATE(STR_TO_DATE(v.fecha_hora_salida, '%%d-%%m-%%Y %%H:%%i:%%s')) <= STR_TO_DATE(%s, '%%Y-%%m-%%d')"
                params.append(hasta)
            
            # Filtro por asientos disponibles
            if asientos_disponibles is True:
                sql += " AND v.asientos_disponibles > 0"
            
            # Filtro por restricciones
            if sin_restricciones is True:
                sql += " AND (v.restricciones IS NULL OR v.restricciones = '' OR v.restricciones = 'Sin restricciones')"
            
            # Filtro por búsqueda de texto
            if texto_busqueda and texto_busqueda.strip():
                texto_busqueda_like = f"%{texto_busqueda.strip()}%"
                if campo_busqueda and campo_busqueda.strip():
                    if campo_busqueda.lower().strip() == "destino":
                        sql += " AND v.destino LIKE %s"
                        params.append(texto_busqueda_like)
                    elif campo_busqueda.lower().strip() == "origen":
                        sql += " AND v.punto_partida LIKE %s"
                        params.append(texto_busqueda_like)
                    else:
                        # Buscar en ambos campos
                        sql += " AND (v.destino LIKE %s OR v.punto_partida LIKE %s)"
                        params.append(texto_busqueda_like)
                        params.append(texto_busqueda_like)
                else:
                    # Si hay texto pero no campo específico, buscar en ambos
                    sql += " AND (v.destino LIKE %s OR v.punto_partida LIKE %s)"
                    params.append(texto_busqueda_like)
                    params.append(texto_busqueda_like)
            
            # Solo mostrar viajes activos (estado_id = 1, que corresponde a "ACTIVO")
            # Filtrar por estado_id = 1 para mostrar solo viajes activos
            sql += " AND v.estado_id = 1"
            
            # Ordenar por fecha de salida
            sql += " ORDER BY v.fecha_hora_salida ASC"
            
            # Debug: imprimir la consulta SQL y los parámetros para verificar
            print(f"[DEBUG] SQL: {sql}")
            print(f"[DEBUG] Params: {params}")
            print(f"[DEBUG] desde: {desde}, hasta: {hasta}")
            
            cursor.execute(sql, params)
            resultados = cursor.fetchall()
            
            print(f"[DEBUG] Resultados encontrados: {len(resultados)}")
            # Debug: mostrar los primeros resultados para verificar
            if resultados:
                print(f"[DEBUG] Primer resultado: {resultados[0] if len(resultados) > 0 else 'N/A'}")
            
            # Convertir los resultados a una lista de diccionarios
            viajes = []
            for row in resultados:
                # Función auxiliar para obtener valores de forma segura
                def get_val(key, default=None):
                    if isinstance(row, dict):
                        return row.get(key, default)
                    return default
                
                def get_val_by_idx(idx, default=None):
                    if isinstance(row, dict):
                        return default
                    return row[idx] if len(row) > idx else default
                
                # Formatear fecha_hora_salida a formato DD-MM-YYYY HH:MM:SS para la respuesta
                fecha_salida_raw = get_val("fecha_hora_salida") or get_val_by_idx(1)
                fecha_salida_str = ""
                if fecha_salida_raw:
                    try:
                        from datetime import datetime
                        if isinstance(fecha_salida_raw, str):
                            # Si es string, intentar parsear
                            if ' ' in fecha_salida_raw:
                                fecha_obj = datetime.strptime(fecha_salida_raw.split()[0], "%Y-%m-%d")
                                hora_str = fecha_salida_raw.split()[1] if len(fecha_salida_raw.split()) > 1 else "00:00:00"
                            else:
                                fecha_obj = datetime.strptime(fecha_salida_raw, "%Y-%m-%d")
                                hora_str = "00:00:00"
                            fecha_salida_str = fecha_obj.strftime("%d-%m-%Y") + " " + hora_str
                        else:
                            # Si es datetime, formatear directamente
                            fecha_salida_str = fecha_salida_raw.strftime("%d-%m-%Y %H:%M:%S")
                    except:
                        fecha_salida_str = str(fecha_salida_raw)
                
                viaje = {
                    "viaje_id": get_val("viaje_id") or get_val("id") or get_val_by_idx(0),
                    "fecha_hora_salida": fecha_salida_str,
                    "punto_partida": get_val("punto_partida") or get_val_by_idx(2),
                    "destino": get_val("destino") or get_val_by_idx(3),
                    "lat_partida": float(get_val("lat_partida") or get_val_by_idx(4) or 0),
                    "lng_partida": float(get_val("lng_partida") or get_val_by_idx(5) or 0),
                    "lat_destino": float(get_val("lat_destino") or get_val_by_idx(6) or 0),
                    "lng_destino": float(get_val("lng_destino") or get_val_by_idx(7) or 0),
                    "asientos_disponibles": int(get_val("asientos_disponibles") or get_val_by_idx(8) or 0),
                    "asientos_ofertados": int(get_val("asientos_ofertados") or get_val_by_idx(9) or 0),
                    "restricciones": get_val("restricciones") or get_val_by_idx(10) or "",
                    "estado": get_val("estado") or get_val_by_idx(11) or "",
                    "vehiculo": {
                        "id": int(get_val("vehiculo_id_detalle") or get_val("vehiculo_id") or get_val_by_idx(12) or 0),
                        "marca": get_val("marca") or get_val_by_idx(13) or "",
                        "modelo": get_val("modelo") or get_val_by_idx(14) or "",
                        "placa": get_val("placa") or get_val_by_idx(15) or "",
                        "color": get_val("color") or get_val_by_idx(16) or ""
                    }
                }
                viajes.append(viaje)
            
            cursor.close()
            con.close()
            
            return True, viajes
            
        except Exception as e:
            if 'con' in locals():
                if 'cursor' in locals():
                    cursor.close()
                con.close()
            return False, f'Error al buscar viajes: {str(e)}'
    
    def listar_viajes_con_usuarios(self):
        """
        Lista todos los viajes con los usuarios que han reservado cada viaje
        
        Returns:
            tuple: (True, lista_viajes) si es exitoso, (False, mensaje_error) si hay error
        """
        try:
            from datetime import datetime
            
            con = Conexion().open
            cursor = con.cursor()
            
            # Consulta SQL para obtener viajes con sus usuarios reservados
            # Solo incluir reservas activas (estado_id no debe ser 18=cancelado ni 15=embarcado)
            sql = """
                SELECT 
                    v.id,
                    v.destino,
                    v.fecha_hora_salida,
                    u.id as usuario_id,
                    CONCAT(u.nombres, ' ', u.apellido_paterno, ' ', u.apellido_materno) as nombre_completo,
                    COALESCE(u.foto, 'default') as foto
                FROM viaje v
                LEFT JOIN reserva_viaje rv ON v.id = rv.viaje_id
                LEFT JOIN reserva r ON rv.reserva_id = r.id
                LEFT JOIN usuario u ON r.pasajero_id = u.id
                WHERE v.estado_id = 1
                AND (rv.estado_id IS NULL OR rv.estado_id NOT IN (18, 15))
                ORDER BY v.id, u.id
            """
            
            cursor.execute(sql)
            resultados = cursor.fetchall()
            
            # Agrupar resultados por viaje
            viajes_dict = {}
            
            for row in resultados:
                # Función auxiliar para obtener valores
                def get_val(key, default=None):
                    if isinstance(row, dict):
                        return row.get(key, default)
                    return default
                
                def get_val_by_idx(idx, default=None):
                    if isinstance(row, dict):
                        return default
                    return row[idx] if len(row) > idx else default
                
                viaje_id = get_val("id") or get_val_by_idx(0)
                destino = get_val("destino") or get_val_by_idx(1) or ""
                fecha_hora_salida = get_val("fecha_hora_salida") or get_val_by_idx(2)
                usuario_id = get_val("usuario_id") or get_val_by_idx(3)
                nombre_completo = get_val("nombre_completo") or get_val_by_idx(4)
                foto = get_val("foto") or get_val_by_idx(5) or "default"
                
                # Si el viaje no existe en el diccionario, crearlo
                if viaje_id not in viajes_dict:
                    # Formatear fecha_hora_salida a formato YYYY-MM-DD HH:MM:SS
                    fecha_hora_str = ""
                    if fecha_hora_salida:
                        try:
                            if isinstance(fecha_hora_salida, str):
                                # Si es string, puede estar en formato DD-MM-YYYY HH:MM:SS
                                if ' ' in fecha_hora_salida:
                                    fecha_part = fecha_hora_salida.split()[0]
                                    hora_str = fecha_hora_salida.split()[1] if len(fecha_hora_salida.split()) > 1 else "00:00:00"
                                    # Intentar parsear como DD-MM-YYYY primero (formato de BD)
                                    try:
                                        fecha_obj = datetime.strptime(fecha_part, "%d-%m-%Y")
                                        fecha_hora_str = fecha_obj.strftime("%Y-%m-%d") + " " + hora_str
                                    except:
                                        # Si falla, intentar como YYYY-MM-DD
                                        try:
                                            fecha_obj = datetime.strptime(fecha_part, "%Y-%m-%d")
                                            fecha_hora_str = fecha_obj.strftime("%Y-%m-%d") + " " + hora_str
                                        except:
                                            fecha_hora_str = fecha_hora_salida
                                else:
                                    # Solo fecha, sin hora
                                    try:
                                        fecha_obj = datetime.strptime(fecha_hora_salida, "%d-%m-%Y")
                                        fecha_hora_str = fecha_obj.strftime("%Y-%m-%d") + " 00:00:00"
                                    except:
                                        try:
                                            fecha_obj = datetime.strptime(fecha_hora_salida, "%Y-%m-%d")
                                            fecha_hora_str = fecha_obj.strftime("%Y-%m-%d") + " 00:00:00"
                                        except:
                                            fecha_hora_str = fecha_hora_salida + " 00:00:00"
                            else:
                                # Si es datetime, formatear directamente
                                fecha_hora_str = fecha_hora_salida.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            fecha_hora_str = str(fecha_hora_salida) if fecha_hora_salida else ""
                    
                    viajes_dict[viaje_id] = {
                        "id": viaje_id,
                        "destino": destino,
                        "fecha_hora": fecha_hora_str,
                        "usuariosReservados": []
                    }
                
                # Agregar usuario si existe (puede ser NULL si no hay reservas)
                if usuario_id and nombre_completo:
                    usuario = {
                        "id": int(usuario_id),
                        "nombre": nombre_completo.upper() if nombre_completo else "",
                        "foto": foto
                    }
                    # Evitar duplicados
                    usuarios_existentes = viajes_dict[viaje_id]["usuariosReservados"]
                    if not any(u["id"] == usuario["id"] for u in usuarios_existentes):
                        usuarios_existentes.append(usuario)
            
            # Convertir diccionario a lista
            viajes_lista = list(viajes_dict.values())
            
            cursor.close()
            con.close()
            
            return True, viajes_lista
            
        except Exception as e:
            if 'con' in locals():
                if 'cursor' in locals():
                    cursor.close()
                con.close()
            return False, f'Error al listar viajes con usuarios: {str(e)}'