import os
import requests
from lxml import html
import easygui
from easygui import *
import configparser
import sys
from sys import exit
from zipfile import ZipFile
import random
import string
import shutil
import win32api, win32con
import gettext


def getCurrentPath():
    # determine if application is a script file or frozen exe
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)
    if (len(application_path)==0):
        application_path = os.path.realpath(".")
    print("NVM app Path: ", application_path)
    return application_path


#Configuration de l'outil
cheminCourant = getCurrentPath()
config = configparser.ConfigParser()
FICHIER_CONFIG = cheminCourant+"/config.ini"
DIR_APPLI = "nvmEnvs"
SUB_DIR = "nodeJSNVMEnvs"
TEMP_DIR = "tempsNVM"
VIRTUAL_ENV_DIR = "VirtualNVMEnv"

versionsDispo = None #tableau contenant les versions disponibles sur le site NodeJS (limité aux versions >=v7)


def sauveConfig():
    with open(FICHIER_CONFIG, 'w') as configfile:
        config.write(configfile)

def getConfig():
    global _
    global config

    if (os.path.exists(FICHIER_CONFIG)):
        config.read(FICHIER_CONFIG)
        langue = config["NVM"]["langue"]
        if (langue == "English"):
            en = gettext.translation('base', localedir=cheminCourant+'/locales', languages=['en'])
            en.install()
            _ = en.gettext
        else:
            _ = gettext.gettext
        #Verification que l'env actif est toujours présent...
        if (config["NVM"]["versioncourante"] != ""):
            if (not os.path.exists(config["NVM"]["dirInstallNodeJS"] + "\\" + config["NVM"]["versioncourante"])):
                config["NVM"]["versioncourante"]=""
    else:
        #Nouvelle installation
        msg = "Configuration de la langue/language configuration"
        choices = ["English", "Francais"]
        langue = buttonbox(msg=msg, title="[NVM] Configuration", choices=choices)
        if (langue == None):
            langue = "Francais"
        if (langue == "English"):
            en = gettext.translation('base', localedir=cheminCourant+'/locales', languages=['en'])
            en.install()
            _ = en.gettext
        else:
            _ = gettext.gettext

        informationUser(_("[NVM] Information"),
                        _("La configuration est introuvable.\nVous allez maintenant configurer NVM.\nCliquez sur OK puis choisissez l'architecture de votre OS puis donnez le répertoire dans lequel NVM installera les versions de NodeJS (un répertoire sera créé à cet endroit).\nPrivilégiez un répertoire dédié aux versions de NodeJS"))

        msg = _("Quelle architecture Windows possédez-vous ?")
        choices = ["x86", "x64"]
        replyArchi = buttonbox(msg=msg, title=_("[NVM] Installation"), choices=choices)
        if (replyArchi == None):
            informationUser(_("[NVM] Information"),
                            _("Vous n'avez pas choisi d'architecture : ce sera x86 par défaut"))
            replyArchi = "x86"


        path = selectionneRepertoire(_('[NVM] Sélectionnez le répertoire dans lequel NVM installera les versions de NodeJS (un répertoire sera créé à cet endroit)'))
        if (path == None):
            informationUser(_("[NVM] Information"),_("Vous n'avez pas choisi de répertoire.. NVM ne peut pas continuer...."))
            exit(-5)
        else:
            #Create the subdirs

            newPath0 = path + "\\" + DIR_APPLI
            if (not os.path.exists(newPath0)):
                try:
                    os.mkdir(newPath0)
                except OSError as err:
                    informationUser(_("[NVM] Erreur"),
                                    _("Création du répertoire ") + newPath0 + _(" échouée\n(raison:") + err.strerror + ")")
                    exit(-10)
            newPath1 = newPath0+"\\"+SUB_DIR
            if (not os.path.exists(newPath1)):
                try:
                    os.mkdir(newPath1)
                except OSError as err:
                    informationUser(_("[NVM] Erreur"),
                                    _("Création du répertoire ")+newPath1+_(" échouée\n(raison:")+err.strerror+")"  )
                    exit(-10)
            newPath2 = newPath0 + "\\" + TEMP_DIR
            if (not os.path.exists(newPath2)):
                try:
                    os.mkdir(newPath2)
                except OSError as err:
                    informationUser(_("[NVM] Erreur"),
                                    _("Création du répertoire " )+ newPath2 + _(" échouée\n(raison:") + err.strerror + ")")
                    exit(-10)
        config['NVM'] = {"langue":langue,"versionCourante":"", "rootDir":newPath0, "dirInstallNodeJS": newPath1, "archi":replyArchi, "dirTemps":newPath2, "virtualEnv":newPath0+"\\"+VIRTUAL_ENV_DIR}
        sauveConfig()
        #Ajoute la variable d'environnement si elle n'existe pas déjà (PATH)
        addVariableEnv()

