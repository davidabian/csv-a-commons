#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    CSV a Commons
#
#    Programa para la subida masiva y controlada de ficheros multimedia
#    a Wikimedia Commons con información asociada en un archivo de CSV.
#    Hace uso del framework Pywikibot, que debe estar instalado en las
#    proximidades del propio programa.
#
#    TODO: Comprobar que los campos que reflejen la duración de las
#              posibles pistas de audio posean los valores correctos.
#    TODO: Ante la ausencia de constantes o de variables del entorno
#              que han de definirse en csvcfg, que el programa se las
#              apañe.
#    TODO: Al principio del programa, comprobar si la configuración de
#              csvcfg es coherente, y no continuar en caso contrario.
#    TODO: Detectar si la sesión se inicia correctamente con Pywikibot.
#              Véase T106580 <https://phabricator.wikimedia.org/T106580>.
#    TODO: Detectar si cada archivo se sube correctamente con Pywikibot.
#              Véase T106580 <https://phabricator.wikimedia.org/T106580>.
#    TODO: Aplicar -always a las subidas con upload.py para evitar
#              dobles confirmaciones por parte del operador y el enorme
#              malgasto de tiempo y esfuerzo, característica aún no
#              disponible.
#              Véase T106412 <https://phabricator.wikimedia.org/T106412>.
#    TODO: Usar hashes para comprobar la integridad de los ficheros.
#    TODO: Optimizar funciones y reducir sus costes en tiempo.
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

import csv
import getpass
import hashlib
import json
import os.path
import random
import re
import sys
import time
import urllib

import abilog
import csvcfg

#  La constante [INTERACTIVO] determina si un operador controlará todo
#  el proceso (True), por defecto, o bien si no se interactuará con
#  ningún operador durante la ejecución (False), solo para depuración y
#  casos aislados.
#
INTERACTIVO = True

#  La constante [SIMULACION] indica si el programa se ejecutará en modo
#  de pruebas (True), sin necesidad de disponer de una instalación de
#  Pywikibot y sin subir ningún fichero, o en el modo habitual (False),
#  destinado a subir ficheros a Wikimedia Commons.
#
SIMULACION = False

#  La variable [correoAyuda] alberga la dirección de correo electrónico
#  a la que el operador del programa deberá dirigirse en caso de que
#  algo salga mal o cuando necesite ayuda.
#  Se sustituye u" [at] " por u"@".
#
correoAyuda = u"da [at] davidabian.com"

correoAyuda = correoAyuda.replace(u" [at] ", u"@")

def comprobar_pwb():
    """Comprueba si Pywikibot core se encuentra instalado en las
    proximidades del directorio actual.
    
    Devuelve la ruta de dicha instalación si se encuentra, o bien None
    si no se encuentra, emitiendo un error en este último caso.
    """
    dirPosibles = [os.path.join(""),
                   os.path.join("..",""),
                   os.path.join("..","..",""),
                   os.path.join("core",""),
                   os.path.join("..","core",""),
                   os.path.join("..","..","core",""),
                   os.path.join("core","core",""),
                   os.path.join("..","core","core",""),
                   os.path.join("..","..","core","core",""),
                   os.path.join("Core",""),
                   os.path.join("..","Core",""),
                   os.path.join("..","..","Core",""),
                   os.path.join("rewrite",""),
                   os.path.join("..","rewrite",""),
                   os.path.join("..","..","rewrite",""),
                   os.path.join("pywikibot",""),
                   os.path.join("..","pywikibot",""),
                   os.path.join("..","..","pywikibot",""),
                   os.path.join("Pywikibot",""),
                   os.path.join("..","Pywikibot",""),
                   os.path.join("..","..","Pywikibot",""),
                   os.path.join("pywikibot","core",""),
                   os.path.join("..","pywikibot","core",""),
                   os.path.join("..","..","pywikibot","core",""),
                   os.path.join("Pywikibot","core",""),
                   os.path.join("..","Pywikibot","core",""),
                   os.path.join("..","..","Pywikibot","core",""),
                   os.path.join("pwb",""),
                   os.path.join("..","pwb",""),
                   os.path.join("..","..","pwb",""),
                   os.path.join("pywikipedia",""),
                   os.path.join("..","pywikipedia",""),
                   os.path.join("..","..","pywikipedia",""),
                   os.path.join("Pywikipedia",""),
                   os.path.join("..","Pywikipedia",""),
                   os.path.join("..","..","Pywikipedia",""),
                   os.path.join("Pywikipedia","core",""),
                   os.path.join("..","Pywikipedia","core",""),
                   os.path.join("..","..","Pywikipedia","core",""),
                   os.path.join("pywikipediabot",""),
                   os.path.join("..","pywikipediabot",""),
                   os.path.join("..","..","pywikipediabot",""),
                   os.path.join("Pywikipediabot",""),
                   os.path.join("..","Pywikipediabot",""),
                   os.path.join("..","..","Pywikipediabot",""),]
    directorio = None
    for dirPosible in dirPosibles:
        check1 = "{}pwb.py".format(dirPosible)
        check2 = "{}upload.py".format(os.path.join(dirPosible,
                                                   "scripts",
                                                   ""))
        if os.path.isfile(check1) and os.path.isfile(check2):
            directorio = dirPosible
            break
    if directorio == None:
        abilog.error(u"No se encuentra una instalación de Pywikibot "
                     u"core en las proximidades del directorio actual.")
    return directorio

