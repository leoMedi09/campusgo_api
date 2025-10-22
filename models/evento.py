from conexionBD import Conexion
from datetime import datetime
import logging

logging.basicConfig(level=logging.DEBUG)

class Evento:
    def registrar(self, titulo, descripcion, fechaInicio, fechaFin, lugar, tipos_entrada):
        con = None
        cursor = None

        try:
            con = Conexion().open
            cursor = con.cursor()

            # Insertar el evento principal
            sql_evento = """
            INSERT INTO evento (titulo, descripcion, fechaInicio, fechaFin, lugar, estado_id)
            VALUES (%s, %s, %s, %s, %s, 1)
            """
            cursor.execute(sql_evento, [titulo, descripcion, fechaInicio, fechaFin, lugar])
            evento_id = cursor.lastrowid

            # Insertar los tipos de entrada y asociarlos
            sql_insert_tipo = """
            INSERT INTO tipoEntrada (nombre, precio, capacidad, limitePersona)
            VALUES (%s, %s, %s, %s)
            """

            sql_asociar = """
            INSERT INTO evento_tipo_entrada (evento_id, tipo_entrada_id)
            VALUES (%s, %s)
            """

            for tipo in tipos_entrada:
                cursor.execute(sql_insert_tipo, [
                    tipo["nombre_tipo"],
                    tipo["precio"],
                    tipo["capacidad_total"],
                    tipo["limite_por_persona"]
                ])
                tipo_id = cursor.lastrowid
                cursor.execute(sql_asociar, [evento_id, tipo_id])

            # Confirmar transacción
            con.commit()
            return True, "Evento y tipos de entrada creados exitosamente."

        except Exception as e:
            if con:
                con.rollback()
            return False, f"Error al crear evento: {str(e)}"

        finally:
            if cursor:
                cursor.close()
            if con:
                con.close()


    @staticmethod
    def consultar():
        try:
            # Aquí va la lógica de la consulta, como antes
            con = Conexion().open
            cursor = con.cursor()

            sqlConsulta = """
            SELECT 
                id, 
                titulo, 
                descripcion, 
                fechaInicio, 
                fechaFin, 
                lugar
            FROM evento
            WHERE estado_id = 1;  
            """

            cursor.execute(sqlConsulta)
            registros = cursor.fetchall()

            if registros:
                return True, registros
            else:
                return False, []

        except Exception as e:
            print(f"Error: {str(e)}")
            return False, []
        
    
