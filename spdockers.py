#!/usr/bin/python
# -*- coding: latin-1 -*-

import platform
import os
import time
import fnmatch
import socket
import sys
from subprocess import call
import subprocess
import shlex
import urllib, urllib2
import xml.etree.ElementTree as ET
import zipfile
import shutil
import sys, tty, termios # para capturar una tecla

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[31m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

FILE_CONFIGURACION="https://raw.githubusercontent.com/Mecool-KX/SpufyDockers/master/config.xml"
NOMBRE_CFG="config.txt"
CARPETA_DESCARGA="/tmp/"
CARPETA_SCRIPTS="/storage/.config/scripts/dockers/"
TIEMPO_MINIMO=3 # Tiempo mínimo en un script para no pedir una pausa

SI = ['1', 'true', 's', 'y', 'si', 'yes']

dockers=""

def main(argv):  
	sys.tracebacklimit = 0
	opcion=1 # para que entre al menu

	#Chequeamos SO
	check_SO()

	# Comprobamos si tenemos internet
	comprueba_internet()

	# Comprobamos si está instalado docker
	if argv[0] != "-NOCHECK": check_docker()

	# Leemos la configuración de dockers a instalar
	descarga_lee_XML()

	while opcion:
		# Lanzamos el menú para elegir opción
		opcion=lanza_menu()
		
		# Instalamos y/o ejecutamos la opción que corresponda
		instala_ejecuta(opcion)
	
	os.system('clear')
	
	sys.exit(0)
	
def descarga_fichero(url, fichero):
	"""
		Función para descargar un fichero donde nos digan
	"""
#	try:
	urllib.urlretrieve(url, fichero, reporthook)
	print ""
	return True
#	except:
#	mostrar_error ("Error al descargar el fichero: " + url)
#	return False

def reporthook(count, block_size, total_size):
    global start_time
    if count == 0:
        start_time = time.time()
        return
    duration = time.time() - start_time
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * duration))
    percent = int(count * block_size * 100 / total_size)
    sys.stdout.write("\t\r%d KB/s, %d/%d MB, %d%%" %
                    (speed, progress_size / (1024 * 1024), total_size / (1024 * 1024), percent))
    sys.stdout.flush()
	
def instala_ejecuta(opcion):
	"""
		Descargamos y/o ejecutamos el script que corresponda
	"""

	if opcion:  # No quiere salir
		cabecera()
		if opcion == len(dockers)+1: borrar_dockers(); return # Quieren borrar todos los dockers
		if not docker_descargado(dockers[opcion-1].get('nombre')):
			# Tenemos que descargar el docker, descomprimirlo y dar permisos al .sh
			
			# Borramos el fichero .zip si existe
			borrar_fichero(CARPETA_DESCARGA + dockers[opcion-1].get('nombre') + ".zip")
	
			# Creamos la carpeta donde se tiene que descomprimir el .zip
			crear_carpeta(CARPETA_SCRIPTS + dockers[opcion-1].get('nombre') + "/")
	
			# Descargamos el zip
			#pause (dockers[opcion-1].get('nombre') + " - " + dockers[opcion-1].find('link').text)
			mostrar_mensaje("Descargamos docker: " + dockers[opcion-1].get('nombre') + "\n", bcolors.OKGREEN)
			descarga_fichero(dockers[opcion-1].find('link').text, CARPETA_DESCARGA + dockers[opcion-1].get('nombre') + ".zip")
	
			# Descomprimimos el fichero descargado
			mostrar_mensaje("Descomprimimos docker", bcolors.OKGREEN)
			descomprime_zip(CARPETA_DESCARGA + dockers[opcion-1].get('nombre') + ".zip", CARPETA_SCRIPTS + dockers[opcion-1].get('nombre') + "/")
	
			# Borramos el fichero .zip si existe
			borrar_fichero(CARPETA_DESCARGA + dockers[opcion-1].get('nombre') + ".zip")

			# Damos los permisos de ejecución a los ficheros .sh del docker
			ficheros_permisos(ficheros_pattern(CARPETA_SCRIPTS + dockers[opcion-1].get('nombre') + "/", "*.sh"))

		# Mostramos la información disponible del docker antes 
		try: # Para que no de error si el campo info está vacío
			mostrar_informacion("" if (dockers[opcion-1].find('info').text).encode('utf-8') is None else (dockers[opcion-1].find('info').text).encode('utf-8'))
		except:
			pass

		# Ya está descargado. Tenemos que ejecutarlo
		mostrar_mensaje ("Ejecutamos el docker", bcolors.OKGREEN)
		
		start_time=time.time()
		lanza_sh(CARPETA_SCRIPTS + dockers[opcion-1].get('nombre'), dockers[opcion-1].find('ssh').text)
		if (time.time() - start_time) <= TIEMPO_MINIMO: pause()

