from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Obtiene un valor de un diccionario usando una clave.
    Ejemplo de uso: {{ diccionario|get_item:clave }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key, [])  # Devuelve una lista vacía si la clave no existe