dirpwb = comprobar_pwb()
if dirpwb:
    sys.path.append(dirpwb)
    import pwb
    sys.path.append("{}scripts".format(dirpwb))
    import upload
    import login

#### Hashes ############################################################

def sha1_f (f):
    """Devuelve el SHA-1 del fichero [f], o None en caso de error."""
    f = os.path.join(csvcfg.entorno("dirarchivos"), f)
    if not SIMULACION:
        with open(f, 'rb') as af:
            try:
                sha1 = hashlib.sha1(af.read()).hexdigest()
            except:
                sha1 = None
    else:
        sha1 = None
    return sha1

def log_hash (f):
    """Registra el hash SHA-1 del fichero [f] en el de depuración."""
    sha1 = sha1_f(f)
    if sha1:
        abilog.debug(u"{}: {}".format(f, sha1))
    else:
        abilog.debug(u"{}: ???".format(f))

#### Pywikibot #########################################################

def login_pwb ():
    """Inicia sesión en Wikimedia Commons con Pywikibot core."""
    #bot = raw_input("Nombre de usuario: ")
    if not SIMULACION:
        #login.main(u"-family:commons",
        #           u"-lang:commons")
        login.main(u"-family:test",
                   u"-lang:test")

def subir (nombrecsv, datos, f, fdestino, descr):
    """Trata de subir el fichero de nombre [f] a Wikimedia Commons con
    el nombre [fdestino] y la descripción [descr].
    """
    if not SIMULACION:
        upload.main(u'-family:test',
                    u'-lang:test',
        #upload.main(u'-family:commons',
        #            u'-lang:commons',
                    u'-noverify',
                    u'-abortonwarn',
                    u'-filename:{}'.format(fdestino),
                    os.path.join(csvcfg.entorno("dirarchivos"), f),
                    u'{}'.format(descr))
    return 0

#### CSV ###############################################################

def leer_csv (nombrecsv):
    """Lee el fichero de CSV de nombre [nombrecsv], decodifica su
    contenido usando UTF-8 y lo devuelve en forma de lista.
    
    La estructura de la lista devuelta es:
        [fila_1,fila_2,...,fila_i], donde
            fila_n es una lista de los elementos de la fila n;
            i es el número de columnas en el fichero de CSV.
    En caso de error, devuelve la lista vacía.
    """
    datos = []
    if os.path.isfile(os.path.join(csvcfg.entorno("dirarchivos"),
                                   nombrecsv)):
        abilog.info(u"Iniciando lectura del fichero «{}».".format(nombrecsv))
        with open("{}{}".format(csvcfg.entorno("dirarchivos"),
                                nombrecsv), 'rb') as f:
            reader = csv.reader(f)
            for fila in reader:
                for i in range(len(fila)):
                    fila[i] = fila[i].decode('utf-8')
                datos.append(fila)
    else:
        abilog.error(u"No se encuentra el fichero «{}». "
                     u"Es posible que no exista o que no sea "
                     u"legible.".format(nombrecsv))
    return datos

#### Base ##############################################################

def print_datos (datos):
    for fila in datos:
        for elemento in fila:
            print elemento

def nombre_num_campo (datos, nombreCampo):
    """Devuelve el número de orden del campo de nombre [nombreCampo] del
    conjunto de datos [datos], o bien None si no existe un campo con tal
    nombre.
    
    Se hace distinción entre mayúsculas y minúsculas.
    El número de orden del primer campo es 0.
    """
    campos = datos[0]
    numCampo = None
    if nombreCampo in campos:
        numCampo = campos.index(nombreCampo)
    return numCampo
    
