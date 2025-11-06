import pymysql
try:
    from ..conexionBD import Conexion
except ImportError:
    from conexionBD import Conexion
from datetime import datetime
import json

class Viaje:
    def listarViajes(self, filtros):
        """
        Lista viajes con filtros opcionales y pasajeros reservados usando JSON_ARRAYAGG
        """
        try:
            db = Conexion().open
            cursor = db.cursor(pymysql.cursors.DictCursor)

            query = """
                SELECT 
                    v.id AS viaje_id,
                    v.punto_partida,
                    v.destino,
                    v.lat_partida,
                    v.lng_partida,
                    v.lat_destino,
                    v.lng_destino,
                    v.fecha_hora_salida,
                    v.asientos_ofertados,
                    v.asientos_disponibles,
                    v.restricciones,
                    e.nombre AS estado,
                    veh.id AS vehiculo_id,
                    veh.marca,
                    veh.modelo,
                    veh.placa,
                    veh.color,
                    (
                        SELECT JSON_ARRAYAGG(
                            JSON_OBJECT('id', u.id, 'foto_perfil', COALESCE(u.foto, 'default'))
                        )
                        FROM reserva_viaje rv
                        JOIN reserva r ON rv.reserva_id = r.id
                        JOIN usuario u ON r.pasajero_id = u.id
                        WHERE rv.viaje_id = v.id AND rv.estado_id = 14
                    ) AS pasajeros_reservados
                FROM viaje v
                JOIN vehiculo veh ON v.vehiculo_id = veh.id
                JOIN estado e ON v.estado_id = e.id
                WHERE 1=1
            """

            params = []
            
            # Filtro por campo de búsqueda
            campo_busqueda = filtros.get("campo_busqueda")
            texto_busqueda = filtros.get("texto_busqueda")

            if campo_busqueda and texto_busqueda:
                if campo_busqueda in ["punto_partida", "destino"]:
                    query += f" AND LOWER(v.{campo_busqueda}) LIKE %s"
                    params.append(f"%{texto_busqueda.lower()}%")

            # Filtro por asientos disponibles
            if str(filtros.get("asientos_disponibles")).lower() in ["true", "1"]:
                query += " AND v.asientos_disponibles > 0"

            # Filtro por restricciones
            if str(filtros.get("sin_restricciones")).lower() in ["true", "1"]:
                query += " AND (v.restricciones IS NULL OR TRIM(v.restricciones) = '' OR LOWER(TRIM(v.restricciones)) IN ('ninguna', 'sin restricciones'))"

            # Filtro por fecha desde
            # La fecha_hora_salida está en formato DD-MM-YYYY HH:MM:SS (string)
            if filtros.get("desde"):
                try:
                    desde = datetime.strptime(filtros["desde"], "%Y-%m-%d").strftime("%Y-%m-%d")
                    query += " AND DATE(STR_TO_DATE(v.fecha_hora_salida, '%%d-%%m-%%Y %%H:%%i:%%s')) >= STR_TO_DATE(%s, '%%Y-%%m-%%d')"
                    params.append(desde)
                except ValueError:
                    pass

            # Filtro por fecha hasta
            # La fecha_hora_salida está en formato DD-MM-YYYY HH:MM:SS (string)
            if filtros.get("hasta"):
                try:
                    hasta = datetime.strptime(filtros["hasta"], "%Y-%m-%d").strftime("%Y-%m-%d")
                    query += " AND DATE(STR_TO_DATE(v.fecha_hora_salida, '%%d-%%m-%%Y %%H:%%i:%%s')) <= STR_TO_DATE(%s, '%%Y-%%m-%%d')"
                    params.append(hasta)
                except ValueError:
                    pass

            # Solo mostrar viajes activos
            query += " AND v.estado_id = 1"

            # Ordenar por fecha de salida
            query += " ORDER BY v.fecha_hora_salida ASC"
            
            cursor.execute(query, params)
            viajes = cursor.fetchall()

            cursor.close()
            db.close()

            resultado = {"data": []}

            for v in viajes:
                # Manejar el campo JSON de pasajeros reservados
                pasajeros_lista = []
                if v.get("pasajeros_reservados"):
                    try:
                        # pymysql devuelve el JSON como un string, lo convertimos a lista
                        if isinstance(v["pasajeros_reservados"], str):
                            pasajeros_lista = json.loads(v["pasajeros_reservados"])
                        elif isinstance(v["pasajeros_reservados"], list):
                            pasajeros_lista = v["pasajeros_reservados"]
                    except (json.JSONDecodeError, TypeError):
                        pasajeros_lista = []

                # Formatear fecha_hora_salida a formato DD-MM-YYYY HH:MM:SS (como lo espera la app móvil)
                fecha_hora_str = ""
                if v["fecha_hora_salida"]:
                    try:
                        if isinstance(v["fecha_hora_salida"], str):
                            # Si ya está en formato DD-MM-YYYY HH:MM:SS, mantenerlo
                            if ' ' in v["fecha_hora_salida"]:
                                fecha_part = v["fecha_hora_salida"].split()[0]
                                hora_str = v["fecha_hora_salida"].split()[1] if len(v["fecha_hora_salida"].split()) > 1 else "00:00:00"
                                # Intentar parsear como DD-MM-YYYY primero (formato de BD)
                                try:
                                    fecha_obj = datetime.strptime(fecha_part, "%d-%m-%Y")
                                    fecha_hora_str = fecha_obj.strftime("%d-%m-%Y") + " " + hora_str
                                except:
                                    # Si falla, intentar como YYYY-MM-DD
                                    try:
                                        fecha_obj = datetime.strptime(fecha_part, "%Y-%m-%d")
                                        fecha_hora_str = fecha_obj.strftime("%d-%m-%Y") + " " + hora_str
                                    except:
                                        fecha_hora_str = v["fecha_hora_salida"]
                            else:
                                # Solo fecha, sin hora
                                try:
                                    fecha_obj = datetime.strptime(v["fecha_hora_salida"], "%d-%m-%Y")
                                    fecha_hora_str = fecha_obj.strftime("%d-%m-%Y") + " 00:00:00"
                                except:
                                    try:
                                        fecha_obj = datetime.strptime(v["fecha_hora_salida"], "%Y-%m-%d")
                                        fecha_hora_str = fecha_obj.strftime("%d-%m-%Y") + " 00:00:00"
                                    except:
                                        fecha_hora_str = v["fecha_hora_salida"] + " 00:00:00"
                        else:
                            # Si es datetime, formatear a DD-MM-YYYY HH:MM:SS
                            fecha_hora_str = v["fecha_hora_salida"].strftime("%d-%m-%Y %H:%M:%S")
                    except:
                        fecha_hora_str = str(v["fecha_hora_salida"]) if v["fecha_hora_salida"] else ""

                viaje = {
                    "viaje_id": v["viaje_id"],
                    "destino": v["destino"],
                    "punto_partida": v["punto_partida"],
                    "lat_partida": v["lat_partida"],
                    "lng_partida": v["lng_partida"],
                    "lat_destino": v["lat_destino"],
                    "lng_destino": v["lng_destino"],
                    "fecha_hora_salida": fecha_hora_str,
                    "asientos_ofertados": v["asientos_ofertados"],
                    "asientos_disponibles": v["asientos_disponibles"],
                    "restricciones": v["restricciones"],
                    "estado": v["estado"],
                    "vehiculo": {
                        "id": v["vehiculo_id"],
                        "marca": v["marca"],
                        "modelo": v["modelo"],
                        "placa": v["placa"],
                        "color": v["color"]
                    },
                    "pasajeros_reservados": pasajeros_lista
                }
                resultado["data"].append(viaje)

            return resultado
        except Exception as e:
            if 'db' in locals():
                if 'cursor' in locals():
                    cursor.close()
                db.close()
            return {"data": [], "error": str(e)}

    def listar_viajes_con_usuarios(self):
        """
        Lista todos los viajes activos con los usuarios que han reservado cada viaje.
        Retorna (True, lista_viajes) o (False, mensaje_error).
        """
        try:
            from datetime import datetime
            con = Conexion().open
            cursor = con.cursor()

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

            viajes_dict = {}

            for row in resultados:
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

                if viaje_id not in viajes_dict:
                    fecha_hora_str = ""
                    if fecha_hora_salida:
                        try:
                            if isinstance(fecha_hora_salida, str):
                                if ' ' in fecha_hora_salida:
                                    fecha_part = fecha_hora_salida.split()[0]
                                    hora_str = fecha_hora_salida.split()[1] if len(fecha_hora_salida.split()) > 1 else "00:00:00"
                                    try:
                                        fecha_obj = datetime.strptime(fecha_part, "%d-%m-%Y")
                                        fecha_hora_str = fecha_obj.strftime("%Y-%m-%d") + " " + hora_str
                                    except:
                                        try:
                                            fecha_obj = datetime.strptime(fecha_part, "%Y-%m-%d")
                                            fecha_hora_str = fecha_obj.strftime("%Y-%m-%d") + " " + hora_str
                                        except:
                                            fecha_hora_str = fecha_hora_salida
                                else:
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
                                fecha_hora_str = fecha_hora_salida.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            fecha_hora_str = str(fecha_hora_salida) if fecha_hora_salida else ""

                    viajes_dict[viaje_id] = {
                        "id": viaje_id,
                        "destino": destino,
                        "fecha_hora": fecha_hora_str,
                        "usuariosReservados": []
                    }

                if usuario_id and nombre_completo:
                    usuario = {
                        "id": int(usuario_id),
                        "nombre": nombre_completo.upper() if nombre_completo else "",
                        "foto": foto
                    }
                    usuarios_existentes = viajes_dict[viaje_id]["usuariosReservados"]
                    if not any(u["id"] == usuario["id"] for u in usuarios_existentes):
                        usuarios_existentes.append(usuario)

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

    def obtener_viaje_con_usuarios(self, viaje_id):
        """
        Obtiene un viaje específico con los usuarios que han reservado ese viaje
        
        Args:
            viaje_id: ID del viaje a obtener
        
        Returns:
            tuple: (True, viaje_data) si es exitoso, (False, mensaje_error) si hay error
        """
        try:
            from datetime import datetime
            
            con = Conexion().open
            cursor = con.cursor()
            
            # Consulta SQL para obtener un viaje específico con sus usuarios reservados
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
                WHERE v.id = %s
                AND v.estado_id = 1
                AND (rv.estado_id IS NULL OR rv.estado_id NOT IN (18, 15))
                ORDER BY u.id
            """
            
            cursor.execute(sql, [viaje_id])
            resultados = cursor.fetchall()
            
            # Verificar si el viaje existe
            if not resultados:
                cursor.close()
                con.close()
                return False, f'No se encontró el viaje con ID {viaje_id}'
            
            # Inicializar el diccionario del viaje
            viaje_data = None
            
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
                
                # Si el viaje no se ha inicializado, crearlo
                if viaje_data is None:
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
                    
                    viaje_data = {
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
                    if not any(u["id"] == usuario["id"] for u in viaje_data["usuariosReservados"]):
                        viaje_data["usuariosReservados"].append(usuario)
            
            cursor.close()
            con.close()
            
            return True, viaje_data
            
        except Exception as e:
            if 'con' in locals():
                if 'cursor' in locals():
                    cursor.close()
                con.close()
            return False, f'Error al listar viajes con usuarios: {str(e)}'
