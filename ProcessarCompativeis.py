# -*- coding: utf-8 -*-
import os
import re
import zipfile
from sets import Set

import StringIO
from Components.Sources.Progress import Progress
from Components.Sources.StaticText import StaticText
from Screens import MessageBox
from Screens.Screen import Screen
from enigma import eTimer

import utils
from Picon import Picon
from ProgressoGerador import ProgressoGeradorScreen
from duvidasList import DuvidasPiconScreen
from geradorpicons import config


class ProcessarCompativeisScreen(Screen):
	skin = """
			<screen name="ProcessarCompativeisScreen" position="267,111" size="723,500" title="Gerador de Picons">
			      <widget source="job_name" render="Label" position="65,147" size="600,35" font="Regular;28" />
			      <widget source="job_task" render="Label" position="65,216" size="600,30" font="Regular;24" />
			      <widget source="job_progress" render="Progress" position="65,291" size="600,36" borderWidth="2" backgroundColor="#254f7497" />
			      <widget source="job_progress" render="Label" position="160,294" size="410,32" font="Regular;28" foregroundColor="#000000" zPosition="2" halign="center" transparent="1">
			        <convert type="ProgressToText" />
			      </widget>
			</screen>
	"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin = ProcessarCompativeisScreen.skin

		self["Title"].text = utils._title
		self.tipoPicon = config.plugins.Channel.tipo.value
		self.onFirstExecBegin.append(self.downloadZip)
		self.progress = Progress()

		self.jobName = StaticText()
		self.jobTask = StaticText()
		self["job_progress"] = self.progress


		self["job_name"] = self.jobName
		self["job_task"] = self.jobTask
		utils.addScreen(self)

	def abre(self):
		self.session.open(DuvidasPiconScreen, zipFile=self.zipFile, gerados=self.gerados, duvidas=self.duvidas)

	def processar(self):
		from enigma import eServiceReference, eServiceCenter, iServiceInformation
		servicehandler = eServiceCenter.getInstance()

		if self.canais:

			item = self.canais.pop()

			canal = eServiceReference(item[0])
			if canal:
				nome = servicehandler.info(canal).getName(canal).lower()

				self.jobName.text = "Processando canal %s" % (nome)

				transponder_info = servicehandler.info(canal).getInfoObject(canal, iServiceInformation.sTransponderData)
				cabo = transponder_info["tuner_type"] == "DVB-C"

				hd = False
				if canal.type == 25:
					hd = True
				if cabo and nome.strip().endswith("hd"):
					hd = True

				# if "espn" in nome:
				# 	print "-----------------------------------------------"
				# 	print "%s eh hd: %s"%(nome,hd)

				if not (not nome or nome == "(...)"):
					self.jobTask.text = "Procurando picons compatíveis..."
					arqs = self.getCompativel(utils.corrigiNome(nome), hd)

					if arqs:
						if len(arqs) == 1:
							self.jobTask.text = "Picon encontrado!"
							self.gerados[canal] = Picon(canal, arqs[0], self.zipFile)
						elif len(arqs) > 1:
							self.jobTask.text = "Hum... Dúvidas..."
							self.duvidas[canal] = arqs[0:10]

			self.progress.value = self.total - len(self.canais)
			self.timer.start(1, True)

		else:
			print "gerados: %d, duvidas: %d" % (len(self.gerados), len(self.duvidas))
			if len(self.duvidas) > 0:
				self.abre()
			else:
				self.session.open(ProgressoGeradorScreen,zipFile=self.zipFile,gerados=self.gerados)


	def downloadZip(self):

		import requests, zipfile, StringIO
		self.response = requests.get(self.tipoPicon, stream=True)
		self.totalProgresso = int(self.response.headers.get('content-length'))
		self.progress.setRange(self.totalProgresso)
		self.jobName.text="Baixando os picons..."
		self.content = ""
		self.recebido = 0

		self.downloadTimer = eTimer()
		self.downloadTimer.callback.append(self.atualizaProgresso)
		self.downloadTimer.start(1, True)

	def atualizaProgresso(self):
		chunck = self.response.iter_content(9216).next()

		self.recebido += len(chunck)
		self.progress.value = self.recebido
		self.content += chunck
		if self.recebido < self.totalProgresso:
			self.downloadTimer.start(1, True)
		else:
			self.zipFile = zipfile.ZipFile(StringIO.StringIO(self.content))
			if self.zipFile:
				self.listaPicons = [(name, re.split("\/", name)[1]) for name in self.zipFile.namelist()]

				self.timerGerar = eTimer()
				self.timerGerar.callback.append(self.gerarChannel)
				self.timerGerar.start(1, True)
			else:
				self.session.open(MessageBox,
				                  text="Erro ao baixar os picons!\nVerifica sua conexão com a internet e tente novamente.",
				                  type=MessageBox.TYPE_WARNING, close_on_any_key=True, timeout=5)

	def gerarChannel(self):

		self.close_on_next_exec = (0, 1)

		from Components.Sources.ServiceList import ServiceList

		# self.tipoPicon = config.plugins.Channel.tipo.value
		# self.listaPicons = [(os.path.join(self.tipoPicon, o), o) for o in os.listdir(self.tipoPicon) if o.lower().endswith(".png")]

		self.tags = {}
		for file in self.listaPicons:
			nomes = re.split("\s", utils.corrigiNome(file[1]))
			# if "espn" in file[1].lower():
			# 	print file[1]
			# 	print nomes

			for nome in nomes:
				if not self.tags.has_key(nome.strip().lower()):
					self.tags[nome.strip().lower()] = []
				self.tags[nome.strip().lower()].append(file)


		# for tag in self.tags.keys():
		# 	if tag=="espn":
		# 		for nome in self.tags[tag]:
		# 			print "%s %s"%(tag,nome)

		currentServiceRef = self.session.nav.getCurrentlyPlayingServiceReference()
		servicelist = ServiceList("")
		servicelist.setRoot(currentServiceRef)
		self.canais = servicelist.getServicesAsList()

		self.gerados = {}
		self.duvidas = {}
		self.filtrarRadios()

		# self.canais=self.canais[80:120]

		self.progress.setRange(len(self.canais))
		self.progress.value = 0

		self.total = len(self.canais)

		self.timer = eTimer()
		self.timer.callback.append(self.processar)
		self.timer.start(10, True)

	def filtrarRadios(self):
		from enigma import eServiceReference, eServiceCenter, iServiceInformation
		servicehandler = eServiceCenter.getInstance()
		import re

		tmp=[]
		for item in self.canais:
			canal = eServiceReference(item[0])
			nome = servicehandler.info(canal).getName(canal).lower()
			transponder_info = servicehandler.info(canal).getInfoObject(canal, iServiceInformation.sTransponderData)

			if canal.type != 2:
				if not re.match("\d+",nome):
					tmp.append(item)

		self.canais=tmp


	def getCompativel(self, nome, hd):
		# self.debug=False
		# if "espn hd" in nome.lower():
		# 	self.debug=True

		for file in self.listaPicons:
			# if nome.lower().startswith("premiere hd"):
			# 	print "%s = %s, %s"%(re.sub("\s+","",file[1]).lower(),re.sub("\s+","",nome).lower(), re.sub("\s+","",file[1]).lower()==re.sub("\s+","",nome).lower())
			if utils.corrigiNome(re.sub("\s+", "", file[1])).lower() == utils.corrigiNome(re.sub("\s+", "", nome)) + ".png".lower():
				return [file]

		tmpTags = Set(self.tags.keys())
		# print "enviando tmpTags %d"%(len(tmpTags))
		compativeis = list(self.getCompativeis(nome, tmpTags, Set(), hd))

		# print "getCompativel: %d"%(len(compativeis))

		if len(compativeis) == 1:
			return compativeis

		# print "verifica se tem nome compativel"

		for file in compativeis:
			fileName = utils.corrigiNome(file[1])
			if fileName.strip() == nome:
				return [file]

		# for file in compativeis:
		# 	fileName = utils.corrigiNome(file[1])
		# 	print "%s - %s - %s - %s" %(fileName,nome,fileName[0:5],nome[0:5])
		# 	if fileName[0:3].strip()==nome[0:3].strip():
		# 		return [file]


		# print "verifica quando sao dois"
		if len(compativeis) == 2:
			print "%s - %s"%(nome,compativeis)
			if len(re.split("\s", compativeis[0][1])) > len(re.split("\s", compativeis[1][1])):
				return [compativeis[1]]
			else:
				return [compativeis[0]]

		# print "tenta encontrar os compativeis"

		for file in compativeis:
			i = 0
			fileName = re.split("\s", utils.corrigiNome(file[1]))
			for name in fileName:
				if name.strip().lower() == nome.lower() or nome.replace("\s+", "").strip().lower() == name.lower():
					return [file]
				if name in nome:
					i = i + 1

			if i >= len(re.split("\s", nome)):
				return [file]


		# i=(0,None,0)
		# for file in compativeis:
		# 	a=0
		# 	files = re.split("\s", utils.corrigiNome(file[1]))
		# 	for f in files:
		# 		nomes= re.split("\s", utils.corrigiNome(nome))
		# 		for n in nomes:
		# 			if f.strip().lower()==n.strip().lower():
		# 				a+=1
		# 	if i[0]<a:
		# 		i=(a,file,len(files))
		# 	elif i[0]==a:
		# 		if i[2]<len(files):
		# 			i=(a,file,len(files))

		# print "--------------------------------------------------------------"
		# print "%s - %s - %s"%(nome,i[1],i[0])
		# if i[1] and i[0]>=2:
		# 	return [i[1]]

		# print "encontrei: %d compativeis"%(len(compativeis))
		return compativeis

	def getCompativeis(self, nome, tmpTags, tmpArquivos, hd):

		# if self.debug:
		# 	print "getCompativeis: %d - arquivos %d"%(len(tmpTags),len(tmpArquivos))
		# 	print "procurando compativeis para %s" %(nome)
		nomes = re.split("\s", nome.strip())
		tmpNome = nomes[0]
		# if self.debug :
		# 	print "tmpNome %s, nomes: %s"%(tmpNome,nomes)
		if len(nomes) > 0 and tmpNome:
			novoNome = ""
			sep = ""
			for i in range(1, len(nomes)):
				novoNome += sep + nomes[i]
				if len(sep)==0:
					sep = " "
			# if self.debug :
			# 	print "%s estah - %s" %(tmpNome, tmpNome in tmpTags)
			if tmpNome in tmpTags:
				# if self.debug:
				# 	print "tmpArquivos - %d"%(len(tmpArquivos))
				if len(tmpArquivos)==0:
					tmpArquivos = tmpArquivos.union(Set(self.tags[tmpNome.strip()]))
					# if self.debug :
					# 	print "quando novo tmpArquivos - %d %s"%(len(tmpArquivos),tmpArquivos)
					# 	print  "hd %s"%(hd)
					if not hd:
						tmpArquivos = self.filtrar(tmpArquivos, "hd", True)
				else:
					tmpArquivos = self.filtrar(tmpArquivos, tmpNome, False)
			# elif len(tmpArquivos)>0:
			# 	if self.debug:
			# 		print "nao estah em %s"%(tmpTags)
			# 		print tmpArquivos
			# 	tmpArquivos = self.filtrar(tmpArquivos, tmpNome, False)


			# if self.debug :
			# 	print "tmpArquivos - %d %s"%(len(tmpArquivos),tmpArquivos)
			tt = Set(self.getTags(tmpArquivos, hd))
			# if self.debug:
			# 	print "encontrei algo? %s %s"%(len(tt),tt)
			# 	print "proximo %s"%(novoNome)
			return self.getCompativeis(novoNome, tt, tmpArquivos, hd)
		else:
			# if self.debug:
			# 	print "terminou %d"%(len(tmpArquivos))
			return tmpArquivos

	def filtrar(self, arquivos, nome, nao):
		tmp = Set()
		for file in arquivos:
			if nao:
				if nome.strip() not in utils.corrigiNome(file[1]).lower():
					tmp.add(file)
			elif nome.strip().lower() in utils.corrigiNome(file[1]).lower():
				tmp.add(file)

		# print "filtrado %d"%(len(tmp))
		return tmp

	def getTags(self, files, hd):
		tmpTags = Set()
		if files:
			for file in files:
				name = re.split("\s", utils.corrigiNome(file[1]))
				for t in name:
					if t.strip().lower() == "hd" and not hd: continue
					tmpTags.add(t.strip())
		return tmpTags