def valores (datos, fila, nombreCampos):
    """Devuelve los valores de los campos de nombre [nombreCampos] de la
    fila [fila] del conjunto de datos [datos].
    
    Si hay algún error, devuelve None.
    """
    valores = []
    for nombreCampo in nombreCampos:
        numCampo = nombre_num_campo(datos,nombreCampo)
        if numCampo == None:
            abilog.error(u"No existe el campo de nombre «{}» en "
                         u"el fichero de CSV.".format(nombreCampo))
            return None
        else:
            valores.append(datos[fila][numCampo])
    return tuple(valores)

#### Ficheros ##########################################################

def copia_seguridad (nombrefichero):
    """Crea una copia de seguridad del fichero de nombre [nombrefichero]
    con la fecha y la hora actuales.
    
    Devuelve None si todo va bien.
    """
    if os.path.isfile(nombrefichero):
        fi = open(u"{}".format(nombrefichero), 'r')
        contenido = fi.read()
        fi.close()
        fo = open(u"{}.{}".format(nombrefichero,
                                  time.strftime("%Y%m%d%H%M%S")), 'w')
        fo.write(contenido)
        fo.close()
    else:
        return (u"No se encuentra el fichero «{}». "
                u"Es posible que no exista o que no sea "
                u"legible.".format(nombrecsv))
    return None

def guardar_fila (nombrecsv, ifila):
    """Guarda [ifila] como contenido del fichero de texto
    [nombrecsv].NOBORRAR.ifila, ubicado en
    [csvcfg.entorno("dirarchivos")].
    """
    f = open(u"{}{}.NOBORRAR.ifila".format(csvcfg.entorno("dirarchivos"),
                                           nombrecsv), 'w')
    f.write(str(ifila))
    f.close()

def cargar_fila (nombrecsv):
    """Carga el contenido del fichero de texto
    [nombrecsv].NOBORRAR.ifila y lo devuelve.
    """
    rutaf = "{}{}.NOBORRAR.ifila".format(csvcfg.entorno("dirarchivos"),
                                         nombrecsv)
    if os.path.isfile(rutaf):
        f = open(rutaf)
        contenido = f.read()
        f.close()
        try:
            tmp = int(contenido) + 1
        except:
            contenido = str(-1)
            abilog.debug("El contenido de «{}.NOBORRAR.ifila» es "
                         "«{}».".format(nombrecsv, contenido))
        if len(contenido) < 8 and int(contenido) >= 0:
            abilog.debug(u"El archivo «{}.NOBORRAR.ifila» existe y "
                         u"su contenido parece coherente "
                         u"(«{}»).".format(nombrecsv, contenido))
        else:
            abilog.aviso(u"El archivo «{}.NOBORRAR.ifila» existe, "
                         u"pero su contenido («{}») es incoherente y se "
                         u"ignora.".format(nombrecsv, contenido))
            contenido = 0
    else:
        contenido = 0
        abilog.debug(u"El archivo «{}.NOBORRAR.ifila» no existe. "
                     u"Se genera desde cero.".format(nombrecsv))
    return contenido

def archivo_de_fila (nombrecsv, datos, nfila):
    """Devuelve el nombre original del fichero contemplado en la fila
    con número de orden [fila] en el conjunto de datos [datos].
    
    El número de orden 0 se reserva para los nombres de los campos.
    """
    campo = csvcfg.entorno("nombresorigen")
    ncampo = nombre_num_campo(datos, campo)
    return datos[nfila][ncampo]

def archivo_destino_de_fila (nombrecsv, datos, nfila):
    """Devuelve el nombre en Wikimedia Commons del fichero contemplado
    en la fila con número de orden [fila] en el conjunto de
    datos [datos].
    
    El número de orden 0 se reserva para los nombres de los campos.
    """
    campo = csvcfg.entorno("nombresdestino")
    ncampo = nombre_num_campo(datos, campo)
    return datos[nfila][ncampo]

#### Comprobaciones ####################################################