def mostrar_informacion(info):
	
	if info != "":
		cabecera()
		mostrar_mensaje("\n ¡¡¡ INFORMACIÓN IMPORTANTE !!!\n", bcolors.FAIL)
		mostrar_mensaje("\t" + info, bcolors.OKGREEN)
		pause(" ")

def borrar_dockers():
	"""
		Borramos la carpeta CARPETA_SCRIPTS
	"""
	if pregunta_sino("¿Quieres borrar todos los dockers?"): shutil.rmtree(CARPETA_SCRIPTS, ignore_errors=True)

def pregunta_sino(mensaje):
	"""
		función para preguntar si o nombre
	"""
	while True:
		#opcion = raw_input("\n    %s (%s) " % (mensaje, "S/N")).lower()
		print ("\n    " + mensaje + "(S/N)")
		opcion = coge_caracter().lower()
		
		if opcion == "s": return True
		elif opcion == "n": return False
		else: pause("Opción no válida. Pulsa una tecla para continuar")

def crear_carpeta(carpeta):
	"""
		creamos la carpeta que nos digan
	"""
	if not os.path.exists(carpeta): os.makedirs(carpeta) # Crea todas las carpetas intermedias hasta la última que pongas

def borrar_fichero(fichero):
	"""
		Borramos el fichero que nos pasen por parámetro
	"""
	# Borramos el fichero .zip si existiera en local
	if os.path.exists(fichero): os.remove(fichero)

def descomprime_zip(fichero, destino):
	"""
		Descomprimimos el fichero .zip que corresponda en el destino (con nombre de fichero) que nos pasen
	"""
	try:
		# Descomprimimos el fichero descargado
		with zipfile.ZipFile(fichero, "r") as file:
			file.extractall(destino)
	except:
		#Borramos la carpeta del docker
		shutil.rmtree(destino, ignore_errors=True)
		mostrar_error ("Error al descomprimir: " + fichero)

def descarga_lee_XML():
	"""
		Leemos la configuración de Github
	"""

	global dockers
	
	try:
		os.remove(CARPETA_DESCARGA + NOMBRE_CFG)
	except:
		pass

	# Descargamos y parseamos el fichero de configuración
	dockers = ET.fromstring(urllib2.urlopen(FILE_CONFIGURACION).read())

	# Borramos del arbol los dockers que no esten habilitados
	for docker in dockers:
		if not (docker.find('enable').text).lower() in SI: dockers.remove(docker) 

def docker_descargado(docker):
	"""
		Comprueba si el docker está ya instalado
	"""
	return True if os.path.exists(CARPETA_SCRIPTS + docker) else False

def ficheros_pattern(carpeta, pattern):
	"""
		devuelve una tabla con los ficheros que cumplan el pattern pasado
	"""
	tabla = fnmatch.filter(os.listdir(carpeta), pattern) # ficheros sin path que cumplen el pattern

	for x, fichero in enumerate(tabla):
		tabla[x] = carpeta + fichero

	return tabla
	

def ficheros_permisos(ficheros, permisos=0777):
	"""
		Asignamos permisos de ejecución al fichero que nos pasen por parámetro
	"""
	for fichero in ficheros:
		# Asignamos permisos de ejecución
		print (fichero)
		os.chmod(fichero, permisos)


def lanza_menu():
	"""
		Lanzamos el menú para elegir opción
	"""
	loop=True
	while loop:          ## While loop which will keep going until loop = False
		caracter=""
		print_menu()    ## Muestra menú
		try:
			opciones=len(dockers) if not os.path.exists(CARPETA_SCRIPTS) else (len(dockers)+1)
			#choice = raw_input("    Elige opción " + bcolors.FAIL + "[0-" + str(opciones) + "]" + bcolors.ENDC + ": ")
			print ("    Elige opción " + bcolors.FAIL + "[0-" + str(opciones) + "]" + bcolors.ENDC + ": ")
			caracter = coge_caracter()
		except KeyboardInterrupt:
			os.system('clear')
			sys.exit()
		if caracter.isdigit() and int(caracter) >=0 and int(caracter)<=opciones: 
			#pause (dockers[caracter-1].get('nombre'))
			#pause ( dockers[caracter-1].find('link').text)
			caracter=int(caracter)
			loop=False
#		elif caracter==0:
#			loop=False
			## You can add your code or functions here
		else:
			# Any integer inputs other than values 1-5 we print an error message
			pause(bcolors.FAIL + "\n\tOpción incorrecta: " + caracter + " Pulsa una tecla para continuar.." + bcolors.ENDC)
	return caracter

