from flask import Blueprint, request, jsonify, send_from_directory
from models.usuario import Usuario
from tools.jwt_utils import generar_token
from tools.jwt_required import jwt_token_requerido
from tools.security import password_validate
import os
from werkzeug.utils import secure_filename

#Crear un modulo blueprint para implementar el servicio web de usuario (login, cambiar clave, registrar, etc)
ws_usuario = Blueprint('ws_usuario', __name__)

#Instanciar a la clase usuario
usuario = Usuario()

#Crear un endpoint para permitir al usuario iniciar sesión(login)
@ws_usuario.route('/login', methods=['POST'])
def login():
    #Obtener los datos que se envian como parámetros de entrada
    data = request.get_json()
    
    #pasar los datos de email y clave a variables
    email = data.get('email')
    clave = data.get('clave')
    
    #Validar si contamos con los parámetros de email y clave
    if not all([email, clave]):
        return jsonify({'status': False, 'data': None, 'message': 'Faltan datos obligatorios'}), 400
    
    try:
        #Llamar al método login
        resultado = usuario.login(email, clave)
        
        if resultado: #Si hay resultado
            #retirar la clave del resultado antes de imprimir
            resultado.pop('clave', None)
            
            #Generar el token con JWT
            token = generar_token({'usuario_id': resultado['id']}, 60*60)
            
            #Incliuir en el resultado el token generado
            resultado['token'] = token
            
            #Imprimir el resultado
            return jsonify({'status': True, 'data': resultado, 'message':'Inicio de sesión satisfactorio'}), 200
        
        else:
            return jsonify({'status': False, 'data': None, 'message': 'Credenciales incorrectas'}), 401
            
    except Exception as e:
        return jsonify({'status': False, 'data': None, 'message': str(e)}), 500


#Crear un endpoint para obtener la foto del usuario mediante su id
@ws_usuario.route('/usuario/foto/<id>', methods=['GET'])
@jwt_token_requerido
def obtener_foto(id):
    #Validar si se cuenta con el ID para mostrar la foto
    if not all([id]):
        return jsonify({'status': False, 'data': None, 'message': 'Faltan datos obligatorios'}), 400
    
    try:
        resultado = usuario.obtener_foto(id)
        if resultado:
            return send_from_directory('uploads/fotos/usuarios', resultado['foto'])
        else:
            return send_from_directory('uploads/fotos/usuarios', 'default.png')
    except Exception as e:
        return jsonify({'status': False, 'data': None, 'message': str(e)}), 500


#Crear un endpoint para registrar nuevos usuarios
@ws_usuario.route('/usuario/registrar', methods=['POST'])
def registrar():
    #Obtener los datos que se envian como parámetros de entrada
    data = request.get_json()
    
    #pasar los datos a variables
    #apellido_paterno, apellido_materno, nombres, dni, telefono, email, clave
    apellido_paterno = data.get('apellido_paterno')
    apellido_materno = data.get('apellido_materno')
    nombres = data.get('nombres')
    dni = data.get('dni')
    telefono = data.get('telefono')
    email = data.get('email')
    clave = data.get('clave')
    clave_confirmada = data.get('clave_confirmada')
    
    #Validar si contamos con los parámetros de email y clave
    if not all([apellido_paterno, apellido_materno, nombres, dni, telefono, email, clave, clave_confirmada]):
        return jsonify({'status': False, 'data': None, 'message': 'Faltan datos obligatorios'}), 400
    
    #Validar que las claves coincidan
    if clave != clave_confirmada:
        return jsonify({'status': False, 'data': None, 'message': 'Las claves ingresadas no coinciden'}), 500
    
    #Validar la complejidad de la clave
    valida, mensaje = password_validate(clave)
    if not valida:
        return jsonify({'status': False, 'data': None, 'message': mensaje}), 500
    
    #Registrar al usuario
    try:
        resultado, mensaje = usuario.registrar(apellido_paterno, apellido_materno, nombres, dni, telefono, email, clave)
        if resultado:
            return jsonify({'status': True, 'data': None, 'message': 'Usuario registrado'}), 200
        else:
            return jsonify({'status': False, 'data': None, 'message': mensaje}), 500
    except Exception as e:
        return jsonify({'status': False, 'data': None, 'message': str(e)}), 500