def comprobar_ficheros (nombrecsv, datos):
    """Comprueba:
        * que no haya filas con nombres de ficheros vacíos;
        * que no haya filas con nombres de ficheros repetidos;
        * que todos los ficheros indicados existan.
    
    Si la comprobación no es exitosa, devuelve el motivo. Si lo es,
    devuelve None.
    """
    ncamponombre = nombre_num_campo(datos, csvcfg.entorno("nombresorigen"))
    nfila = 1
    for fila in datos[1:]:
        if not fila[ncamponombre]:
            return (u"Hay ficheros sin un nombre especificado en el campo "
                    u"«{}» de «{}».".format(csvcfg.entorno("nombresorigen"),
                                            nombrecsv))
        else:
            rutafichero = os.path.join(csvcfg.entorno("dirarchivos"),
                                       fila[ncamponombre])
            
            if not SIMULACION and not os.path.isfile(rutafichero):
                return (u"No se encuentra el fichero «{}». "
                        u"Es posible que no exista o que no sea "
                        u"legible.".format(rutafichero))
        for nfilacmp in range(nfila+1, len(datos[1:])):
            if fila[ncamponombre] == datos[nfilacmp][ncamponombre]:
                return (u"Error. El nombre de fichero «{}» está "
                        u"contemplado más de una vez en "
                        u"«{}».".format(fila[ncamponombre], nombrecsv))
        nfila += 1
    return None

def comprobar_fila (nombrecsv, datos, fila):
    """Comprueba si la información de la fila con número de orden [fila]
    del conjunto de datos [datos] es correcta.
    
    Si no es correcta, devuelve el motivo. Si lo es, devuelve None.
    """
    for campo in datos[0]:
        valor = valores(datos,fila,[campo])[0]
        if valor:
            if re.search(csvcfg.regex(campo), valor) == None:
                return (u"El valor «{}», en la {}.ª fila, "
                        u"no es válido para el campo "
                        u"«{}».".format(valor, fila+1, campo))
    return None

def comprobar_campos (nombrecsv, datos):
    """Comprueba que los campos del conjunto de datos [datos] sean
    válidos.
    
    Esto es:
        * no hay campos repetidos;
        * no hay campos vacíos (sin nombre);
        * hay, al menos, dos campos en el CSV;
        * existe el campo donde se indica el nombre de los ficheros.
    Si no son válidos, devuelve un motivo. Si lo son, devuelve None.
    """
    nCampos = len(datos[0])
    if nCampos < 2:
        return u"No hay suficientes campos en el conjunto de datos."
    else:
        for i in range(nCampos):
            if not datos[0][i]:
                return u"Hay uno o más campos sin nombre."
            else:
                if datos[0].count(datos[0][i]) > 1:
                    return (u"El campo «{}» está "
                            u"repetido.".format(datos[0][i]))
    camponombre = csvcfg.entorno("nombresorigen")
    existecamponombre = False
    for campo in datos[0]:
        if campo == camponombre:
            existecamponombre = True
    if not existecamponombre:
        return (u"El campo «{}», configurado para albergar los "
                u"nombres de los ficheros, no se encuentra recogido "
                u"en «{}».".format(camponombre, nombrecsv))
    abilog.info(u"Los nombres de los campos son válidos.")
    return None

def comprobar_todo (nombrecsv, datos):
    """Comprueba si el conjunto de datos [datos] es válido.
    
    Si no es válido, devuelve un motivo. Si lo es, devuelve None.
    Un conjunto de datos se considera válido si, y solo si:
        * no hay campos repetidos;
        * no hay campos vacíos (sin nombre);
        * no hay filas sin nombre de fichero;
        * los ficheros existen en el directorio correspondiente;
        * no hay nombres de ficheros repetidos;
        * hay, al menos, dos campos en el CSV;
        * existe el campo donde se indica el nombre de los ficheros;
        * hay, al menos, una fila con información;
        * la información de las filas es válida según las reglas
              definidas para la subida en particular.
    """
    abilog.info(u"Comprobando la corrección de los datos de "
                u"«{}».".format(nombrecsv))
    lendatos = len(datos)
    if lendatos < 2:
        comprobacion = (u"Debe haber, al menos, un archivo contemplado "
                        u"para subir a Wikimedia Commons y, por tanto, "
                        u"un mínimo de dos filas en «{}».".format(nombrecsv))
    else:
        comprobacion = comprobar_campos(nombrecsv, datos)
        if comprobacion == None:
            abilog.info(u"Comprobando ficheros. Espere, por favor.")
            comprobacion = comprobar_ficheros(nombrecsv, datos)
            if comprobacion == None:
                if lendatos > 10000:
                    division = 1000
                elif lendatos > 5000:
                    division = 500
                elif lendatos > 1000:
                    division = 100
                elif lendatos > 100:
                    division = 25
                else:
                    division = 10
                for fila in range(1,lendatos):
                    comprobacion = comprobar_fila(nombrecsv,datos,fila)
                    if comprobacion:
                        break
                    if fila % division == 0:
                        abilog.info(u"{} filas de información "
                                    u"validadas.".format(fila))
                if comprobacion == None:
                    if fila % division != 0:
                        abilog.info(u"{} filas de información "
                                    u"validadas, comprobación "
                                    u"completada.".format(fila))
                    else:
                        abilog.info(u"Comprobación completada.")
    return comprobacion

