import os
import sys
import time
import logging
import datetime
import argparse

import cv2
import pandas as pd
import numpy as np
from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.schedulers.blocking import BlockingScheduler
import requests
import tzlocal

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
		print("\tDomain :",self.domain)
		print("\tAPI Key :",self.key)

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
		requests.get(url)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-pn', '--project-name', type=str, required=True, help='set Project Name') 
	parser.add_argument('-k', '--key', type=str, default='ygbyi87b7b87ygb87tbytb8iugiut76t6bgby', help='set key number') 
	parser.add_argument('-d', '--domain', type=str, default='http://api.cctv.kecilin.id', help='set domain key') 
	parser.add_argument('-sn', '--service-name', type=str, help='set name service', default='kecilin-logs') 
	parser.add_argument('-c', '--cron', action='store_true', help='run cron restart')
	parser.add_argument('--force-restart', '-fr', default=('0',), type=str, nargs='+', help='set id of force restart')
	parser.add_argument('-ifr', '--interval-fr', default=30, type=int, help='set interval of force restart')
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
	kecilin_log.reg_init_key()

	sched = BackgroundScheduler(daemon=True, timezone=str(tzlocal.get_localzone()))

	@sched.scheduled_job('interval', id='job_api_key', minutes=10)
	def check_history_key():
		kecilin_log.status_key = kecilin_log.history_key()
		if not kecilin_log.status_key:
			kecilin_log.send_notif(f'Kecilin {args.project_name}\nApi Key is inactived or Expired')
			if kecilin_log.services is not None:
				for service in kecilin_log.services:
					logging.error(F"{datetime.datetime.now()}, stopping {service[1]}")
					cmd = F"pm2 stop {service[1]}"
					os.system(cmd)
		else:
			print("key is active")

		

	if args.interval_fr > 0:
		print('Force Restart Active')
		pm2_ids = ' '.join(list(args.force_restart))

		@sched.scheduled_job('interval', id='job_force_restart', minutes=args.interval_fr)
		def force_restart_service():
			cmd = F"pm2 restart {pm2_ids}" 
			os.system(cmd)
	else:
		print('Force Restart is not Active')

	if args.cron:
		print('Cron Restart Active')
		pm2_ids = ' '.join(list(args.force_restart))

		@sched.scheduled_job('cron', id='job_force_restart', hour=0)
		def force_restart_service():
			cmd = F"pm2 restart {pm2_ids}" 
			os.system(cmd)
	else:
		print('Cron Force Restart is not Active')
	

	sched.start()

	if not args.skip_cctv:
		kecilin_log.services = pd.read_csv('templates/services_list.csv', delimiter=',', header=0)
		kecilin_log.services = np.array(kecilin_log.services)	

	while True:
		if args.skip_cctv or not kecilin_log.status_key:
			print('Skipping CCTV')
		else:
			print('Log CCTV is running')
			for service in kecilin_log.services:
				if kecilin_log.status_key:
					cap = cv2.VideoCapture(service[3])
					time.sleep(30)
					if not cap.isOpened():
						cap = cv2.VideoCapture(service[2])
						time.sleep(15)
						if not cap.isOpened():
							logging.error(F"{datetime.datetime.now()}, Camera {service[2]} is offline")
							kecilin_log.send_notif(f"Kecilin {args.project_name}\nCompression not work normally\non this link {service[3]}\nCamera Original is offline")
						else:
							logging.error(F"{datetime.datetime.now()}, restarting {service[1]}")
							cmd = F"pm2 restart {service[1]}"
							os.system(cmd)
							kecilin_log.send_notif(f'Kecilin {args.project_name}\nCompression not work normally\non this link {service[3]}\nTrying to restart service {service[1]}')
					cap = None

		time.sleep(30)