#Crear un endpoint para registrar nuevos usuarios
@ws_usuario.route('/usuario/actualizar', methods=['PUT'])
@jwt_token_requerido
def actualizar():
    #Obtener los datos que se envian como parámetros de entrada
    data = request.get_json()
    
    #pasar los datos a variables
    #apellido_paterno, apellido_materno, nombres, dni, telefono, email, id
    apellido_paterno = data.get('apellido_paterno')
    apellido_materno = data.get('apellido_materno')
    nombres = data.get('nombres')
    dni = data.get('dni')
    telefono = data.get('telefono')
    email = data.get('email')
    id = data.get('id')
    
    #Validar si contamos con los parámetros de email y clave
    if not all([apellido_paterno, apellido_materno, nombres, dni, telefono, email, id]):
        return jsonify({'status': False, 'data': None, 'message': 'Faltan datos obligatorios'}), 400
    
    #Actualizar los datos del usuario
    try:
        resultado, mensaje = usuario.actualizar(apellido_paterno, apellido_materno, nombres, dni, telefono, email, id)
        if resultado:
            return jsonify({'status': True, 'data': None, 'message': 'Datos del usuario actualizados'}), 200
        else:
            return jsonify({'status': False, 'data': None, 'message': mensaje}), 500
    except Exception as e:
        return jsonify({'status': False, 'data': None, 'message': str(e)}), 500
    
    
    
    #Crear un endpoint para registrar nuevos usuarios


@ws_usuario.route('/usuario/baja', methods=['DELETE'])
@jwt_token_requerido
def baja():
    #Obtener los datos que se envian como parámetros de entrada
    data = request.get_json()
    
    #pasar los datos a variables
    #id
    id = data.get('id')
    
    #Validar si contamos con los parámetros de email y clave
    if not all([id]):
        return jsonify({'status': False, 'data': None, 'message': 'Faltan datos obligatorios'}), 400
    
    #Actualizar los datos del usuario
    try:
        resultado, mensaje = usuario.dar_baja(id)
        if resultado:
            return jsonify({'status': True, 'data': None, 'message': 'Se ha registrado la baja del usuario'}), 200
        else:
            return jsonify({'status': False, 'data': None, 'message': mensaje}), 500
    except Exception as e:
        return jsonify({'status': False, 'data': None, 'message': str(e)}), 500
    
    
@ws_usuario.route('/usuario/actualizar/foto', methods=['PUT'])
@jwt_token_requerido
def actualizar_foto():
    #pasar los datos a variables
    #id, foto
    id = request.form.get('id')
    foto = request.files.get('foto')
    
    #Validar si contamos con los parámetros de email y clave
    if not all([id, foto]):
        return jsonify({'status': False, 'data': None, 'message': 'Faltan datos obligatorios'}), 400
    
    #Actualizar la foto del usuario
    try:
        #Cargar la foto del usuario al servidor (storage)
        nombre_foto = None
        
        if foto:
            extension = os.path.splitext(foto.filename)[1] #obtiene: ".jpg", ".png", ".gif"
            nombre_foto = secure_filename(f"{id}{extension}") #obtiene: "3.jpg", "3.png"
            ruta_foto = os.path.join("uploads", "fotos", "usuarios", nombre_foto)
            foto.save(ruta_foto)
        
            resultado, mensaje = usuario.actualizar_foto(nombre_foto, id)
            if resultado:
                return jsonify({'status': True, 'data': None, 'message': 'Se ha actualizado la foto del usuario'}), 200
            else:
                return jsonify({'status': False, 'data': None, 'message': mensaje}), 500
        else:
            return jsonify({'status': False, 'data': None, 'message': "La fotografía que intenta cargar no es válida"}), 500
        
    except Exception as e:
        return jsonify({'status': False, 'data': None, 'message': str(e)}), 500
    

#Crear un endpoint para registrar nuevos usuarios
@ws_usuario.route('/usuario/actualizar/clave', methods=['PUT'])
def actualizar_clave():
    #Obtener los datos que se envian como parámetros de entrada
    data = request.get_json()
    
    #pasar los datos a variables
    #clave_actual, clave_nueva, clave_nueva_confirmada
    clave_actual = data.get('clave_actual')
    clave_nueva = data.get('clave_nueva')
    clave_nueva_confirmada = data.get('clave_nueva_confirmada')
    id = data.get('id')
    
    #Validar si contamos con los parámetros requeridos
    if not all([clave_actual, clave_nueva, clave_nueva_confirmada, id]):
        return jsonify({'status': False, 'data': None, 'message': 'Faltan datos obligatorios'}), 400
    
    #Validar que las nuevas claves coincidan
    if clave_nueva == clave_actual:
        return jsonify({'status': False, 'data': None, 'message': 'No es posible actualizar por la misma clave'}), 500
    
    #Validar que las nuevas claves coincidan
    if clave_nueva != clave_nueva_confirmada:
        return jsonify({'status': False, 'data': None, 'message': 'Las nuevas claves ingresadas no coinciden'}), 500
    
    #Validar la complejidad de la clave
    valida, mensaje = password_validate(clave_nueva)
    if not valida:
        return jsonify({'status': False, 'data': None, 'message': mensaje}), 500
    
    #Registrar al usuario
    try:
        resultado, mensaje = usuario.actualizar_clave(clave_actual, clave_nueva, id)
        if resultado:
            return jsonify({'status': True, 'data': None, 'message': 'Su clave ha sido actualizada correctamenete'}), 200
        else:
            return jsonify({'status': False, 'data': None, 'message': mensaje}), 500
    except Exception as e:
        return jsonify({'status': False, 'data': None, 'message': str(e)}), 500
