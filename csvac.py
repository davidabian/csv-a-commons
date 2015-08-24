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
#    TODO: Optimizar funciones y reducir sus costes en tiempo y memoria.
#    TODO: i18n.
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
        dirPosible = os.path.abspath(dirPosible)
        check1 = os.path.join(dirPosible,"pwb.py")
        check2 = os.path.join(dirPosible,"scripts","upload.py")
        if os.path.isfile(check1) and os.path.isfile(check2):
            directorio = dirPosible
            break
    if directorio is None:
        print(u"ERROR: No se encuentra una instalación de Pywikibot "
              u"core en las proximidades del directorio actual.")
    return directorio

DIR_PWB = comprobar_pwb()
if DIR_PWB:
    sys.path.append(DIR_PWB)
    import pwb
    import pywikibot
    sys.path.append(os.path.join(DIR_PWB,"scripts"))
    import upload
    #SITE_PWB = pywikibot.Site('test', 'test')
    SITE_PWB = pywikibot.Site('commons', 'commons')

#### Hashes ############################################################

def sha1_f (cfg, f):
    """Devuelve el SHA-1 del fichero [f], o None en caso de error."""
    f = os.path.join(cfg["nombreDir"], f)
    if not SIMULACION:
        with open(f, 'rb') as af:
            try:
                sha1 = hashlib.sha1(af.read()).hexdigest()
            except:
                sha1 = None
    else:
        sha1 = None
    return sha1

def log_hash (cfg, f):
    """Registra el hash SHA-1 del fichero [f] en el de depuración."""
    sha1 = sha1_f(cfg, f)
    if sha1:
        abilog.debug(u"{}: {}".format(f, sha1))
    else:
        abilog.debug(u"{}: ???".format(f))

#### Pywikibot #########################################################

def login_pwb ():
    """Inicia sesión en Wikimedia Commons con Pywikibot core."""
    if not SIMULACION:
        SITE_PWB.login()
        while not SITE_PWB.logged_in():
            abilog.error(u"No se ha iniciado sesión en {} con "
                         u"Pywikibot.".format(SITE_PWB))
            time.sleep(1.5)
            print
            SITE_PWB.login()
            time.sleep(1.5)
    elif not SITE_PWB.logged_in():
        abilog.error(u"No se ha iniciado sesión en {} con "
                     u"Pywikibot.".format(SITE_PWB))

def subir (cfg, f, fdestino, descr):
    """Trata de subir el fichero de nombre [f] a Wikimedia Commons con
    el nombre [fdestino] y la descripción [descr].
    """
    if not SIMULACION:
        bot = upload.UploadRobot(url=[os.path.join(cfg["nombreDir"], f)],
                                 description=descr,
                                 useFilename=fdestino,
                                 keepFilename=True,
                                 verifyDescription=False,
                                 ignoreWarning=False,
                                 targetSite=SITE_PWB,
                                 aborts=True,
                                 always=True)
        bot.run()
    return 0

#### CSV ###############################################################

def leer_csv (cfg):
    """Lee el fichero de CSV de nombre cfg["nombreCsv"], en el
    directorio cfg["nombreDir"], decodifica su contenido usando UTF-8 y
    lo devuelve en forma de lista.
    
    La estructura de la lista devuelta es:
        [fila_1,fila_2,...,fila_i], donde
            fila_n es una lista de los elementos de la fila n;
            i es el número de columnas en el fichero de CSV.
    En caso de error, devuelve la lista vacía.
    """
    datos = []
    if os.path.isfile(os.path.join(cfg["nombreDir"], cfg["nombreCsv"])):
        abilog.info(u"Iniciando lectura del fichero "
                    u"«{}».".format(cfg["nombreCsv"]))
        with open(os.path.join(cfg["nombreDir"],
                               cfg["nombreCsv"]), 'rb') as f:
            reader = csv.reader(f)
            for fila in reader:
                for i in range(len(fila)):
                    fila[i] = fila[i].decode('utf-8')
                datos.append(fila)
    else:
        abilog.error(u"No se encuentra el fichero «{}». "
                     u"Es posible que no exista o que no sea "
                     u"legible.".format(cfg["nombreCsv"]))
    return datos

#### Base ##############################################################

def print_datos (datos):
    for fila in datos:
        for elemento in fila:
            print elemento

def nombre_num_campo (campos, nombreCampo):
    """Devuelve el número de orden del campo de nombre [nombreCampo] de
    la lista de campos [campos], o bien None si no existe un campo con
    tal nombre.
    
    Se hace distinción entre mayúsculas y minúsculas.
    El número de orden del primer campo es 0.
    """
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
        numCampo = nombre_num_campo(datos[0],nombreCampo)
        if numCampo is None:
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
                u"legible.".format(nombrefichero))
    return None

