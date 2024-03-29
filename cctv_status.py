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
		self.temp_status_camera = {}
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
			print(req.status_code)
		except:
			pass

	def update_status_camera(self, url_api, link, status, identitas):
		if link in self.temp_status_camera:
			if self.temp_status_camera[link] != status:
				self.temp_status_camera[link] = status
				update = True
			else:
				update = False
		else:
			self.temp_status_camera[link] = status
			update = True

		if update:
			if status == 'blank':
				self.send_notif(f"Kecilin {args.project_name}\n{datetime.datetime.now()}\nJenis: {identitas['jenis_kereta']},\nNo Sarana: {identitas['no_sarana']}\nCamera channel {identitas['channel']} is Blank")
			elif status:
				self.send_notif(f"Kecilin {args.project_name}\n{datetime.datetime.now()}\nJenis: {identitas['jenis_kereta']},\nNo Sarana: {identitas['no_sarana']}\nCamera channel {identitas['channel']} is Online")
			else:
				self.send_notif(f"Kecilin {args.project_name}\n{datetime.datetime.now()}\nJenis: {identitas['jenis_kereta']},\nNo Sarana: {identitas['no_sarana']}\nCamera channel {identitas['channel']} is Offline")

			notif_data = {
			    "rtsp": 	link,
				"status"	: status
			}
			print(notif_data)
			self.post_data_notif(url_api, notif_data)


	def checking_status(self, args, success, frame, link, identitas):
		if success:
			if not camera_is_open(frame, 100):
				logging.error(F"{datetime.datetime.now()}, Camera {link}, blank")
				self.update_status_camera(args.url_api_notif, link, 'blank', identitas)
				print('camera blank')
			else:
				self.update_status_camera(args.url_api_notif, link, True, identitas)
				print('camera aktif')
					
		else:
			logging.error(F"{datetime.datetime.now()}, Camera {link} is offline")
			self.update_status_camera(args.url_api_notif, link, False, identitas)
			print('camera offline')


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-pn', '--project-name', type=str, required=True, help='set Project Name') 
	parser.add_argument('-k', '--key', type=str, default='ygbyi87b7b87ygb87tbytb8iugiut76t6bgby', help='set key number') 
	parser.add_argument('-d', '--domain', type=str, default='http://api.cctv.kecilin.id', help='set domain key') 
	# parser.add_argument('-sn', '--service-name', type=str, help='set name service', default='kecilin-logs') 
	parser.add_argument('-ua','--url-api', type=str, default="http://127.0.0.1:8000/active", help='set url of post data') 
	parser.add_argument('-uan','--url-api-notif', type=str, default="http://127.0.0.1:8555/api/notif/store", help='set url of post data for notif') 
	# parser.add_argument('-pm2', '--pm2-json', action='store_true', help='Create service pm2 config.json')
	parser.add_argument('--force-restart', '-fr', default=('0',), type=str, nargs='+', help='set id of force restart')
	parser.add_argument('-ifr', '--interval-fr', default=0, type=int, help='set interval of force restart')
	parser.add_argument('-fnl', '--fn-log', default='logs/kecilin.log', type=str, help='set file name of log')
	parser.add_argument('-sc', '--skip-cctv', default=False, action='store_true', help='hide confidences')
	parser.add_argument('-tt', '--tlg-token', type=str, default='5793621628:AAGlXUMECyjG0ZaDpqUp3ayuG-fL4-Jko0U', help='Set Telegram token')
	parser.add_argument('-tc', '--tlg-chat-id', type=str, default='-735553666', help='Set telegram chat id')
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
	
	while True:
		try:
			data_cctv = requests.get(args.url_api).json()
		except Exception as e:
			print(F'\n\n{e}')
			logging.error(F"{datetime.datetime.now()}, request to {args.url_api} is error")
			sys.exit()
		data = data_cctv['data'] 
		
		
		for ip in data:
			jenis_kereta = ip["jenis_kereta"]
			no_sarana = ip["no_sarana"]
			channel = 1

			identitas = {}

			identitas['no_sarana'] = no_sarana
			identitas['jenis_kereta'] = jenis_kereta

			for link in ip["rtsp"]:
				identitas['channel'] = channel
				
				
				
				# print(link)
				cap = cv2.VideoCapture(link)
				time.sleep(0.5)


				
				success, frame = cap.read() 
				kecilin_log.checking_status(args, success, frame, link, identitas)
				

				cap = None
				channel += 1

		for link in kecilin_log.temp_status_camera:
			cap = cv2.VideoCapture(link)
			time.sleep(0.5)				
			success, frame = cap.read() 
			kecilin_log.checking_status(args, success, frame, link, identitas)
			

			cap = None

		time.sleep(1)