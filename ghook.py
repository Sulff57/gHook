# This Python file uses the following encoding: utf-8

import es, gamethread, os, playerlib, popuplib, ConfigParser

from math import sqrt


info = es.AddonInfo()
info.name = "gHook" 
info.version = "1.06"
info.author = "Sulff" 
info.url = "www.team-tocs.com"

es.ServerVar('gHook', info.version, 'grapple server').makepublic()

# default config #

var_list = {'push_delay': 0.4, 'distance_hook': 400, 'speed_hook': 600, 'minimal_speed': 0.4, 'air_accelerate': 100}
hook_mode = 1

##################


player_delay = {}

map_file = None

global map_file, hook_mode

global lock_freezetime
lock_freezetime = True

def player_activate(ev):
	userid = ev['userid']
	player_delay[userid] = False

        popuplib.send('welcome_popup', userid)


def create_welcome_popup():
        global welcome_popup

        welcome_popup = popuplib.create('welcome_popup')
        welcome_popup.addline("Welcome. This server is using gHook %s."%info.version)
        welcome_popup.addline('You can use a grapple by binding any key to "+ghook".')
        welcome_popup.addline('Example : type Bind f "+ghook" in your console,')
        welcome_popup.addline('Then press F to use it.')


        
def load():
        global freezetime
        freezetime = es.ServerVar('mp_freezetime') # sert à désactiver le hook pendant le freezetime
    
        if not es.exists('clientcommand', '+ghook'): # on enregistre le bind ghook pour créer une touche pour le grappin
                es.regclientcmd('+ghook', 'ghook/hookon', 'push on')
                es.regclientcmd('-ghook', 'ghook/hookoff', 'push off')

        if not es.exists('saycommand', 'test'):
                es.regsaycmd('!ghook', 'ghook/send_menu', 'menu principal')

        create_welcome_popup()

        
def unload():
    if es.exists('clientcommand', '+ghook'):
        es.unregclientcmd('+ghook')
        es.unregclientcmd('-ghook')

    if es.exists('saycommand', '!ghook'):
        es.unregsaycmd('!ghook')
        
def load_config():
        global hook_mode, map_file

        map_file = es.ServerVar('eventscripts_gamedir') + '//' + 'maps' + '//' + es.ServerVar("eventscripts_currentmap") + '.cfg'
        
        config = ConfigParser.ConfigParser()
        
        if not os.path.isfile(map_file) :
                 generate_config_file()
                
        else:
                config.readfp(open(map_file))
        
                hook_mode = config.getint('ChoixMode', 'hook_mode')


        load_config_map(map_file)
        


def generate_config_file():
        global map_file, hook_mode

        
        config = ConfigParser.ConfigParser()
        
        config.add_section('ChoixMode')
        config.add_section('ConfigMode1')
        config.add_section('ConfigMode2')

        config.write(open(map_file, 'w'))



        for x in var_list:
                if hook_mode == 1:
                        config.set('ConfigMode1', x, var_list[x])
                        config.set('ConfigMode1', 'minimal_speed', var_list['minimal_speed'])
                else:
                        config.set('ConfigMode2', x, var_list[x])

        config.write(open(map_file, 'w'))
                


        
     
def load_config_map(file):
        
        if hook_mode == 1:

                read_cfg(file, 'ConfigMode1')
        elif hook_mode == 2:
                read_cfg(file, 'ConfigMode2')      

        es.server.queuecmd("sv_airaccelerate %s"%var_list['air_accelerate'])
        
def read_cfg(file, section): 

        config = ConfigParser.ConfigParser()
        config.readfp(open(file))
        
        for x in var_list:
                if (section == 'ConfigMode1') or ((section == 'ConfigMode2') and (x != 'minimal_speed')) : # on ne charge pas la valeur minimal_speed qui n'existe pas dans la section 2
                        var = config.getfloat(section, x)
                        if var:
                                var_list[x] = var

                        
                
        
def es_map_start(ev):
        global beam, map_file
        beam = es.precachemodel("cable/rope.vmt")
        

        
        gamethread.delayed(10, load_config)
        
        
def round_start(ev):
        global lock_freezetime
        lock_freezetime = True
        gamethread.delayed(float(freezetime), enable_freezetime)
    
