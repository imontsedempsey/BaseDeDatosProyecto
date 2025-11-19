import re

def validar_correo(correo: str) -> bool:
    """
    Valida el formato básico de un correo.
    Ej: nombre.apellido@gmail.com
    """
    if correo is None:
        return False
    correo = correo.strip()
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, correo) is not None


def validar_rut(rut_raw: str) -> bool:
    """
    Valida el RUT chileno.
    Acepta formatos:
    - '12.345.678-5'
    - '12345678-5'
    - '123456785'
    - '9.876.543-K'
    """
    try:
        if rut_raw is None:
            return False

        # 1. limpiar: sacar puntos y guion, mayúscula
        rut = rut_raw.replace(".", "").replace("-", "").strip().upper()

        # ahora rut debe ser [cuerpo][DV]
        # cuerpo = todos menos el último
        # DV = último (0-9 o K)
        if len(rut) < 8 or len(rut) > 9:
            # mínimo 7 dígitos + DV = 8 chars
            # máximo 8 dígitos + DV = 9 chars
            return False

        cuerpo = rut[:-1]
        dv_ingresado = rut[-1]

        # cuerpo tiene que ser numérico
        if not cuerpo.isdigit():
            return False

        # 2. calcular dígito verificador esperado con el algoritmo oficial
        suma = 0
        mult = 2
        # recorrer el cuerpo de derecha a izquierda
        for c in reversed(cuerpo):
            suma += int(c) * mult
            mult = 2 if mult == 7 else mult + 1

        resto = suma % 11
        dv_calc_num = 11 - resto

        if dv_calc_num == 11:
            dv_esperado = "0"
        elif dv_calc_num == 10:
            dv_esperado = "K"
        else:
            dv_esperado = str(dv_calc_num)

        # 3. comparar DV ingresado vs DV esperado
        return dv_ingresado == dv_esperado

    except Exception:
        return False