def guardar_fila (cfg, ifila):
    """Guarda [ifila] como contenido del fichero de texto
    cfg["nombreCsv"].NOBORRAR.ifila, ubicado en cfg["nombreDir"].
    """
    f = open(u"{}.NOBORRAR.ifila".format(os.path.join(cfg["nombreDir"], 
                                                      cfg["nombreCsv"])), 
             'w')
    f.write(str(ifila))
    f.close()

def cargar_fila (cfg):
    """Carga el contenido del fichero de texto
    cfg["nombreCsv"].NOBORRAR.ifila, en el directorio cfg["nombreDir"],
    y lo devuelve.
    """
    rutaf = "{}.NOBORRAR.ifila".format(os.path.join(cfg["nombreDir"], 
                                                    cfg["nombreCsv"]))
    if os.path.isfile(rutaf):
        f = open(rutaf)
        contenido = f.read()
        f.close()
        try:
            tmp = int(contenido) + 1
        except:
            contenido = str(-1)
            abilog.debug("El contenido de «{}.NOBORRAR.ifila» es "
                         "«{}».".format(cfg["nombreCsv"], contenido))
        if len(contenido) < 8 and int(contenido) >= 0:
            abilog.debug(u"El archivo «{}.NOBORRAR.ifila» existe y "
                         u"su contenido parece coherente "
                         u"(«{}»).".format(cfg["nombreCsv"], contenido))
        else:
            abilog.aviso(u"El archivo «{}.NOBORRAR.ifila» existe, "
                         u"pero su contenido («{}») es incoherente y se "
                         u"ignora.".format(cfg["nombreCsv"], contenido))
            contenido = 0
    else:
        contenido = 0
        abilog.debug(u"El archivo «{}.NOBORRAR.ifila» no existe. "
                     u"Se genera desde cero.".format(cfg["nombreCsv"]))
    return contenido

def archivo_de_fila (cfg, datos, nfila):
    """Devuelve el nombre original del fichero contemplado en la fila
    con número de orden [fila] en el conjunto de datos [datos].
    
    El número de orden 0 se reserva para los nombres de los campos.
    """
    campo = cfg["campoNombres0"]
    ncampo = nombre_num_campo(datos[0], campo)
    return datos[nfila][ncampo]

def archivo_destino_de_fila (cfg, datos, nfila):
    """Devuelve el nombre en Wikimedia Commons del fichero contemplado
    en la fila con número de orden [fila] en el conjunto de
    datos [datos].
    
    El número de orden 0 se reserva para los nombres de los campos.
    """
    campo = cfg["campoNombresC"]
    ncampo = nombre_num_campo(datos[0], campo)
    return datos[nfila][ncampo]

#### Comprobaciones ####################################################

def comprobar_ficheros (cfg, datos):
    """Comprueba:
        * que no haya filas con nombres de ficheros vacíos;
        * que no haya filas con nombres de ficheros repetidos;
        * que todos los ficheros locales indicados existan;
        * que todos los nombres de destino de los ficheros tengan
              extensión.
    
    Si la comprobación no es exitosa, devuelve el motivo. Si lo es,
    devuelve None.
    """
    # Número de orden del campo de nombres de origen de los ficheros
    nCampoNombres0 = nombre_num_campo(datos[0], cfg["campoNombres0"])
    # Número de orden del campo de nombres de destino de los ficheros
    nCampoNombresC = nombre_num_campo(datos[0], cfg["campoNombresC"])
    nfila = 1
    for fila in datos[1:]:
        # Análsis de los nombres de origen de los ficheros
        if not fila[nCampoNombres0]:
            return (u"Hay ficheros sin un nombre especificado en el "
                    u"campo «{}» de «{}».".format(cfg["campoNombres0"],
                                                  cfg["nombreCsv"]))
        else:
            rutaf0 = os.path.join(cfg["nombreDir"],
                                  fila[nCampoNombres0])
            if not SIMULACION and not os.path.isfile(rutaf0):
                return (u"No se encuentra el fichero «{}». "
                        u"Es posible que no exista o que no sea "
                        u"legible.".format(rutaf0))
        for nfilacmp in range(nfila+1, len(datos[1:])):
            if fila[nCampoNombres0] == datos[nfilacmp][nCampoNombres0]:
                return (u"El nombre de fichero «{}» está contemplado "
                        u"más de una vez en "
                        u"«{}».".format(fila[nCampoNombres0],
                                        cfg["nombreCsv"]))
        # Análsis de los nombres de destino los ficheros
        if not fila[nCampoNombresC]:
            return (u"Hay ficheros sin un nombre especificado en el "
                    u"campo «{}» de «{}».".format(cfg["campoNombresC"],
                                                  cfg["nombreCsv"]))
        elif "." not in fila[nCampoNombresC]:
            return (u"El archivo «{}», en la {}.ª fila de información "
                    u"del fichero «{}», no tiene un nombre final "
                    u"válido para la subida porque carece de "
                    u"extensión.".format(fila[nCampoNombresC],
                                         nfila,
                                         cfg["nombreCsv"]))
        for nfilacmp in range(nfila+1, len(datos[1:])):
            if fila[nCampoNombresC] == datos[nfilacmp][nCampoNombresC]:
                return (u"El nombre de fichero «{}» está contemplado "
                        u"más de una vez en "
                        u"«{}».".format(fila[nCampoNombresC],
                                        cfg["nombreCsv"]))
        nfila += 1
    return None