def hookon():
	userid = str(es.getcmduserid())
	player_team = es.getplayerteam(userid)
	player = playerlib.getPlayer(userid)

	if (player_team == 2) or (player_team == 3): # si le joueur est terro (2) ou ct (3)
		if (player_delay[userid] == False) and (lock_freezetime == False) and (player.isdead == False): # et qu'il n'a pas rehook trop vite 
                        player_delay[userid] = True # on met la protection hook et on lance le reste
			
			gamethread.delayed(var_list['push_delay'], enable_hook, userid) # on lance un timer pour le déblocage du hook
			# mettre un son
			location_aim = ViewCoord(userid) # coordonnées du point visé
			location_aim = location_aim.split(",")
			x2, y2, z2 = location_aim
			x2, y2, z2 = float(x2), float(y2), float(z2)
			location_aim = x2, y2, z2
			
			x, y, z = es.getplayerlocation(userid) # coordonnées du joueur
			
			iscrouch = es.getplayerprop(userid, "CBasePlayer.m_fFlags") # on ajuste les coordonnées selon la hauteur du joueur (accroupi ou non)
                        if int((iscrouch) == 66179):
                                z += 20
                        else:
                                z += 60

                        location_player = (float(x), float(y), float(z))
			
			distance = CalcDistance(location_aim, location_player)
			if distance[0] > var_list['distance_hook']:
				ratio_difference = distance[0] / var_list['distance_hook'] # on calcule un ratio pour savoir de combien on dépasse

				X = location_player[0] + distance[1]/ratio_difference
				Y = location_player[1] + distance[2]/ratio_difference
				Z = location_player[2] + distance[3]/ratio_difference

				es.effect("energysplash", "%s,%s,%s"%(X, Y, Z), "%s,%s,%s"%(X, Y, Z+60), 0) # on draw un point d'impact dans le vide
				es.effect("beam", "%s,%s,%s"%(X, Y, Z), "%s,%s,%s"%(location_player[0], location_player[1], location_player[2]), beam, beam, 0, 0, 0.3, 1, 1, 1, 1, 255, 255, 255, 255, 200)
			else:
                                a, b, c = tuple([es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[%s]'%x) for x in range(3)]) # on prend la vélocité avant hook du joueur
				force = (a)**2 + (b)**2
				force = sqrt(force) # on calcule le vecteur des axe X et Y

				speed_variation = (int(force/3)) # variable qui va servir à ajuster la vitesse du hook visuel
				if speed_variation > 255:
                                        speed_variation = 255
				color_variation = 255 - speed_variation
				if speed_variation < 60:
                                        speed_variation = 60
				
                                force = float(force)/float(var_list['speed_hook']) # on module selon la puissance désirée dans la config
				bump = var_list['speed_hook'] / 3 # on ne rend pas la puissance du saut variable selon la vélocité du joueur, on module seulement selon la puissance du hook

				
				if force < var_list['minimal_speed']: # on regarde si le ratio/indicateur force est inférieur au minimum configuré
                                        force = var_list['minimal_speed']  # pour le mettre à niveau si nécessaire
                                
				k = var_list['speed_hook']/distance[0]
                                
                                es.effect("energysplash", "%s,%s,%s"%(location_aim[0], location_aim[1], location_aim[2]), "%s,%s,%s"%(location_aim[0], location_aim[1], location_aim[2]+60), 0) # on draw un point d'impact dans le vide

                                if hook_mode == 1:
                                        es.effect("beam", "%s,%s,%s"%(location_aim[0], location_aim[1], location_aim[2]), "%s,%s,%s"%(location_player[0], location_player[1], location_player[2]), beam, beam, 0, 0, 0.3, 1, 1, 1, 1, 255, color_variation, color_variation, 255, speed_variation)
                                        es.setplayerprop(userid, 'CBasePlayer.localdata.m_vecBaseVelocity', "%s,%s,%s"%((-a+(distance[1]*(k)))*force*var_list['minimal_speed'], (-b+(distance[2]*(k)))*force*var_list['minimal_speed'], -c+(distance[3]*k)+force*250))
                                else:
                                        es.effect("beam", "%s,%s,%s"%(location_aim[0], location_aim[1], location_aim[2]), "%s,%s,%s"%(location_player[0], location_player[1], location_player[2]), beam, beam, 0, 0, 0.3, 1, 1, 1, 1, 255, 255, 255, 255, 175)
                                        es.setplayerprop(userid, 'CBasePlayer.localdata.m_vecBaseVelocity', "%s,%s,%s"%(-a+(distance[1]*(k)), -b+(distance[2]*(k)), -c+(distance[3]*(k))+bump))
			
			
def CalcDistance(location_end, location_start): # on calcule la distance (en game units) entre les 2 points
					
	X = location_end[0] - location_start[0]
	Y = location_end[1] - location_start[1]
	Z = location_end[2] - location_start[2]
	
	distance = X**2 + Y**2 + Z**2
	distance = (sqrt(distance), X, Y, Z)
	
	return distance
        # retourne une variable dictionnaire contenant :
        # la distance totale pour le vecteur
        # la distance entre chaque point de coordonnée
			
def ViewCoord(userid): # méthode pour avoir la location de l'endroit visé sans bug
    es.server.cmd('es_xprop_dynamic_create %s props_c17/tv_monitor01_screen.mdl' % userid)
    lastgive = es.ServerVar('eventscripts_lastgive')
    location = es.getindexprop(lastgive, 'CBaseEntity.m_vecOrigin')
    es.server.queuecmd('es_xremove ' + lastgive)
    return location
			
def enable_hook(userid):
	player_delay[userid] = False

def enable_freezetime():
        global lock_freezetime
	lock_freezetime = False

        


