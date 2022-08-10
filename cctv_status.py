import os
import sys
import time
import logging
import datetime
import argparse

import cv2
# import pandas as pd
# import numpy as np
from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.schedulers.blocking import BlockingScheduler
import requests
import tzlocal

from modules import camera_is_open



class KecilinLog:

	def __init__(self, args):
		self.domain 		= args.domain
		self.key 			= args.key
		self.url1 			= F"{self.domain}/api/cctv/cek-api-key/{self.key}"
		self.url2 			= F"{self.domain}/api/cctv/cek-status-api-key/{self.key}"

		self.tlg_token 		= args.tlg_token
		self.tlg_chat_id 	= args.tlg_chat_id
		self.interval_fr 	= args.interval_fr
		self.skip_cctv 		= args.skip_cctv

		self.services 		= None
		self.status_key 	= True


		print("\n\n\tKecilinLog")
		print("\tProject Name:", args.project_name)
		# print("\tAPI Key :",self.key)

	def reg_init_key(self):
		
		try:
			request = requests.get(url=self.url1)
			response = request.json()
			if response['mac_address']=='all':
				pass
			elif response['mac_address']==None:
				print("\n\tKey Baru")
				answer = input("\n\t\tTambahkan device untuk key ini? (Y/n), Answer: ")
				
				if answer == "Y" or answer == "y" or answer == "" :
					put_mac = requests.put(url=F"{self.domain}/api/cctv/put_mac/{self.key}/{gma()}")
				elif answer== "n":
					print("\texiting program")
					sys.exit() 
				else:
					print("\twrong answer")
					print("\texiting program")
					sys.exit() 
			else:
				if response['mac_address']==gma():
					pass
				else:
					print("\n\tKey telah digunakan di device lain\n\n\t\tOR")
					sys.exit() 

			# print("\n\tAPI key is valid")

		except:
			print("\n\tMaybe Api key Not valid\n\tProggram close automaticaly")
			print("\n\tCheck your connection")
			sys.exit() 

	def history_key(self):        
		
		try:
			status = requests.get(url=self.url2)
			status = status.json()

			if status['status']=='0':
				print("\n\tAPI key is not Active\n")
				return False
			elif status['expired']:
				print("\n\tAPI key is Expired or Not yet active\n")
				return False 
			else:
				
				print("\n\tAPI key is Active\n")
				return True
		except (requests.ConnectionError, requests.Timeout) as e:
			return True
		except:
			print("\n\tAPI key is Not Active\n")
			return False

	def send_notif(self, message):
		url = F'https://api.telegram.org/bot{self.tlg_token}/sendMessage?chat_id={self.tlg_chat_id}&text={message}'
		print(url)
		requests.get(url)

	def post_data_notif(self, url_api, form_data):
		try:
			req = requests.post(url_api, data=form_data)

		except:
			pass


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-pn', '--project-name', type=str, required=True, help='set Project Name') 
	parser.add_argument('-k', '--key', type=str, default='ygbyi87b7b87ygb87tbytb8iugiut76t6bgby', help='set key number') 
	parser.add_argument('-d', '--domain', type=str, default='http://api.cctv.kecilin.id', help='set domain key') 
	# parser.add_argument('-sn', '--service-name', type=str, help='set name service', default='kecilin-logs') 
	parser.add_argument('-ua','--url-api', type=str, default="http://192.168.0.233:28088", help='set url of post data') 
	parser.add_argument('-uan','--url-api-notif', type=str, default="https://gerbongkai.kecilin.id/api/notif/store", help='set url of post data for notif') 
	# parser.add_argument('-pm2', '--pm2-json', action='store_true', help='Create service pm2 config.json')
	parser.add_argument('--force-restart', '-fr', default=('0',), type=str, nargs='+', help='set id of force restart')
	parser.add_argument('-ifr', '--interval-fr', default=0, type=int, help='set interval of force restart')
	parser.add_argument('-fnl', '--fn-log', default='logs/kecilin.log', type=str, help='set file name of log')
	parser.add_argument('-sc', '--skip-cctv', default=False, action='store_true', help='hide confidences')
	parser.add_argument('-tt', '--tlg-token', type=str, default='5384978803:AAEKN30ooecrdwbfj0QDp__2ZZlMuoE54_g', help='Set Telegram token')
	parser.add_argument('-tc', '--tlg-chat-id', type=str, default='-713374553', help='Set telegram chat id')
	args = parser.parse_args()

	logging.getLogger('apscheduler.executors.default').propagate = False
	logging.getLogger('apscheduler.scheduler').propagate = False
	logging.basicConfig(filename=args.fn_log, level=logging.DEBUG)
	logging.info('Kecilin logs is started')

	kecilin_log = KecilinLog(args)
	# kecilin_log.reg_init_key()

		

	if args.interval_fr > 0:
		sched = BackgroundScheduler(daemon=True, timezone=str(tzlocal.get_localzone()))
		print('Force Restart Active')
		pm2_ids = ' '.join(list(args.force_restart))

		@sched.scheduled_job('interval', id='job_force_restart', minutes=args.interval_fr)
		def force_restart_service():
			cmd = F"pm2 restart {pm2_ids}" 
			os.system(cmd)

		sched.start()

	else:
		print('\n\nForce Restart is not Active')
	print('Log CCTV is running')
	temp_data = None
	while True:
		try:
			data_cctv = requests.get(args.url_api).json()
		except Exception as e:
			print(F'\n\n{e}')
			logging.error(F"{datetime.datetime.now()}, request to {args.url_api} is error")
			sys.exit()
		data = data_cctv['data'] 
		if temp_data is None or temp_data != data:
			temp_data = data
			for ip in data:
				jenis_kereta = ip["jenis_kereta"]
				no_sarana = ip["no_sarana"]
				channel = 1
				for link in ip["rtsp"]:
					cap = cv2.VideoCapture(link)
					time.sleep(15)


					loop_time = 1
					while cap.isOpened():
						success, frame = cap.read() 
						if success:
							if not camera_is_open(frame, 100):
								logging.error(F"{datetime.datetime.now()}, Camera {link}, blank")
								kecilin_log.send_notif(f"Kecilin {args.project_name}\n{datetime.datetime.now()}\nJenis: {jenis_kereta},\nNo Sarana: {no_sarana}\nCamera channel {channel} is blank")
								
								notif_data = {
									"name" : F"{ip['ip']}_Ch-{channel}",
									"datetime" : str(datetime.datetime.now()),
									"jenis" :  jenis_kereta,
									"no_sarana" : no_sarana,
									"status"	: False
								}
								kecilin_log.post_data_notif(args.url_api_notif, notif_data)
							else:
								kecilin_log.send_notif(f"Kecilin {args.project_name}\n{datetime.datetime.now()}\nJenis: {jenis_kereta},\nNo Sarana: {no_sarana}\nCamera channel {channel} is Online")
								
								notif_data = {
									"name" : F"{ip['ip']}_Ch-{channel}",
									"datetime" : str(datetime.datetime.now()),
									"jenis" :  jenis_kereta,
									"no_sarana" : no_sarana,
									"status"	: True
								}
								kecilin_log.post_data_notif(args.url_api_notif, notif_data)		
						else:
							logging.error(F"{datetime.datetime.now()}, Camera {link} is offline")
							kecilin_log.send_notif(f"Kecilin {args.project_name}\n{datetime.datetime.now()}\nJenis: {jenis_kereta},\nNo Sarana: {no_sarana}\nCamera channel {channel} is offline")
							
							notif_data = {
								"name" : F"{ip['ip']}_Ch-{channel}",
								"datetime" : str(datetime.datetime.now()),
								"jenis" :  jenis_kereta,
								"no_sarana" : no_sarana,
								"status"	: False
							}
							kecilin_log.post_data_notif(args.url_api_notif, notif_data)
						if loop_time == 4:
							break

						loop_time = loop_time + 1


					cap = None
					channel += 1

		time.sleep(30)
