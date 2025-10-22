from conexionBD import Conexion
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

class Usuario:
    def __init__(self):
        self.ph = PasswordHasher()
        
    def login(self, email, clave):
        #Abrir la conexión
        con = Conexion().open
        
        #Crear un cursor para ejecutar la sentencia sql
        cursor = con.cursor()
        
        #Definir la sentencia sql
        sql = "select id, concat(nombres, ' ', apellido_paterno, ' ', apellido_materno) as nombre, email, clave from usuario where email = %s"
        
        #Ejecutar la sentencia
        cursor.execute(sql,[email])
        
        #Recuperar los datos del usuario
        resultado = cursor.fetchone()
        
        #Cerrar el curso y la conexión
        cursor.close()
        con.close()
        
        if resultado: #Verificando si se encontró al usuario con el email ingresado
            try:
                self.ph.verify(resultado['clave'], clave) #Verificando la clave almacenada en la BD con la clave que ingresó el usuario
                return resultado
            except VerifyMismatchError:
                return None
            
        else: #No se ha encontrado al usuario con el email ingreso
            return None
        
    def obtener_foto(self, id):
        #Abrir la conexión
        con = Conexion().open
        
        #Crear un cursor para ejecutar la sentencia sql
        cursor = con.cursor()
        
        #Definir la sentencia sql
        sql = "select coalesce(foto, 'x') as foto from usuario where id=%s"
        
        #Ejecutar la sentencia
        cursor.execute(sql,[id])
        
        #Recuperar los datos del usuario
        resultado = cursor.fetchone()
        
        #Cerrar el curso y la conexión
        cursor.close()
        con.close()
        
        if resultado and resultado['foto'] != 'x':
            return resultado #devolver el nombre del archivo que contiene la foto
        
        #Si no hay foto devolver none
        return None
    
    def registrar(self, apellido_paterno, apellido_materno, nombres, dni, telefono, email, clave):
        #Abrir la conexión
        con = Conexion().open
        
        #Crear un cursor para ejecutar la sentencia sql
        cursor = con.cursor()
        
        #Definir la sentencia sql para validar el dni e email
        sql = "SELECT 1 AS cantidad FROM usuario WHERE dni=%s OR email=%s"
        
        #Ejecutar la sentencia
        cursor.execute(sql,[dni, email])
        
        #Recuperar los datos del usuario
        resultado = cursor.fetchone()
        
        #Validar dni o email duplicado
        if resultado:
            return False, 'El DNI o email ingresado ya se encuentra registrado por otro usuario'
        
        #Definir la sentencia sql
        sql = """
            INSERT INTO usuario (apellido_paterno, apellido_materno, nombres, dni, telefono, email, estado_id, clave) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        
        #Ejecutar la sentencia
        cursor.execute(sql,[apellido_paterno, apellido_materno, nombres, dni, telefono, email, '1', self.ph.hash(clave)])
        
        #Confirmar los datos en la BD
        con.commit()
        
        #Cerrar el curso y la conexión
        cursor.close()
        con.close()
        
        #Retonar al final true
        return True, 'ok'
        
    def actualizar(self, apellido_paterno, apellido_materno, nombres, dni, telefono, email, id):
        #Abrir la conexión
        con = Conexion().open
        
        #Crear un cursor para ejecutar la sentencia sql
        cursor = con.cursor()
        
        #Definir la sentencia sql
        sql = """
            UPDATE 
                usuario 
            set 
                apellido_paterno = %s,
                apellido_materno = %s, 
                nombres = %s, 
                dni = %s, 
                telefono = %s, 
                email = %s,
                fecha_modificacion = NOW()
            where
                id = %s
        """
        
        #Ejecutar la sentencia
        cursor.execute(sql,[apellido_paterno, apellido_materno, nombres, dni, telefono, email, id])
        
        #Confirmar los datos en la BD
        con.commit()
        
        #Cerrar el curso y la conexión
        cursor.close()
        con.close()
        
        #Retonar al final true
        return True, 'ok'
        
    def dar_baja(self, id):
        #Abrir la conexión
        con = Conexion().open
        
        #Crear un cursor para ejecutar la sentencia sql
        cursor = con.cursor()
        
        #Definir la sentencia sql
        sql = """
            UPDATE 
                usuario 
            set 
                estado_id = 2,
                fecha_modificacion = NOW()
            where
                id = %s
        """
        
        #Ejecutar la sentencia
        cursor.execute(sql,[id])
        
        #Confirmar los datos en la BD
        con.commit()
        
        #Cerrar el curso y la conexión
        cursor.close()
        con.close()
        
        #Retonar al final true
        return True, 'ok'
    
    def actualizar_foto(self, foto, id):
        #Abrir la conexión
        con = Conexion().open
        
        #Crear un cursor para ejecutar la sentencia sql
        cursor = con.cursor()
        
        #Definir la sentencia sql
        sql = """
            UPDATE 
                usuario 
            set 
                foto = %s,
                fecha_modificacion = NOW()
            where
                id = %s
        """
        
        #Ejecutar la sentencia
        cursor.execute(sql,[foto, id])
        
        #Confirmar los datos en la BD
        con.commit()
        
        #Cerrar el curso y la conexión
        cursor.close()
        con.close()
        
        #Retonar al final true
        return True, 'ok'
    
    def actualizar_clave(self, clave_actual, clave_nueva, id):
        #Abrir la conexión
        con = Conexion().open
        
        #Crear un cursor para ejecutar la sentencia sql
        cursor = con.cursor()
        
        #Definir la sentencia sql para validar el dni e email
        sql = "SELECT clave FROM usuario WHERE id=%s"
        
        #Ejecutar la sentencia
        cursor.execute(sql,[id])
        
        #Recuperar los datos del usuario
        resultado = cursor.fetchone()
        
        #Validar que la clave sea correcta
        try:
            self.ph.verify(resultado['clave'], clave_actual)    
        except VerifyMismatchError:
            return False, 'La clave actual es incorrecta, verifique'
        
        #Definir la sentencia sql
        sql = """
            UPDATE 
                usuario 
            set 
                clave = %s,
                fecha_modificacion = NOW()
            where
                id = %s
        """
        
        #Ejecutar la sentencia
        cursor.execute(sql,[ self.ph.hash(clave_nueva), id])
        
        #Confirmar los datos en la BD
        con.commit()
        
        #Cerrar el curso y la conexión
        cursor.close()
        con.close()
        
        #Retonar al final true
        return True, 'ok'