def comprobar_fila (datos, fila):
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

def comprobar_campos (cfg, datos):
    """Comprueba que los nombres de los campos del conjunto de datos
    [datos] sean válidos.
    
    Esto es:
        * no hay campos repetidos;
        * no hay campos vacíos (sin nombre);
        * hay, al menos, dos campos en el CSV;
        * existe el campo donde se indica el nombre de los ficheros.
    Si no son válidos, devuelve un motivo. Si lo son, devuelve None.
    """
    campos = datos[0]
    if len(campos) < 2:
        return (u"No hay suficientes campos en el conjunto de datos, o "
                u"bien el fichero de CSV no está construido con comas "
                u"como separadores de campos.")
    else:
        for i in range(len(campos)):
            if not campos[i]:
                return u"Hay uno o más campos sin nombre."
            else:
                if campos.count(campos[i]) > 1:
                    return (u"El campo «{}» está "
                            u"repetido.".format(campos[i]))
    if cfg["campoNombres0"] not in campos:
        return (u"El campo «{}», configurado para albergar los "
                u"nombres locales de los ficheros, no se encuentra "
                u"recogido en "
                u"«{}».".format(cfg["campoNombres0"], cfg["nombreCsv"]))
    if cfg["campoNombresC"] not in campos:
        return (u"El campo «{}», configurado para albergar los "
                u"nombres finales de los ficheros en Wikimedia Commons, "
                u"no se encuentra recogido en "
                u"«{}».".format(cfg["campoNombresC"], cfg["nombreCsv"]))
    abilog.info(u"Los nombres de los campos son válidos.")
    return None

def comprobar_todo (cfg, datos):
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
                u"«{}».".format(cfg["nombreCsv"]))
    lendatos = len(datos)
    if lendatos < 2:
        comprobacion = (u"Debe haber, al menos, un archivo contemplado "
                        u"para subir a Wikimedia Commons y, por tanto, "
                        u"un mínimo de dos filas en "
                        u"«{}».".format(cfg["nombreCsv"]))
    else:
        comprobacion = comprobar_campos(cfg, datos)
        if comprobacion is None:
            abilog.info(u"Comprobando ficheros. Espere, por favor.")
            comprobacion = comprobar_ficheros(cfg, datos)
            if comprobacion is None:
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
                    comprobacion = comprobar_fila(datos,fila)
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

def comprobar_subida (cfg, f):
    """Comprueba si el fichero [f] existe íntegramente en Commons.
    
    Devuelve None en caso afirmativo, o un mensaje de error en caso
    contrario.
    Se basa en SHA-1 y en la API de Wikimedia Commons.
    """
    aisha1 = sha1_f(cfg, f)
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

def descansar (tDescansoSeg):
    """Indica al operador que lleva más de [tDescansoSeg] segundos de
    procesamiento ininterrumpido de archivos hasta el momento, y sugiere
    un descanso.
    """
    print
    abilog.aviso(u"Llevamos más de {} minutos seguidos subiendo "
                 u"archivos. ¿Por qué no un "
                 u"descanso?".format(int(tDescansoSeg/60)))
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
    while True:
        print u"\n{}".format(pregunta)
        r = raw_input("s/n: ").upper()
        if r == "S":
            return True
        elif r == "N":
            return False

def reintentar (cfg,datos,f,fdestino,descr):
    abilog.debug(u"Se pregunta si reintentar la subida.")
    r = sn(u"¿Desea reintentar la subida?")
    if r:
        abilog.debug(u"Se escoge reintentar la subida.")
        subir(cfg,f,fdestino,descr)
        comprobacion = comprobar_subida(cfg,f)
        if comprobacion:
            abilog.error(comprobacion)
            reintentar(cfg,datos,f,fdestino,descr)
    else:
        abilog.debug(u"Se escoge no reintentar la subida.")
        flog = open(u"{}.fallidas.log".format(os.path.join(cfg["nombreDir"], 
                                                           cfg["nombreCsv"])),
                    'a')
        flog.write("{}\n".format(f))
        flog.close()
        

#### Procesamiento #####################################################