def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


def informationUser(titre, contenu):
    msgbox(title=titre, msg=contenu)

def supprimeVersion(vInstallees):
    msg = _("Choisir la version de NodeJS à supprimer")
    title = _("Choisir une version à supprimer")
    listeDispo = []
    for v in vInstallees:
        valeur = v;
        if (valeur ==  config["NVM"]["versionCourante"]) :
            valeur = valeur + _(" ** activée")
        listeDispo.append(valeur)
    if (len(listeDispo)<2):
        listeDispo.append(_("Aucune..."))

    choice = choicebox(msg, title, listeDispo)

    if (choice != _("Aucune...")):
        if (choice.endswith(_(" ** activée"))):
            choice = choice[:choice.index(_(" ** activée"))]
            desactiverNVM()
        if (os.path.exists(config["NVM"]["dirInstallNodeJS"] + "\\" + choice)):
            shutil.rmtree(config["NVM"]["dirInstallNodeJS"] + "\\" + choice)
        #vInstallees.remove(choice) - Inutile car chargement a chaque affichage du menu pour éviter les pb (modifs rep)

def activeVersion(vInstallees):
    msg = _("Choisir la version de NodeJS à activer via NVM")
    title = _("Choisir une version à activer")
    listeDispo = []
    for v in vInstallees:
        valeur = v;
        if (valeur ==  config["NVM"]["versionCourante"]) :
            valeur = valeur + _(" ** activée")
        listeDispo.append(valeur)
    listeDispo.append(_("Aucune/désactiver"))

    choice = choicebox(msg, title, listeDispo)
    if (choice != None):
        if (choice == _("Aucune/désactiver")):
            desactiverNVM()
        else:
            if (choice.endswith(_("** activée"))):
                choice = choice[:choice.index(_(" ** activée"))]
            if (os.path.exists(config["NVM"]["dirInstallNodeJS"] + "\\" + choice)):
                activerNVM(choice)

def desactiverNVM():
    if (os.path.exists(config["NVM"]["virtualenv"])):
        os.remove(config["NVM"]["virtualenv"])
        config["NVM"]["versionCourante"] = ""
        sauveConfig()


def activerNVM(env):
    if (os.path.exists(config["NVM"]["virtualenv"])):
        os.remove(config["NVM"]["virtualenv"])
    creerLienSymbolique(env)
    config["NVM"]["versionCourante"] = env
    sauveConfig()


def menu():
    global versionsDispo
    getConfig()
    #Vérifie les répertoires installés
    versionInstallees = getListInstallations()
    if (versionsDispo == None): #ON les charge une seule fois par execution...
        versionsDispo = chargeVersionsList()
    msg = _("Menu principal.. (")+config["NVM"]["archi"]+")"
    if (len(config["NVM"]["versionCourante"])>0):
        msg = msg + _(" Version activée :")+config["NVM"]["versionCourante"]
    img = cheminCourant+"/img/logo.png"
    choices = [_("Installer une version NodeJS")]
    if (len(versionInstallees)>0):
        choices.append(_("Modifier la version de NodeJS active"))
        choices.append(_("Supprimer une version"))
    if (len(config["NVM"]["versionCourante"])>0):
        choices.append(_("Désactiver NVM"))
    choices.append(_("Quitter"))

    replyMenu = buttonbox(title="[NVM] Menu (v0.8) 08/2020", msg=msg, choices=choices, image=img)
    if (replyMenu == None or replyMenu == _("Quitter")):
        exit(0)
    else:
        if (replyMenu == _("Installer une version NodeJS")):
            installNewVersion(versionsDispo, versionInstallees)
        if (replyMenu == _("Modifier la version de NodeJS active")):
            activeVersion(versionInstallees)
        if (replyMenu == _("Désactiver NVM")):
            desactiverNVM()
        if (replyMenu == _("Supprimer une version")):
            supprimeVersion(versionInstallees)