def comprobar_subida (f):
    """Comprueba si el fichero [f] existe íntegramente en Commons.
    
    Devuelve None en caso afirmativo, o un mensaje de error en caso
    contrario.
    Se basa en SHA-1 y en la API de Wikimedia Commons.
    """
    aisha1 = sha1_f(f)
    abilog.debug(u"SHA-1 de {}: {}".format(f, aisha1))
    if not SIMULACION:
        url = u"https://commons.wikimedia.org/w/api.php?action=query&" \
              u"list=allimages&format=json&aiprop=sha1&" \
              u"aisha1={}".format(aisha1)
        try:
            f = urllib.urlopen(url)
        except:
            abilog.debug(u"Error al acceder a {}.".format(url))
            return u"No se ha logrado acceder a la API de Wikimedia " \
                   u"Commons. Revise la conexión e inténtelo de nuevo."
        txt = f.read()
        d = json.loads(txt)
        abilog.debug(u"Contenido de la consulta: {}".format(d))
        try:
            sha1 = d['query']['allimages'][0]['sha1']
        except:
            abilog.debug(u"Error al obtener el SHA-1 con {}.".format(url))
            return u"Es probable que el archivo no haya podido subirse " \
                   u"a Wikimedia Commons. Inténtelo de nuevo o repare " \
                   u"el error."
        if not aisha1 == sha1:
            abilog.debug(u"{} != {}".format(aisha1, sha1))
            return u"Fallo inesperado. Contacte con el desarrollador " \
                   u"por medio de <{}>.".format(correoAyuda)
    return None

#### Interacción #######################################################

def descansar (tdescanso):
    """Indica al operador que lleva más de [tdescanso] minutos de
    procesamiento ininterrumpido de archivos hasta el momento, y sugiere
    un descanso.
    """
    print
    abilog.aviso(u"Llevamos más de {} minutos seguidos subiendo "
                 u"archivos. ¿Por qué no un "
                 u"descanso?".format(int(tdescanso/60)))
    time.sleep(2)
    abilog.info(u"Recuerde: aunque cierre el programa, la sesión "
                u"se guardará y podrá continuar más adelante en el "
                u"mismo punto en que dejó el proceso de subida.")
    time.sleep(2)
    preg = u"¿Quiere salir y continuar en otro momento?"
    r = sn(preg)
    if r:
        abilog.debug(u"Se decide descansar y salir.")
        print u"Muy bien, seguimos en otro momento. :)"
        time.sleep(5)
        sys.exit()
    else:
        print

def sn (pregunta):
    """Plantea la pregunta [pregunta] al operador y le pide que responda
    afirmativa ("s") o negativamente ("n"), devolviendo True o False,
    respectivamente.
    
    No se hace distinción entre mayúsculas y minúsculas.
    """
    while (True):
        print u"\n{}".format(pregunta)
        r = raw_input("s/n: ").upper()
        if r == "S":
            return True
        elif r == "N":
            return False

def reintentar (nombrecsv,datos,f,fdestino,descr):
    abilog.debug(u"Se pregunta si reintentar la subida.")
    r = sn(u"¿Desea reintentar la subida?")
    if r:
        abilog.debug(u"Se escoge reintentar la subida.")
        subir(nombrecsv,datos,f,fdestino,descr)
        comprobacion = comprobar_subida(f)
        if comprobacion:
            abilog.error(comprobacion)
            reintentar(nombrecsv,datos,f,fdestino,descr)
    else:
        abilog.debug(u"Se escoge no reintentar la subida.")
        flog = open(u"{}{}.fallidas.log".format(csvcfg.entorno("dirarchivos"),
                                                nombrecsv),
                    'a')
        flog.write("{}\n".format(f))
        flog.close()
        

#### Procesamiento #####################################################