def bucle (cfg, datos, nultimof):
    correctos = 0
    tanda = cfg["tanda0"]
    tDescansoSeg = cfg["tDescanso"] * 60 # cálculos en segundos
    t0 = time.time()
    for nfila in range(nultimof+1, len(datos)):
        if correctos == tanda:
            print
            print '*' * 80
            print
            abilog.info(u"Se ha tratado una tanda de {} "
                        u"archivos.".format(tanda))
            abilog.info(u"Total de ficheros de «{}» tratados hasta "
                        u"ahora: {}".format(cfg["nombreCsv"],nfila-1))
            abilog.info(u"Total de ficheros por subir: "
                        u"{}".format(len(datos)-nfila))
            completado = (nfila-1)*100/(len(datos)-1)
            abilog.info(u"Completado: {:.2f} %".format(completado))
            tanda = int(tanda * cfg["crecimTanda"])
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
                print
                print (u"Por favor, revise las subidas realizadas hasta "
                       u"el momento en Wikimedia Commons.")
                print (u"Si encuentra todo en orden, escriba "
                       u"«{}».".format(palabra))
                if len(datos)-nfila <= tanda:
                    abilog.aviso(u"La siguiente tanda será la última "
                                 u"de este proceso de subida.")
                    abilog.info(u"       Constará de los {} archivos "
                                u"restantes.".format(len(datos)-nfila))
                else:
                    abilog.info(u"La siguiente tanda será de {} "
                                u"archivos.".format(tanda))
                abilog.debug(u"Se pide escribir «{}».".format(palabra))
                continuar = False
                t0rev = time.time()
                while not continuar:
                    r = raw_input("> ")
                    abilog.debug("Se escribe «{}».".format(r))
                    if r.upper() == palabra:
                        if time.time() - t0rev < 7 + tanda/20:
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
                            if time.time() - t0 > tDescansoSeg:
                                descansar(tDescansoSeg)
                                t0 = time.time()
                            continuar = True
            else:
                print
                abilog.info(u"El proceso se pausará por 115 segundos.")
                time.sleep(115)
                abilog.info(u"La siguiente tanda será de {} "
                            u"archivos.".format(tanda))
            correctos = 0
            try:
                urllib.urlopen("https://commons.wikimedia.org/")
            except:
                abilog.error(u"No puede accederse a Wikimedia Commons.")
                print u"Por favor, inténtelo más tarde."
                sys.exit()
        f = archivo_de_fila(cfg, datos, nfila)
        print
        abilog.info(u"Cargando {}.ª fila.".format(nfila))
        print '-' * 80
        abilog.info(u"Archivo original: {}".format(f))
        fdestino = archivo_destino_de_fila(cfg, datos, nfila)
        abilog.info(u"Archivo en Commons: {}".format(fdestino))
        descr = csvcfg.descripcion(datos,nfila)
        print "Descripción:"
        print descr
        print '-' * 80
        if INTERACTIVO and correctos < cfg["aprobar"]:
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
        subir(cfg,f,fdestino,descr)
        comprobacion = comprobar_subida(cfg,f)
        if comprobacion:
            abilog.error(comprobacion)
            reintentar(cfg,datos,f,fdestino,descr)
        guardar_fila(cfg,nfila)
        correctos += 1
        time.sleep(cfg["tEspera"])

def fin (cfg):
    """Notifica el fin del proceso de subida y reinicializa los datos
    guardados.
    """
    time.sleep(1)
    print
    print '*' * 80
    print
    abilog.info(u"El proceso de subida se da por concluido.")
    abilog.info(u"Por favor, revise los resultados.")
    abilog.info(u"Mil gracias por su contribución.")
    log_hash(cfg, u"{}.log".format(cfg["nombreCsv"]))
    print
    print '*' * 80
    print
    guardar_fila(cfg, 0)
    time.sleep(10)