def print_menu():       ## Your menu design here
	"""
		Pintamos el menu
	"""

	cabecera()
	for x, child in enumerate(dockers): # files are iterable
		print "\t" + bcolors.OKGREEN + str(x+1) + ". " + ("Descargar y ejecutar " if not docker_descargado(child.get('nombre')) else "Ejecutar ") + child.get('nombre') + bcolors.ENDC + "\n\t   (" + (dockers[x].find('desc').text).encode('utf-8') + ")\n"
	print
	if os.path.exists(CARPETA_SCRIPTS): print "\t" + bcolors.OKGREEN + str(len(dockers)+1) + ". " + "Borrar TODOS los dockers\n"
	print "\t" + bcolors.OKGREEN + "0. Salir\n" + bcolors.ENDC

def coge_caracter():
	"""
		Cogemos un caracter de stdin
	"""
	fd = sys.stdin.fileno()
	old_settings = termios.tcgetattr(fd)
	try:
		tty.setraw(sys.stdin.fileno())
		ch = sys.stdin.read(1)
	finally:
		termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
	return ch

def cabecera():
	"""
		Cabecera del script
	"""
	os.system('clear')

	print bcolors.OKBLUE + \
		  "┌────────────────────────────────────────────────────────────────────┐"
	print "│  _____              __         _____             _                 │"
	print "│ / ____|            / _|       |  __ \           | |                │"
	print "│| (___  _ __  _   _| |_ _   _  | |  | | ___   ___| | _____ _ __ ___ │"
	print "│ \___ \| '_ \| | | |  _| | | | | |  | |/ _ \ / __| |/ / _ \ '__/ __|│"
	print "│ ____) | |_) | |_| | | | |_| | | |__| | (_) | (__|   <  __/ |  \__ \│"
	print "│|_____/| .__/ \__,_|_|  \__, | |_____/ \___/ \___|_|\_\___|_|  |___/│"
	print "│       | |               __/ |                                      │"
	print "│       |_|              |___/                                       │"
	print "│                                                                    │"
	print "│                                        https://t.me/Emby_Oficial   │"
	print "└────────────────────────────────────────────────────────────────────┘\n"  + bcolors.ENDC


def pause(texto="Pulsa una tecla para continuar"):
	"""
		Hacemos una pausa con el texto que nos pasen por parámetro
	"""

	raw_input(texto)
	
def comprueba_internet():
	"""
	Para comprobar si hay conexión a Internet
	"""
	
	if not checkinternet: 
		mostrar_error("Es necesario disponer de conexión a Internet")
	
	
def checkinternet(host="8.8.8.8", port=53, timeout=3):
	"""
	Host: 8.8.8.8 (google-public-dns-a.google.com)
	OpenPort: 53/tcp
	Service: domain (DNS/TCP)
	"""
	try:
		socket.setdefaulttimeout(timeout)
		socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
		return True
	except Exception as ex:
		print ex.message
		return False
	
def mostrar_mensaje(mensaje, color=""):
	"""
		Mostramos un mensaje en pantalla
	"""
	print "\t" + color + mensaje + bcolors.ENDC
	

def mostrar_error(mensaje):
	"""
		Mostramos error y paramos el script
	"""

	#os.system('clear')
	
	print bcolors.FAIL + mensaje + bcolors.ENDC + "\n"
	
	sys.exit(1)

def check_SO():
	"""
		Comprobamos si el SO es uno de los permitidos
	"""
	os, name, version, date, arqui, _ = platform.uname()
	
	if name != "CoreELEC":
		mostrar_error("Este script solo se puede ejecutar en CoreELEC")
		
		
def check_docker():
	"""
		Comprobamos si se encuentra Docker instalado
	"""
	if not existe_ejecutable("docker"): mostrar_error("No se encuentra instalado Docker. Instalalo desde CoreELEC - Repositorios - LinuxServer.io’s Docker Addons")

def existe_ejecutable(ejecutable):
    return any(
        os.access(os.path.join(path, ejecutable), os.X_OK) 
        for path in os.environ["PATH"].split(os.pathsep)
    )

def lanza_sh(carpeta, ssh, arg=None):
	"""
		Lanzamos el SSH con los argumentos que nos pasaen
	"""
	argumentos="" if not arg else arg[0]
	
	# Cambiamos la carpeta antes de ejecutar el script
	os.chdir(carpeta)
	
	# Lanzamos el script
	call(shlex.split('/bin/sh ' + ssh + " " + argumentos))


# this runs when the script is called from the command line
if __name__ == '__main__':  
    main(sys.argv[1:])