def bucle (nombrecsv, datos, nultimof):
    correctos = 0
    
    # Número de archivos que tratar en la tanda inicial
    tanda = 5 # por defecto
    try:
        tmp = int(csvcfg.cte("tanda0"))
        if tmp > 0:
            tanda = tmp
    except:
        abilog.debug("No se ha definido el número de archivos que "
                     "tratar en la tanda inicial.")
        abilog.debug("Se asume {}.".format(tanda))
    
    # Número fijo de archivos que aprobar manualmente en cada tanda
    if tanda < 3:
        conAprobacion = tanda # por defecto
    else:
        conAprobacion = 3 # por defecto
    try:
        tmp = int(csvcfg.cte("conaprobacion"))
        if tmp < conAprobacion and tmp >= 0:
            conAprobacion = tmp
            abilog.debug("Número de archivos que aprobar manualmente "
                         "en cada tanda: {}".format(conAprobacion))
        else:
            abilog.error("La configuración del número de archivos que "
                         "aprobar manualmente en cada tanda ({}) no es "
                         "coherente.".format(tmp))
            abilog.info("Se asume {}.".format(conAprobacion))
            
    except:
        abilog.info("No se ha definido el número de archivos que "
                    "aprobar manualmente en cada tanda.")
        abilog.info("Se asume {}.".format(conAprobacion))
    
    # Tiempo de trabajo ininterrumpido a partir del que sugerir descansar
    tdescanso = 1800 # 1800 s = 30 min, por defecto
    try:
        tdescanso = csvcfg.cte("tdescanso") * 60 # cálculos en segundos
        abilog.debug("Tiempo de trabajo ininterrumpido en minutos a "
                     "partir del que sugerir un descanso al operador: "
                     "{}".format(tdescanso/60))
    except:
        abilog.debug("No se ha definido el tiempo de trabajo "
                     "ininterrumpido en minutos a partir del que "
                     "sugerir un descanso al operador.")
        abilog.debug("Por defecto, se asume {}.".format(tdescanso/60))
    
    # Factor de crecimiento en el número de archivos en cada tanda
    crecimientoTanda = 1.5 # por defecto
    try:
        crecimientoTanda = csvcfg.cte("crecimientotanda")
        abilog.debug("Factor de crecimiento en el número de archivos que "
                     "tratar en cada tanda: {}".format(crecimientoTanda))
    except:
        abilog.debug("No se ha definido un factor de crecimiento en el "
                     "número de archivos que tratar en cada tanda.")
        abilog.debug("Por defecto, se asume {}.".format(crecimientoTanda))
    
    # Bucle
    t0 = time.time()
    for nfila in range(nultimof+1, len(datos)):
        if correctos == tanda:
            print
            abilog.info(u"Se ha tratado una tanda de {} "
                        u"archivos.".format(tanda))
            abilog.info(u"Total de ficheros de {} tratados hasta "
                        u"ahora: {}".format(nombrecsv,nfila-1))
            abilog.info(u"Total de ficheros por subir: "
                        u"{}".format(len(datos)-nfila))
            tanda = int(tanda * crecimientoTanda)
            if INTERACTIVO:
                tmp = random.randint(0, 6)
                if tmp == 0:
                    palabra = u"CONTINUAR"
                elif tmp == 1:
                    palabra = u"PROSEGUIR"
                elif tmp == 2:
                    palabra = u"SEGUIR"
                elif tmp == 3:
                    palabra = u"ADELANTE"
                elif tmp == 4:
                    palabra = u"AVANZAR"
                elif tmp == 5:
                    palabra = u"REANUDAR"
                else:
                    palabra = u"WIKIMEDIA"
                print (u"Por favor, revise las subidas realizadas hasta "
                       u"el momento en Wikimedia Commons.")
                print (u"Si encuentra todo en orden, escriba "
                       u"«{}».".format(palabra))
                abilog.info(u"La siguiente tanda será de {} "
                            u"archivos.".format(tanda))
                abilog.debug(u"Se pide escribir «{}».".format(palabra))
                continuar = False
                t0rev = time.time()
                while (not continuar):
                    r = raw_input("> ")
                    abilog.debug("Se escribe «{}».".format(r))
                    if r.upper() == palabra:
                        if time.time() - t0rev < 7 + tanda/5:
                            print
                            abilog.aviso(u"No ha revisado las subidas "
                                         u"convenientemente.")
                            abilog.info(u"Es importante cerciorarse "
                                        u"de que las subidas "
                                        u"realizadas hasta el momento "
                                        u"sean correctas, en "
                                        u"especial, las de la última "
                                        u"tanda.")
                            abilog.info(u"Cuando las haya revisado, "
                                        u"escriba «{}» de nuevo, "
                                        u"por favor.".format(palabra))
                            print
                            t0rev = time.time()
                        else:
                            if time.time() - t0 > tdescanso:
                                descansar(tdescanso)
                                t0 = time.time()
                            continuar = True
            else:
                print
                abilog.info(u"El proceso se pausará por 115 segundos.")
                time.sleep(115)
                abilog.info(u"La siguiente tanda será de {} "
                            u"archivos.".format(tanda))
            correctos = 0
        f = archivo_de_fila(nombrecsv, datos, nfila)
        print
        abilog.info(u"Cargando {}.ª fila.".format(nfila))
        print ("".center(80, '-'))
        abilog.info(u"Archivo original: {}".format(f))
        fdestino = archivo_destino_de_fila(nombrecsv, datos, nfila)
        abilog.info(u"Archivo en Commons: {}".format(fdestino))
        descr = csvcfg.descripcion(datos,nfila)
        print "Descripción:"
        print descr
        print ("".center(80, '-'))
        if INTERACTIVO:
            if correctos < conAprobacion:
                preg = u"¿Son correctos los datos indicados?"
                time.sleep(4.5)
                r = sn(preg)
                if r:
                    abilog.debug(u"Los datos se dan por correctos.")
                else:
                    print (u"\nPor favor, corrija cuanto sea "
                           u"necesario y contacte con el "
                           u"desarrollador a través de "
                           u"<{}>.".format(correoAyuda))
                    print (u"Gracias.")
                    time.sleep(20)
                    sys.exit()
        subir(nombrecsv,datos,f,fdestino,descr)
        comprobacion = comprobar_subida(f)
        if comprobacion:
            abilog.error(comprobacion)
            reintentar(nombrecsv,datos,f,fdestino,descr)
        guardar_fila(nombrecsv,nfila)
        correctos += 1

