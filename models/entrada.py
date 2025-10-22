from conexionBD import Conexion

class Entrada:
    def __init__(self):
        pass

    def comprar(self, usuario_id, evento_id, tipo_entrada_id, cantidad, metodo_pago):
        con = None
        cursor = None

        try:
            con = Conexion().open
            cursor = con.cursor()

            #  Validar cantidad
            try:
                cantidad = int(cantidad)
                if cantidad <= 0:
                    return False, " La cantidad debe ser mayor que 0."
            except Exception:
                return False, """ La cantidad debe ser un número válido."""

            # Buscar tipo de entrada y capacidad disponible
            sql_validar = """
            SELECT te.id, te.capacidad
            FROM tipoEntrada te
            INNER JOIN evento_tipo_entrada ete ON te.id = ete.tipo_entrada_id
            WHERE ete.evento_id = %s AND te.id = %s
            """
            cursor.execute(sql_validar, [evento_id, tipo_entrada_id])
            resultado = cursor.fetchone()

            print(f" DEBUG resultado SQL -> {resultado}")

            if not resultado:
                return False, f" No se encontró relación entre el evento {evento_id} y el tipo de entrada {tipo_entrada_id}."

            # Soportar tanto dict como tupla
            if isinstance(resultado, dict):
                tipo_id = resultado.get("id")
                capacidad_disponible = resultado.get("capacidad")
            else:
                tipo_id = resultado[0]
                capacidad_disponible = resultado[1]

            # Convertir capacidad a número
            try:
                capacidad_disponible = int(float(capacidad_disponible))
            except Exception:
                return False, f" Capacidad inválida en BD: {capacidad_disponible}"

            print(f" DEBUG capacidad_disponible={capacidad_disponible}, cantidad={cantidad}")

            #  Validar disponibilidad
            if capacidad_disponible <= 0:
                return False, f"No hay boletos disponibles para este tipo de entrada."
            if cantidad > capacidad_disponible:
                return False, f" Solo hay {capacidad_disponible} boletos disponibles."

            # Registrar compra
            sql_compra = """
            INSERT INTO entrada (idTipoEntrada, cantidad, eventoid, metodoPago)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql_compra, [tipo_entrada_id, cantidad, evento_id, metodo_pago])

            # Descontar boletos
            sql_update = "UPDATE tipoEntrada SET capacidad = capacidad - %s WHERE id = %s"
            cursor.execute(sql_update, [cantidad, tipo_entrada_id])

            con.commit()

            boletos_restantes = capacidad_disponible - cantidad
            return True, f" Compra exitosa. Quedan {boletos_restantes} boletos."

        except Exception as e:
            if con:
                con.rollback()
            return False, f" Error al realizar la compra: {str(e)}"

        finally:
            if cursor:
                cursor.close()
            if con:
                con.close()