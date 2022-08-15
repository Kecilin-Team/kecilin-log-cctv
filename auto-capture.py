import os
import sys
import time
import logging
import argparse
import datetime
import uuid

import modules

import cv2
import tzlocal
from apscheduler.schedulers.background import BackgroundScheduler

logging.getLogger('apscheduler.executors.default').propagate = False
logging.getLogger('apscheduler.scheduler').propagate = False
# logging.basicConfig(filename=args.fn_log, level=logging.DEBUG)
# logging.info('Kecilin logs is started')

class CronIntervalJob:
	def __init__(self, args):
		# self.logging = logging.getLogger('apscheduler.executors.default').propagate = False
		# self.logging.getLogger('apscheduler.scheduler').propagate = False
		logging.basicConfig(filename=args.fn_log, level=logging.DEBUG)
		logging.info('Kecilin logs is started')
		self.scheduler = BackgroundScheduler(daemon=True, timezone=str(tzlocal.get_localzone()))
		self.sources				= args.sources
		self.cron 					= args.cron
		self.cron_type_time			= args.cron_type_time
		self.cron_times 			= args.cron_times
		self.interval 				= args.interval
		self.interval_type_time		= args.interval_type_time
		self.interval_times 		= args.interval_times
		self.url_api				= args.url_api
		# for camera in self.sources:
		# 	print(camera)

		if self.cron:
			print("cron-job is running")
			id_job = 1
			for time in self.cron_times:
				id_job_details = F"cron_{id_job}_{time}"
				print(id_job_details)
				if self.cron_type_time=='second':
					self.scheduler.add_job(self.main_job, 'cron', second=time, id=id_job_details)
				elif self.cron_type_time=='minute':
					self.scheduler.add_job(self.main_job, 'cron', minute=time, id=id_job_details)
				elif self.cron_type_time=='hour':
					self.scheduler.add_job(self.main_job, 'cron', hour=time, id=id_job_details)
				else:
					print("Error Cron type of time")
		
		if self.interval:
			print("interval-job is running")
			id_job = 1
			for time in self.interval_times:
				id_job_details = F"interval_{id_job}_{time}"
				print(id_job_details)
				if self.interval_type_time=='seconds':
					self.scheduler.add_job(self.main_job, 'interval', seconds=time, id=id_job_details)
				elif self.interval_type_time=='minutes':
					self.scheduler.add_job(self.main_job, 'interval', minutes=time, id=id_job_details)
				elif self.interval_type_time=='hours':
					self.scheduler.add_job(self.main_job, 'interval', hours=time, id=id_job_details)
				else:
					print("Error Interval type of time")
		
		self.start_time = datetime.datetime.now()


	def main_job(self):
		now = datetime.datetime.now()
		print("_________________________________________")
		print("\tRunnning Job", now)
		print("\tDefisit time Job", (now-self.start_time))
		self.job_capture(now)
		print("_________________________________________")

	def job_capture(self, datetime):
		for camera in self.sources:
			cap = None
			try:
				cap = cv2.VideoCapture(int(camera))
			except:
				cap = cv2.VideoCapture(camera)

			

			time.sleep(2)	
			status, frame = cap.read()

			if status:
				self.job_capture_post(frame, camera,datetime)
			else:
				logging.error(F"{datetime}, Camera {camera} is offline")

	def job_capture_post(self, frame, camera,datetime):
		filename = F"logs/images/{uuid.uuid4()}_{str(datetime).replace(' ', '_')}.jpeg"
		cv2.imwrite(filename, frame)

		if self.url_api is not None:
			files = {
				'image_object'      : filename,								
			}
			form_data = {
				'camera'       		: "CCTV POC",
				'link'				: camera,
				'datetime'			: str(datetime)
				}

			status_res = modules.post_data_api(self.url_api, form_data, files)

			print(status_res)










if __name__ == "__main__":

	parser = argparse.ArgumentParser("Kecilin Aps!")
	parser.add_argument('-fnl', '--fn-log', default='logs/auto-capture.log', type=str, help='set file name of log')
	parser.add_argument("-srcs", "--sources", type=str, required=True, nargs='+', help='set sources camera')
	parser.add_argument("-cr", "--cron", action='store_true', help='Add cron job')
	parser.add_argument("-crtyt", "--cron-type-time", default='minute', type=str, help='Set the interval type of times')
	parser.add_argument("-crtm", "--cron-times", type=int, nargs='+', help='Set the interval times')
	parser.add_argument("-itr", "--interval", action='store_true', help='Add cron interval job')
	parser.add_argument("-itrtyt", "--interval-type-time", type=str, default='minutes', help='Set the interval type of times')
	parser.add_argument("-itrtm", "--interval-times", type=int, nargs='+', help='Set the interval times')
	parser.add_argument('-ua','--url-api', type=str, default=None, help='set url of post data') 

	opt = parser.parse_args()

	cron_interval_job = CronIntervalJob(opt)
	try:
		cron_interval_job.scheduler.start()
		while True:
			time.sleep(15)
		
	except KeyboardInterrupt:
		sys.exit()
