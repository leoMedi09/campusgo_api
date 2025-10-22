from conexionBD import Conexion

class Vehiculo:
       
    def registrar(self, conductor_id, marca, modelo, placa, color, pasajeros):
        #Abrir la conexión
        con = Conexion().open
        
        #Crear un cursor para ejecutar la sentencia sql
        cursor = con.cursor()
        
        #Definir la sentencia sql para validar el vehiculo por placa
        sql = "SELECT 1 AS cantidad FROM vehiculo WHERE placa=%s"
        
        #Ejecutar la sentencia
        cursor.execute(sql,[placa])
        
        #Recuperar los datos del usuario
        resultado = cursor.fetchone()
        
        #Validar por placa
        if resultado:
            return False, 'La placa que intenta registrar ya se encuentra registrada'
        
        #Definir la sentencia sql
        sql = """
            INSERT INTO vehiculo (conductor_id, marca, modelo, placa, color, pasajeros, estado_id) 
            VALUES (%s, %s, %s, %s, %s, %s, 1);
        """
        
        #Ejecutar la sentencia
        cursor.execute(sql,[conductor_id, marca, modelo, placa, color, pasajeros])
        
        #Confirmar los datos en la BD
        con.commit()
        
        #Cerrar el curso y la conexión
        cursor.close()
        con.close()
        
        #Retonar al final true
        return True, 'ok'
        