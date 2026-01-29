import re

def validar_email(email):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email)

def validar_telefono(telefono):
    return telefono.isdigit() and len(telefono) == 10

def validar_cedula(ci):
    return ci.isdigit() and len(ci) == 10