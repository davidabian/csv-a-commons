#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Módulo para el registro de acciones y mensajes en ficheros de texto
#    junto a datos del entorno.
#
#    Léase acerca de la biblioteca logging
#    <https://docs.python.org/2/howto/logging.html>.
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

import logging

def config (f):
    logging.basicConfig(filename=f,\
                        level=logging.DEBUG,\
                        format='%(asctime)s %(levelname)s: %(message)s')

def debug (msj):
    logging.debug(msj)

def info (msj):
    logging.info(msj)
    print msj

def aviso (msj):
    logging.warning(msj)
    print "AVISO: %s" % msj   

def error (msj):
    logging.error(msj)
    print "ERROR: %s" % msj    
