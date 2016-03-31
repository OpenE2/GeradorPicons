import os

from Tools.LoadPixmap import LoadPixmap


class Picon:
	def __init__(self,categoria,path,zipFile,duvida=False):
		# from Components.Renderer.Picon import getPiconName
		self.categoria=categoria
		self.path=path[0]
		self.selected=False
		self.duvida=duvida

		self.tmpPng=zipFile.extract(self.path,"/tmp")
		self.png=LoadPixmap(self.tmpPng)

		self.tipoPicon=self.tmpPng.split("/")[1]

	def getPiconName(self):
		# replace("#SERVICE ", "").split("::")[0].replace(":", "_")+".png";
		return self.categoria.toString()[:-1].replace(":","_")+".png"

	def getDirPath(self):
		return "/".join(self.path.split("/")[:-1])+"/"

	def removerPng(self):
		if self.tmpPng:
			try:
				os.remove(self.tmpPng)
			except:
				pass