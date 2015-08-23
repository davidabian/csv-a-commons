# -*- coding: utf-8 -*-
#
#    Módulo modificable de configuración para la subida masiva de
#    ficheros multimedia a Wikimedia Commons con información asociada en
#    un archivo de CSV.
#
#   Copyright (C) 2015, David Abián <da [at] davidabian.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import csvac

########################################################################
##       REGLAS DE VERIFICACIÓN PARA LA PREVENCIÓN DE ERRORES         ##
########################################################################

def regex (campo):
    """Devuelve la expresión regular (regex) que debe seguir todo valor
    del campo [campo] para que dicho valor se considere aceptable.
    
    Si no se indica una expresión regular para algún campo o dicha
    expresión es la cadena vacía, cualquier valor se considerará
    aceptable.
    """
    dictReglas = {
        #
        #  Las reglas, una por línea, deben seguir el siguiente formato:
        #  "NOMBREDELCAMPO": "\A[Rr]egex[A-Z]$",
        #
        "NOMBREDELCAMPO": "\A[Rr]egex[A-Z]$",
    }
    if regla in dictReglas:
        return dictReglas[regla]
    else:
        return ""

########################################################################
##           DESCRIPCIÓN DE ARCHIVOS EN WIKIMEDIA COMMONS             ##
########################################################################

def descripcion (datos, fila):
    """Devuelve la descripción que se incluirá finalmente junto al
    archivo que subir a Wikimedia Commons tomando la información de la
    fila [fila] del conjunto de datos [datos].
    """
    return u"Descripción de prueba. {{testing with\n|1=%s\n|2=%s\n}}\nThat's all." \
           % csvac.valores(datos,fila,[\
                                    u"CAMPO1",\
                                    u"CAMPO2",\
                                   ])

########################################################################
##
########################################################################

def cte ():
    dictCte = {
        # Directorio donde se encuentran los ficheros que subir y el
        # fichero de CSV.
        "nombreDir": "/home/usuario/csv-commons/",
        
        # Nombre del fichero de CSV donde se recogen los ficheros para
        # subir y su información, ubicado en [dirarchivos].
        "nombreCsv": u"nombreDelArchivo.csv",
        
        # Nombre del campo del fichero de CSV que indica los nombres
        # originales de los ficheros que subir.
        "campoNombres0": "Nombre fichero local",
        
        # Nombre del campo del fichero de CSV que indica los nombres
        # que tomarán en Wikimedia Commons los ficheros para subir.
        "campoNombresC": "Nombre fichero en Commons",
        
        # Minutos transcurridos desde el inicio o la reanudación del
        # proceso de subida para sugerir un descanso al operador.
        "tDescanso": 30,
        
        # Segundos mínimos de espera entre una subida y la siguiente.
        "tEspera": 1,
        
        # Número de ficheros que subir en la tanda inicial.
        "tanda0": 5,
        
        # Número de subidas que deben ser aprobadas por el operador
        # en cada tanda. Número entero menor o igual que [tanda0].
        "aprobar": 3,
        
        # Constante multiplicativa que va incrementando el número de
        # ficheros que tratar en cada tanda.
        # Número real mayor o igual que 1.
        "crecimTanda": 1.5,
    }
    return dictCte
        
