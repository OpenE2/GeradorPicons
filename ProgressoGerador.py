# -*- coding: utf-8 -*-
import os

import shutil
from Components.Sources.Progress import Progress
from Components.Sources.StaticText import StaticText
from Screens.Screen import Screen
from enigma import eTimer,eDVBDB

import utils
from geradorpicons import config


class ProgressoGeradorScreen(Screen):

	skin="""
			<screen name="ProgressoGerador" position="267,111" size="723,500" title="Gerador de Picons">
			      <widget source="job_name" render="Label" position="65,147" size="600,35" font="Regular;28" />
			      <widget source="job_task" render="Label" position="65,216" size="600,30" font="Regular;24" />
			      <widget source="job_progress" render="Progress" position="65,291" size="600,36" borderWidth="2" backgroundColor="#254f7497" />
			      <widget source="job_progress" render="Label" position="160,294" size="410,32" font="Regular;28" foregroundColor="#000000" zPosition="2" halign="center" transparent="1">
			        <convert type="ProgressToText" />
			      </widget>
			</screen>
	"""
	            # <widget source="job_progress" render="Progress" position="590,260" size="600,36" borderWidth="2" backgroundColor="#254f7497" />

	def __init__(self, session,zipFile,gerados={}):
		Screen.__init__(self, session)
		self.skin=ProgressoGeradorScreen.skin

		self["Title"].text=utils._title+" - "+utils._developer

		self.onFirstExecBegin.append(self.windowShow)
		self.gerados=gerados

		self.progress=Progress()

		self.jobName=StaticText()
		self.jobTask=StaticText()
		self["job_progress"]=self.progress

		self["job_name"]=self.jobName
		self["job_task"]=self.jobTask

		self.progress.setRange(len(gerados))
		self.progress.value=0

		self.total=len(gerados)
		utils.addScreen(self)
		self.zipFile=zipFile


	def windowShow(self):
		self.jobName.text="Preparando..."
		self.wrappertimer = eTimer()
		self.wrappertimer.callback.append(self.processar)
		self.wrappertimer.start(10, True)

	def reload(self):
		eDVBDB.getInstance().reloadBouquets()
		eDVBDB.getInstance().reloadServicelist()
		self.close()

	def processar(self):
		if self.gerados:
			piconsDir=config.plugins.Channel.pasta.value

			try:
				os.makedirs(piconsDir)
			except OSError as exception:
				pass

			from enigma import eServiceCenter
			servicehandler = eServiceCenter.getInstance()

			canal = self.gerados.keys().pop()
			if canal:
				picon = self.gerados[canal]
				del self.gerados[canal]
				nome = servicehandler.info(canal).getName(canal).lower()
				self.jobName.text = "Processando canal %s" % (nome)
				if picon:
					self.tipoPicon=picon.tipoPicon
					piconName = piconsDir + "/" + picon.getPiconName()
					self.jobTask.text = "Copiando arquivo..."

					shutil.copy(picon.tmpPng,piconName)


				self.progress.value = self.total-len(self.gerados)
				self.wrappertimer.start(10, True)
		else:
			self.jobName.text="Concluído!"
			self.jobTask.text=""
			print "/tmp/%s"%(self.tipoPicon)
			shutil.rmtree("/tmp/"+self.tipoPicon,True)

			self.timer = eTimer()
			self.timer.callback.append(self.reload)
			self.timer.start(2000,True)