def fin (nombrecsv):
    """Notifica el fin del proceso de subida y reinicializa los datos
    guardados.
    """
    time.sleep(1)
    print
    print ("".center(80, '*'))
    print
    abilog.info(u"El proceso de subida se da por concluido.")
    abilog.info(u"Por favor, revise los resultados.")
    abilog.info(u"Mil gracias por su contribución.")
    log_hash(u"{}.log".format(nombrecsv))
    print
    print ("".center(80, '*'))
    print
    guardar_fila(nombrecsv, 0)
    time.sleep(10)

def main ():
    print chr(27) + "[2J" # limpiar pantalla
    nombrecsv = csvcfg.entorno("nombrecsv")
    abilog.config(u"{}.log".format(nombrecsv)) # fichero de registros
    abilog.debug(u"---")
    abilog.debug(u"Se abre el programa.")
    try:
        abilog.debug(u"Operador/a: {}".format(getpass.getuser()))
    except:
        pass
    log_hash(u"{}.log".format(nombrecsv))
    if dirpwb or SIMULACION:
        abilog.info(u"El directorio de Pywikibot encontrado es " \
                    u"«{}».".format(dirpwb))
        error = None
        try:
            urllib.urlopen("https://commons.wikimedia.org/")
        except:
            error = u"No puede accederse a Wikimedia Commons."
        try:
            urllib.urlopen("https://commons.wikimedia.org/w/api.php")
        except:
            error = u"No puede accederse a la API de Wikimedia " \
                    u"Commons (https://commons.wikimedia.org/w/api.php)."
        if not error:
            abilog.info(u"La conexión se ha comprobado "
                        u"satisfactoriamente.")
            login_pwb()
            abilog.info(u"Creando copias de seguridad.")
            error = copia_seguridad("{}{}".format(csvcfg.entorno("dirarchivos"),
                                                  nombrecsv))
        if error:
            abilog.error(error)
        else:
            datos = leer_csv(nombrecsv)
            if datos:
                abilog.info(u"Lectura completada.")
                #print_datos(datos)
                abilog.info(u"Total de archivos contemplados "
                            u"para la subida: {}".format(len(datos)-1))
                abilog.info(u"Total de campos de información "
                            u"detectados: {}".format(len(datos[0])))
                error = comprobar_todo(nombrecsv, datos)
                if error:
                    abilog.error(error)
                else:
                    ifila = int(cargar_fila(nombrecsv))
                    if ifila == 0:
                        guardar_fila(nombrecsv,ifila)
                    abilog.info(u"Ficheros de {} tratados hasta "
                                u"ahora: {}".format(nombrecsv,ifila))
                    abilog.info(u"Ficheros por subir: "
                                u"{}".format(len(datos)-ifila-1))
                    time.sleep(2)
                    print
                    nultimof = int(cargar_fila(nombrecsv))
                    ultimof = archivo_de_fila(nombrecsv, datos, nultimof)
                    if nultimof > 0:
                        abilog.info(u"Hay datos guardados de una "
                                    u"sesión anterior de la subida "
                                    u"de archivos de "
                                    u"«{}».".format(nombrecsv))
                        abilog.info(u"Según los cálculos, el "
                                    u"último fichero tratado fue "
                                    u"«{}», de la {}.ª "
                                    u"fila.".format(ultimof, nultimof))
                        if INTERACTIVO:
                            desconocido = True
                            while (desconocido):
                                print (u"\nEscriba «REANUDAR» si quiere "
                                       u"continuar ya con el proceso de "
                                       u"subida de ficheros contemplados "
                                       u"en «{}» a Wikimedia Commons en "
                                       u"el punto indicado, o bien «REINICIAR» "
                                       u"si desea eliminar la sesión guardada "
                                       u"y comenzar todo el proceso de subida "
                                       u"desde el principio.\n".format(nombrecsv))
                                abilog.debug(u"Se pide la escritura de "
                                             u"«REANUDAR» o de «REINICIAR».")
                                r = raw_input("> ")
                                abilog.debug("Se escribe «{}».".format(r))
                                r = r.upper()
                                if r == "REANUDAR":
                                    desconocido = False
                                elif r == "REINICIAR":
                                    abilog.debug(u"Se pide confirmación.")
                                    preg = (u"¿Está seguro de que quiere "
                                            u"borrar todos los progresos "
                                            u"para {} e iniciar el proceso "
                                            u"de nuevo?".format(nombrecsv))
                                    if sn(preg):
                                        abilog.debug(u"Se confirma.")
                                        print
                                        abilog.info(u"Se han borrado "
                                                    u"todos los progresos "
                                                    u"para {}.".format(nombrecsv))
                                        abilog.info(u"Se empezará de cero.")
                                        nultimof = 0
                                        guardar_fila(nombrecsv,0)
                                        desconocido = False
                                    else:
                                        abilog.debug(u"No se confirma.")
                    else:
                        nultimof = 0
                        if INTERACTIVO:
                            print (u"\nEscriba «COMENZAR» si ha revisado "
                                   u"concienzudamente la información del "
                                   u"fichero «{}» y quiere iniciar ya el "
                                   u"proceso de subida de los archivos "
                                   u"multimedia contemplados a Wikimedia "
                                   u"Commons.\n".format(nombrecsv))
                            abilog.debug(u"Se pide la escritura de "
                                         u"«COMENZAR».")
                            comenzar = False
                            while (not comenzar):
                                r = raw_input("> ")
                                abilog.debug(u"Se escribe «{}».".format(r))
                                if r.upper() == "COMENZAR":
                                    comenzar = True
                    print
                    print (" AVISO IMPORTANTE ".center(80, '#'))
                    print (u"\nDESDE ESTE MOMENTO, NO MODIFIQUE EL FICHERO "
                           u"DE CSV «{}», NI LOS FICHEROS POR SUBIR, NI "
                           u"LOS DE CONFIGURACIÓN DEL PROGRAMA, NI NINGÚN "
                           u"OTRO FICHERO UTILIZADO O, SIMPLEMENTE, LEÍDO "
                           u"POR ESTE PROGRAMA, NI SIQUIERA AUNQUE CIERRE "
                           u"EL PROGRAMA Y LO VUELVA A "
                           U"ABRIR.".format(nombrecsv))
                    print (u"HACERLO DERIVARÁ EN UN COMPORTAMIENTO "
                           u"IMPREDECIBLE, Y USTED, OPERADOR, SE HARÁ "
                           u"RESPONSABLE DE TODOS LOS DAÑOS "
                           U"OCASIONADOS.")
                    print (u"SI VERDADERAMENTE NECESITA EFECTUAR ALGUNA "
                           u"MODIFICACIÓN A PARTIR DE AHORA, EXPONGA LA "
                           u"SITUACIÓN EN UN CORREO ELECTRÓNICO DIRIGIDO "
                           u"A <{}>. GRACIAS.\n".format(correoAyuda))
                    print ("".center(80, '#'))
                    print
                    if INTERACTIVO:
                        time.sleep(10)
                    bucle(nombrecsv,datos,nultimof)
                    fin(nombrecsv)

if __name__ == '__main__':
    main()