def selectionneRepertoire(title):
    path = easygui.diropenbox(title=title)
    #print(path)
    return path

def telechargeFichier(url, directory) :
  localFilename = url.split('/')[-1]
  prev = -1
  with open(directory + '/' + localFilename, 'wb') as f:
    r = requests.get(url, stream=True)
    total_length = int(r.headers.get('content-length'))
    dl = 0
    if total_length is None: # no content length header
      f.write(r.content)
    else:
      for chunk in r.iter_content(1024):
        dl += len(chunk)
        f.write(chunk)
        done = int(50 * dl / total_length)
        if (prev != done):
            sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50-done)))
            prev = done


def dezipper(file, dest):
    with ZipFile(file, 'r') as zip:
        # afficher tout le contenu du fichier zip
        #zip.printdir()
        # extraire tous les fichiers du zip
        print("\n",_("extraction de l'archive dans le répertoire %s") % config["NVM"]["dirInstallNodeJS"])
        zip.extractall(path=dest)
        print(_('\nExtraction terminée...'))

def chargeDownloads(url, versionChoisie, dir):
     #Charge les liens de téléchargement
    page = requests.get(url, allow_redirects=True)
    tree = html.fromstring(page.content)
    liens = tree.xpath("//a/@href")
    versions=[]
    for lien in liens:
         versionOK = False
         if (lien.startswith("node-v"+versionChoisie+"-win") and lien.endswith(".zip")):
                try:
                    if (lien.index(config["NVM"]["archi"])>=0):
                        versionOK = True
                except:
                    versionOK = False
         if (versionOK):
            versions.append(lien)
    # Pour le retour > indique le nom de l'environnement créé (par défaut inexistant...)
    nomEnv = None

    if (len(versions) == 0):
        informationUser(_("[NVM] Erreur"), _("La version choisie n'est pas compatible avec cet outil NVM\Il n'y a pas d'archives pour windows compatible !"))
    else:
        fic = versions[0]
        nomRep = fic[:fic.index(".zip")]
        nomEnv = versionChoisie
        reply = None
        if (os.path.exists(config["NVM"]["dirInstallNodeJS"] + "\\" + versionChoisie)):
            msg = _("Un environnement avec le même nom existe déjà (")+versionChoisie+_(").. \r Voulez-vous supprimer l'ancien, annuler l'installation ou renommer le nouvel environnement ?")
            choices = [_("Supprimer"), _("Renommer"), _("Annuler")]
            reply = buttonbox(msg=msg, title="[NVM] Attention", choices=choices)
            if (reply != _("Annuler")):
                if (reply == _("Supprimer")):
                    print(_("Chargement en cours.... Veuillez patienter !"))
                    shutil.rmtree(config["NVM"]["dirInstallNodeJS"] + "\\" + versionChoisie)
                else:
                    if (reply == _("Renommer")):
                        msg = _("Donner le nom de l'environnement souhaité")
                        title = _("[NVM] Renommer l'environnement à installer")
                        fieldNames = [_("Nom")]
                        fieldValues = [versionChoisie+"_"+get_random_string(8)]  # we start with blanks for the values
                        retour = multenterbox(msg, title, fieldNames, fieldValues)
                        nomEnv = retour[0]
            else:
                nomEnv = None
        if (reply == None or reply != _("Annuler")):
            telechargeFichier(url + "/" + fic, dir)
            dezipper(dir + '\\' + fic, config["NVM"]["dirtemps"])
            os.rename(config["NVM"]["dirtemps"] + "\\" + nomRep, config["NVM"]["dirInstallNodeJS"] + "\\" + nomEnv)
            os.remove(dir+"\\"+fic)
    return nomEnv

