import os

from Tools.LoadPixmap import LoadPixmap

import utils


class Picon:
	def __init__(self,categoria,path,zipFile,duvida=False):
		self.categoria=categoria
		self.path=path[0]
		self.selected=False
		self.duvida=duvida

		self.tmpPng=zipFile.extract(self.path,utils._picoZipDir)
		if self.tmpPng:
			self.png=LoadPixmap(self.tmpPng)
		else:
			self.png=None

		from enigma import eServiceReference, eServiceCenter, iServiceInformation
		servicehandler = eServiceCenter.getInstance()
		self.nome=servicehandler.info(self.categoria).getName(self.categoria)

	def getPiconName(self):
		# replace("#SERVICE ", "").split("::")[0].replace(":", "_")+".png";
		return self.categoria.toString()[:-1].replace(":","_")+".png"

	def getDirPath(self):
		return "/".join(self.path.split("/")[:-1])+"/"

	def getPiconByName(self):
		import re
		return self.acertarNome(re.sub("[\s!?.,_()]","", utils.removerAcentos(self.nome).replace(" ",""))).lower()+".png"

	def removerPng(self):
		if self.tmpPng:
			try:
				os.remove(self.tmpPng)
			except:
				pass

	def acertarNome(self,nome):
		import re
		tmp= re.sub("\*","star",nome)
		tmp= re.sub("\+","plus",tmp)
		tmp= re.sub("\-","minus",tmp)
		tmp= re.sub("\&","and",tmp)
		tmp= re.sub("\$","dollar",tmp)
		tmp= re.sub("\%","percent",tmp)
		tmp= re.sub("\@","at",tmp)
		tmp= re.sub("\#","hash",tmp)
		tmp= re.sub("\=","equal",tmp)
		return tmp