def obtener_cfg ():
    ##
    ##  Valores por defecto
    ##
    cfg = {
        "nombreDir":     None,
        "nombreCsv":     None,
        "campoNombres0": None,
        "campoNombresC": None,
        "tDescanso":     30,
        "tEspera":       0,
        "tanda0":        5,
        "aprobar":       3,
        "crecimTanda":   1.5,
    }
    try:
        tmp = csvcfg.cte()
    except:
        tmp = {}
    
    ##
    ##  Nombre del directorio en que se ubican los archivos
    ##
    error = False
    if "nombreDir" not in tmp:
        error = True
        if INTERACTIVO:
            nivel = "AVISO"
        else:
            nivel = "ERROR"
        print(u"{}: No se ha definido el directorio donde se ubican "
              u"los ficheros de la subida en el archivo de "
              u"configuración.".format(nivel))
    elif not type(tmp["nombreDir"]) is str and \
         not type(tmp["nombreDir"]) is unicode:
        error = True
        print(u"ERROR: El directorio «{}», definido en el archivo de "
              u"configuración, no se reconoce como una cadena de "
              u"texto.".format(tmp["nombreDir"]))
    elif not os.path.isdir(tmp["nombreDir"]):
        error = True
        print(u"ERROR: El directorio «{}», definido en el archivo de "
              u"configuración, no existe o no es un "
              u"directorio.".format(tmp["nombreDir"]))
    else:
        #
        #  Superadas todas las pruebas, el valor del archivo de
        #  configuración se considera válido y se adopta.
        #
        cfg["nombreDir"] = tmp["nombreDir"]
    if error:
        if INTERACTIVO:
            while not cfg["nombreDir"]:
                print(u"\nEscriba la ruta completa del directorio "
                      u"en que se encuentran los ficheros que subir "
                      u"y el fichero de CSV.")
                tmp["nombreDir"] = raw_input("> ")
                if tmp["nombreDir"] == "":
                    print(u"ERROR: No ha escrito nada.")
                elif not os.path.isdir(tmp["nombreDir"]):
                    print(u"ERROR: El directorio indicado no es "
                          u"válido o no existe.")
                else:
                    cfg["nombreDir"] = tmp["nombreDir"]
        else:
            sys.exit()
    
    ##
    ##  Nombre del fichero de CSV con la información de la subida
    ##
    error = False
    if "nombreCsv" not in tmp:
        error = True
        if INTERACTIVO:
            nivel = "AVISO"
        else:
            nivel = "ERROR"
        print(u"{}: No se ha definido el nombre del fichero de CSV con "
              u"los datos de la subida en el archivo de "
              u"configuración.".format(nivel))
    elif not type(tmp["nombreCsv"]) is str and \
         not type(tmp["nombreCsv"]) is unicode:
        error = True
        print(u"ERROR: El nombre «{}», definido en el archivo de "
              u"configuración, no se reconoce como una cadena de "
              u"texto.".format(tmp["nombreCsv"]))
    elif not os.path.isfile(tmp["nombreCsv"]):
        if os.path.isfile(u"{}.csv".format(tmp["nombreCsv"])):
            # Detectar omisión de la extensión .csv
            cfg["nombreCsv"] = u"{}.csv".format(tmp["nombreCsv"])
        elif os.path.isfile(u"{}.CSV".format(tmp["nombreCsv"])):
            # Detectar omisión de la extensión .CSV
            cfg["nombreCsv"] = u"{}.CSV".format(tmp["nombreCsv"])
        else:
            error = True
            print(u"ERROR: El fichero «{}», definido en el archivo de "
                  u"configuración, no existe en el directorio «{}» o "
                  u"no es un fichero.".format(tmp["nombreCsv"],
                                              cfg["nombreDir"]))
    else:
        #
        #  Superadas todas las pruebas, el valor del archivo de
        #  configuración se considera válido y se adopta.
        #
        cfg["nombreCsv"] = tmp["nombreCsv"]
    if error:
        if INTERACTIVO:
            while not cfg["nombreCsv"]:
                print(u"\nEscriba el nombre del fichero de CSV ubicado "
                      u"en el directorio «{}» y que contiene los datos "
                      u"de la subida.".format(cfg["nombreDir"]))
                tmp["nombreCsv"] = raw_input("> ")
                if tmp["nombreCsv"] == "":
                    print(u"ERROR: No ha escrito nada.")
                elif not os.path.isfile(tmp["nombreCsv"]):
                    if os.path.isfile(u"{}.csv".format(tmp["nombreCsv"])):
                        # Detectar omisión de la extensión .csv
                        cfg["nombreCsv"] = u"{}.csv".format(tmp["nombreCsv"])
                    elif os.path.isfile(u"{}.CSV".format(tmp["nombreCsv"])):
                        # Detectar omisión de la extensión .CSV
                        cfg["nombreCsv"] = u"{}.CSV".format(tmp["nombreCsv"])
                    else:
                        print(u"ERROR: El fichero indicado no es válido "
                              u"o no existe.")
                else:
                    cfg["nombreCsv"] = tmp["nombreCsv"]
        else:
            sys.exit()
        print
    
    ##
    ##  Configuración del fichero de registros
    ##
    abilog.config(u"{}.log".format(cfg["nombreCsv"]))
    
    ##
    ##  Campo con los nombres locales de los ficheros que subir
    ##
    if "campoNombres0" not in tmp:
        abilog.error(u"No se ha definido en el archivo de "
                     u"configuración el nombre del campo del fichero "
                     u"de CSV que, a su vez, contiene los nombres de "
                     u"los ficheros que tratar.")
        abilog.info(u"Para hacerlo, escriba el nombre en el "
                    u"diccionario de la función cte() de la siguiente "
                    u"forma:")
        abilog.info(u'    "campoNombres0": "Nombre del campo",')
        abilog.info(u"... sustituyendo «Nombre del campo» por el "
                    u"nombre del campo en cuestión.")
        sys.exit()
    else:
        cfg["campoNombres0"] = tmp["campoNombres0"]
    
    ##
    ##  Campo con los nombres finales de los ficheros en Commons
    ##
    if "campoNombresC" not in tmp:
        abilog.error(u"No se ha definido en el archivo de "
                     u"configuración el nombre del campo del fichero "
                     u"de CSV que, a su vez, contiene los nombres de "
                     u"destino de los ficheros en Wikimedia Commons.")
        abilog.info(u"Para hacerlo, escriba el nombre en el "
                    u"diccionario de la función cte() de la siguiente "
                    u"forma:")
        abilog.info(u'    "campoNombresC": "Nombre del campo",')
        abilog.info(u"... sustituyendo «Nombre del campo» por el "
                    u"nombre del campo en cuestión.")
        sys.exit()
    else:
        cfg["campoNombresC"] = tmp["campoNombresC"]
    
    ##
    ##  Tiempo de trabajo a partir del que sugerir un descanso
    ##
    if "tDescanso" not in tmp:
        abilog.debug(u"No se ha definido el tiempo de trabajo a partir "
                     u"del que sugerir un descanso en el archivo de "
                     u"configuración.")
        abilog.debug(u"Se asumirá «{} [minutos]», el valor por "
                     u"defecto.".format(cfg["tDescanso"]))
    elif not type(tmp["tDescanso"]) is int and \
         not type(tmp["tDescanso"]) is float:
        abilog.error(u"El valor «{}», definido en el archivo "
                     u"de configuración como el tiempo de trabajo en "
                     u"minutos a partir del que sugerir un descanso, "
                     u"no es un número "
                     u"válido.".format(str(tmp["tDescanso"])))
        abilog.info(u"Se asumirá «{} [minutos]», el valor por "
                    u"defecto.".format(cfg["tDescanso"]))
        print
    elif tmp["tDescanso"] < 1:
        abilog.error(u"El valor «{} [minutos]», definido en el archivo "
                     u"de configuración como el tiempo de trabajo a "
                     u"partir del que sugerir un descanso, no puede "
                     u"ser inferior a 1.".format(tmp["tDescanso"]))
        abilog.info(u"Se asumirá «{} [minutos]», el valor por "
                    u"defecto.".format(cfg["tDescanso"]))
        print
    else:
        #
        #  Superadas todas las pruebas, el valor del archivo de
        #  configuración se considera válido y se adopta.
        #
        cfg["tDescanso"] = tmp["tDescanso"]
    
    ##
    ##  Tiempo de espera entre subida y subida
    ##
    if "tEspera" not in tmp:
        abilog.debug(u"No se ha definido el tiempo de espera entre "
                     u"subida y subida.")
        abilog.debug(u"Se asumirá «{} [segundos]», el valor por "
                     u"defecto.".format(cfg["tEspera"]))
    elif not type(tmp["tEspera"]) is int and \
         not type(tmp["tEspera"]) is float:
        abilog.error(u"El valor «{}», definido en el archivo "
                     u"de configuración como el tiempo de espera en "
                     u"segundos entre subida y subida, no es un número "
                     u"válido.".format(str(tmp["tEspera"])))
        abilog.info(u"Se asumirá «{} [segundos]», el valor por "
                    u"defecto.".format(cfg["tEspera"]))
        print
    elif tmp["tEspera"] < 0:
        abilog.error(u"El valor «{} [segundos]», definido en el archivo "
                     u"de configuración como el tiempo de espera entre "
                     u"subida y subida, no puede ser "
                     u"negativo.".format(tmp["tEspera"]))
        abilog.info(u"Se asumirá «{} [segundos]», el valor por "
                    u"defecto.".format(cfg["tEspera"]))
        print
    else:
        #
        #  Superadas todas las pruebas, el valor del archivo de
        #  configuración se considera válido y se adopta.
        #
        cfg["tEspera"] = tmp["tEspera"]
    
    ##
    ##  Número de archivos que tratar en la tanda inicial
    ##
    error = True
    if "tanda0" not in tmp:
        msj = (u"No se ha definido el número de archivos que tratar "
               u"en la tanda inicial de subidas.")
        if INTERACTIVO:
            abilog.aviso(msj)
        else:
            abilog.error(msj)
    elif not type(tmp["tanda0"]) is int:
        abilog.error(u"El valor «{}», definido en el archivo de "
                     u"configuración como el número de ficheros que "
                     u"tratar en la tanda inicial, no es un "
                     u"entero.".format(str(tmp["tanda0"])))
    elif tmp["tanda0"] < 1:
        abilog.error(u"El valor «{}», definido en el archivo de "
                     u"configuración como el número de ficheros que "
                     u"tratar en la tanda inicial, no es un entero "
                     u"positivo.".format(str(tmp["tanda0"])))
    elif tmp["tanda0"] > 299 and INTERACTIVO:
        abilog.aviso(u"El valor «{}», definido en el archivo de "
                     u"configuración como el número de ficheros que "
                     u"subir en la tanda inicial, parece "
                     u"desproporcionado.".format(str(tmp["tanda0"])))
        abilog.debug(u"Se pregunta si cambiar tal valor.")
        r = sn(u"¿Desea cambiar el número configurado de archivos que "
               u"tratar en la tanda inicial por otro más razonable?")
        if r:
            abilog.debug(u"Se decide cambiar tal valor.")
            r = None
            while not r:
                print
                abilog.info(u"¿Cuántos archivos deben subirse en la "
                            u"tanda inicial?")
                r = raw_input("> ")
                abilog.debug(u"Se escribe {}.".format(r))
                try:
                    r = int(r)
                except:
                    abilog.error(u"«{}» no es un entero.".format(r))
                    r = None
                if r is not None:
                    if r == "":
                        abilog.error(u"No ha escrito nada.".format(r))
                        r = None
                    elif r > tmp["tanda0"]:
                        abilog.error(u"No tiene sentido, {} es aún mayor "
                                     u"que {}.".format(r, tmp["tanda0"]))
                        r = None
                    elif r < 1:
                        abilog.error(u"No tiene sentido, el número "
                                     u"debe ser mayor que "
                                     u"0.".format(r, tmp["tanda0"]))
                        r = None
            cfg["tanda0"] = r
        else:
            abilog.debug(u"Se decide mantener tal valor.")
            cfg["tanda0"] = tmp["tanda0"]
        print
        error = False
    else:
        #
        #  Superadas todas las pruebas, el valor del archivo de
        #  configuración se considera válido y se adopta.
        #
        cfg["tanda0"] = tmp["tanda0"]
        error = False
    if error:
        #
        #  El valor del archivo de configuración se ha descartado en
        #  alguna prueba.
        #
        abilog.info(u"Se asumirá {}, el valor por "
                    u"defecto.".format(cfg["tanda0"]))
        print
    
    ##
    ##  Número fijo de archivos que aprobar manualmente en cada tanda
    ##
    error = True
    if "aprobar" not in tmp:
        abilog.aviso(u"No se ha definido el número fijo de archivos "
                     u"que aprobar manualmente para su subida en cada "
                     u"tanda.")
    elif not type(tmp["aprobar"]) is int:
        abilog.error(u"El valor «{}», definido en el archivo de "
                     u"configuración como el número fijo de archivos "
                     u"que aprobar manualmente para su subida en cada "
                     u"tanda, no es un "
                     u"entero.".format(str(tmp["aprobar"])))
    elif tmp["aprobar"] < 0:
        abilog.error(u"El valor «{}», definido en el archivo de "
                     u"configuración como el número fijo de archivos "
                     u"que aprobar manualmente para su subida en cada "
                     u"tanda, no puede ser "
                     u"negativo.".format(tmp["aprobar"]))
    elif tmp["aprobar"] > cfg["tanda0"]:
        abilog.error(u"El valor «{}», definido en el archivo de "
                     u"configuración como el número fijo de archivos "
                     u"que aprobar manualmente para su subida en cada "
                     u"tanda, no puede superar el número de archivos "
                     u"que tratar en la tanda inicial "
                     u"({}).".format(tmp["aprobar"],cfg["tanda0"]))
    else:
        #
        #  Superadas todas las pruebas, el valor del archivo de
        #  configuración se considera válido y se adopta.
        #
        cfg["aprobar"] = tmp["aprobar"]
        error = False
    if error:
        #
        #  El valor del archivo de configuración se ha descartado en
        #  alguna prueba.
        #
        abilog.info(u"Se asumirá {}, el valor por "
                    u"defecto.".format(cfg["aprobar"]))
        print
    
    ##
    ##  Factor de crecimiento en el número de archivos de cada tanda
    ##
    error = True
    if "crecimTanda" not in tmp:
        abilog.aviso(u"No se ha definido el factor de crecimiento en el "
                     u"número de archivos de cada tanda.")
    elif not type(tmp["crecimTanda"]) is int and \
         not type(tmp["crecimTanda"]) is float:
        abilog.error(u"El valor «{}», definido en el archivo de "
                     u"configuración como el factor de crecimiento en "
                     u"el número de ficheros de cada tanda, no es un "
                     u"número real.".format(str(tmp["crecimTanda"])))
    elif tmp["crecimTanda"] < 1:
        abilog.error(u"El valor «{}», definido en el archivo de "
                     u"configuración como el factor de crecimiento en "
                     u"el número de ficheros de cada tanda, debe ser "
                     u"1 o mayor que 1.".format(tmp["crecimTanda"]))
    elif tmp["crecimTanda"] > 3:
        abilog.error(u"El valor «{}», definido en el archivo de "
                     u"configuración como el factor de crecimiento en "
                     u"el número de ficheros de cada tanda, es "
                     u"desproporcionado.".format(tmp["crecimTanda"]))
    else:
        #
        #  Superadas todas las pruebas, el valor del archivo de
        #  configuración se considera válido y se adopta.
        #
        cfg["crecimTanda"] = tmp["crecimTanda"]
        error = False
    if error:
        #
        #  El valor del archivo de configuración se ha descartado en
        #  alguna prueba.
        #
        abilog.info(u"Se asumirá {}, el valor por "
                    u"defecto.".format(cfg["crecimTanda"]))
        print
    
    return cfg