def chargeVersionsList():
    print ("Loading...")
    #CHarge la liste des versions disponibles sur le site
    versionArray = {}
    url = 'https://nodejs.org/en/download/releases/'
    page = requests.get(url, allow_redirects=True)
    tree = html.fromstring(page.content)
    versions = tree.xpath("//table[@class='download-table full-width']/tbody/tr")
    #print (versions)
    for version in versions:
        ok = True
        #Création d'un dictionnaire
        contenu = {}
        for id in version:
            if ("data-label" in id.attrib):
                if (id.attrib["data-label"]=="Date"):
                    contenu[id.attrib["data-label"]] = id[0].text
                else:
                    if (id.attrib["data-label"] == "Version"):
                        if (id.text.startswith("Node")):
                            vv = id.text[id.text.index(' ')+1:]
                            vv = int(vv[:vv.index(".")])
                            if (vv >= 7):
                                contenu[id.attrib["data-label"]] = id.text[id.text.index(' ')+1:]
                            else:
                                ok = False
                        else:
                            ok = False
                    else:
                        contenu[id.attrib["data-label"]] = id.text

            if ("class" in id.attrib and id.attrib["class"]=="download-table-last"):
                contenu["href"]= id[0].attrib["href"]
        if (ok == True):
            versionArray[contenu["Version"]] = contenu
    return  versionArray

def getListInstallations():
    liste = (os.listdir(config["NVM"]["dirInstallNodeJS"]))
    return liste

def choisirVersion(versionsDispo, versionsInstallees):
    listeV = []
    chaine = ""
    #print (versionsInstallees)
    for v in versionsDispo:
        item = versionsDispo[v]
        chaine = v + " ("
        if (item["npm"] != None):
            chaine = chaine + "NPM = " + item["npm"] + ", "
        if (item["LTS"] != None):
            chaine = chaine + "LTS = " + item["LTS"] + ", "
        chaine = chaine + item["Date"] + ")"
        listeV.append(chaine)

    msg = _("Choisir la version de NodeJS que vous souhaitez installer - La vérification de la compatibilité avec NVM sera faite ensuite")
    title = _("Choisir une version à installer")
    choice = choicebox(msg, title, listeV)
    #Extraction de la version uniquement
    if (choice != None):
        choice = choice[:choice.index(' ')]
    return choice

def creerLienSymbolique(nomEnv):
    os.system("mklink /D /J "+config["NVM"]["virtualenv"]+" "+config["NVM"]["dirinstallnodejs"]+"\\"+nomEnv)

def installNewVersion(vDispos, vInstallees):
    version = choisirVersion(vDispos, vInstallees)
    if (version != None):
        env = chargeDownloads(vDispos[version]["href"], version, config["NVM"]["dirtemps"])
        if (env != None):
            if (len(vInstallees) == 0): #1ere installation on créé le lien symbolique
                creerLienSymbolique(env)
                config["NVM"]["versionCourante"] = env
                sauveConfig()
            #vInstallees.append(env) - Inutile car chargement a chaque affichage du menu pour éviter les pb (modifs rep)
    else:
        informationUser(_("[NVM] Erreur"), _("Vous n'avez pas choisi de version à installer..."))

def addVariableEnv():
    pathActuel = os.getenv('PATH')
    #print(pathActuel)
    try:
        indice = pathActuel.index(config["NVM"]["virtualEnv"])
        print ("OK")
    except:
        print ("Adding the environment variable....")
        script = cheminCourant+"\\install.bat"
        win32api.ShellExecute(None, "runas", script, config["NVM"]["virtualEnv"], None, win32con.SW_SHOWNORMAL);
        informationUser(_("[NVM] Information"), _("Les variables d'environnement ont été modifiées, relancer l'application..."))
        exit(0)


# Main...
if __name__ == '__main__':
    if (len(sys.argv)>1) :

        print("NVM shell Parameters: \non [env] --->  activate [env]\noff desactivate NVM\n\n")
        getConfig()
        args =  sys.argv[1:]
        if (len(args)==2 and args[0]=="on"):
            #Vérifie si le répertoire donné de l'env existe..
            nomEnv = args[1].strip()
            if (not os.path.exists(config["NVM"]["dirinstallnodejs"]+"\\"+nomEnv)):
                    print("NodeJS env ",config["NVM"]["dirinstallnodejs"]+"\\"+nomEnv,"not found/non trouvé..")
            else:
                activerNVM(nomEnv)
                print("NVM on: ", nomEnv)
        else:
            if (args[0] == "off" and len(args)==1):
                desactiverNVM()
                print("NVM off")
    else:
        while (True):
            menu()