def main ():
    if not (DIR_PWB or SIMULACION):
        sys.exit()
    cfg = obtener_cfg()
    print chr(27) + "[2J" # limpiar pantalla
    abilog.debug(u"---")
    abilog.debug(u"Se inicia el programa.")
    try:
        abilog.debug(u"Operador/a: {}".format(getpass.getuser()))
    except:
        abilog.debug(u"Operador/a: ???")
    log_hash(cfg, u"{}.log".format(cfg["nombreCsv"]))
    abilog.info(u"El directorio de Pywikibot encontrado es "
                u"«{}».".format(DIR_PWB))
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
        error = copia_seguridad(os.path.join(cfg["nombreDir"],
                                             cfg["nombreCsv"]))
    if error:
        abilog.error(error)
    else:
        datos = leer_csv(cfg)
        if datos:
            abilog.info(u"Lectura completada.")
            #print_datos(datos)
            abilog.info(u"Total de archivos contemplados "
                        u"para la subida: {}".format(len(datos)-1))
            abilog.info(u"Total de campos de información "
                        u"detectados: {}".format(len(datos[0])))
            error = comprobar_todo(cfg, datos)
            if error:
                abilog.error(error)
            else:
                ifila = int(cargar_fila(cfg))
                if ifila == 0:
                    #
                    #  En caso de error al intentar reanudar la sesión,
                    #  [ifila] será 0, y tal valor se guarda en el
                    #  fichero para reiniciar el proceso de subida.
                    #
                    guardar_fila(cfg,ifila)
                abilog.info(u"Ficheros de {} tratados hasta "
                            u"ahora: {}".format(cfg["nombreCsv"],ifila))
                abilog.info(u"Ficheros por subir: "
                            u"{}".format(len(datos)-ifila-1))
                time.sleep(2)
                print
                ultimof = archivo_de_fila(cfg, datos, ifila)
                if ifila > 0:
                    abilog.info(u"Hay datos guardados de una "
                                u"sesión anterior de la subida "
                                u"de archivos de "
                                u"«{}».".format(cfg["nombreCsv"]))
                    abilog.info(u"Según los cálculos, el "
                                u"último fichero tratado fue "
                                u"«{}», de la {}.ª "
                                u"fila.".format(ultimof, ifila))
                    if INTERACTIVO:
                        desconocido = True
                        while desconocido:
                            print (u"\nEscriba «REANUDAR» si quiere "
                                   u"continuar ya con el proceso de "
                                   u"subida de ficheros contemplados "
                                   u"en «{}» a Wikimedia Commons en "
                                   u"el punto indicado, o bien «REINICIAR» "
                                   u"si desea eliminar la sesión guardada "
                                   u"y comenzar todo el proceso de subida "
                                   u"desde el principio."
                                   u"\n".format(cfg["nombreCsv"]))
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
                                        u"para «{}» e iniciar el proceso "
                                        u"de nuevo?".format(cfg["nombreCsv"]))
                                if sn(preg):
                                    abilog.debug(u"Se confirma.")
                                    print
                                    abilog.info(u"Se han borrado "
                                                u"todos los progresos "
                                                u"para "
                                                u"«{}».".format(cfg["nombreCsv"]))
                                    abilog.info(u"Se empezará de cero.")
                                    ifila = 0
                                    guardar_fila(cfg,0)
                                    desconocido = False
                                else:
                                    abilog.debug(u"No se confirma.")
                else:
                    ifila = 0
                    if INTERACTIVO:
                        print (u"\nEscriba «COMENZAR» si ha revisado "
                               u"concienzudamente la información del "
                               u"fichero «{}» y quiere iniciar ya el "
                               u"proceso de subida de los archivos "
                               u"multimedia contemplados a Wikimedia "
                               u"Commons.\n".format(cfg["nombreCsv"]))
                        abilog.debug(u"Se pide la escritura de "
                                     u"«COMENZAR».")
                        comenzar = False
                        while not comenzar:
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
                       U"ABRIR.".format(cfg["nombreCsv"]))
                print (u"HACERLO DERIVARÁ EN UN COMPORTAMIENTO "
                       u"IMPREDECIBLE, Y USTED, OPERADOR, SE HARÁ "
                       u"RESPONSABLE DE TODOS LOS DAÑOS "
                       U"OCASIONADOS.")
                print (u"SI VERDADERAMENTE NECESITA EFECTUAR ALGUNA "
                       u"MODIFICACIÓN A PARTIR DE AHORA, EXPONGA LA "
                       u"SITUACIÓN EN UN CORREO ELECTRÓNICO DIRIGIDO "
                       u"A <{}>. GRACIAS.\n".format(correoAyuda))
                print '#' * 80
                print
                if INTERACTIVO:
                    time.sleep(10)
                bucle(cfg,datos,ifila)
                fin(cfg)

if __name__ == '__main__':
    main()
