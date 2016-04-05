# -*- coding: utf-8 -*-
from Components.ActionMap import ActionMap
from Components.Language import language
from Components.PluginComponent import plugins
from Components.Sources.StaticText import StaticText
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE
from Tools.LoadPixmap import LoadPixmap
from enigma import eServiceCenter

import utils
from Picon import Picon
from PiconList import *
from ProgressoGerador import ProgressoGeradorScreen


def languageChanged():
	plugins.clearPluginList()
	plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))


class DuvidasPiconScreen(Screen):
	skin="""
		 <screen name="DuvidasPicon" position="267,111" size="723,500" title="Gerador de Picons">

		         <widget name="list" position="44,10" size="630,444" font="Regular;26" scrollbarMode="showOnDemand" selectionPixmap="skin_default-HD/buttons/sel.png" />
		         <ePixmap pixmap="skin_default/buttons/red.png" position="131,460" size="26,26" alphatest="on" />
		        <widget source="key_red" render="Label" position="166,460" size="220,28" backgroundColor="darkgrey" zPosition="2" transparent="1" foregroundColor="grey" font="Regular;24" halign="left" />

		        <ePixmap pixmap="skin_default/buttons/green.png" position="415,460" size="26,26" alphatest="on" />
		        <widget source="key_green" render="Label" position="450,460" size="220,28" backgroundColor="darkgrey" zPosition="2" transparent="1" foregroundColor="grey" font="Regular;24" halign="left" />

		      </screen>
			"""
	def __init__(self, session,zipFile, gerados={},duvidas={}):
		Screen.__init__(self, session)
		# self.skinName = [ "PluginBrowser" ]

		self.zipFile=zipFile
		self.skin=DuvidasPiconScreen.skin

		self.onLayoutFinish.append(self.updateList)

		self.onFirstExecBegin.append(self.mostraMensagem)

		self["Title"].text=utils._title

		self.list = []
		self.lista=PluginList(self.list)
		self["list"] = self.lista
		self.duvidasList = {}
		self.expanded = []

		self["key_red"] = StaticText(_("Cancelar"))
		self["key_green"] = StaticText(_("Salvar"))

		self["actions"] = ActionMap(["OkCancelActions","InputActions","ColorActions", "DirectionActions"],
        {
            "green": self.enviar,
            "cancel": self.close,
            "ok":self.selecionar,
	        "back": self.close,
	        "left": self.left,
	        "right": self.right

        }, -2)
		self.gerados=gerados
		self.prepareList(duvidas)
		utils.addScreen(self)


	def mostraMensagem(self):
		msg="Foram encontrado(s) %d picons!\nPorem eu fiquei em dúvida em alguns.\nVocê pode escolher na lista os que combinam com cada canal."%(len(self.gerados))
		self.session.open(MessageBox, text = msg, type = MessageBox.TYPE_WARNING,close_on_any_key=True, timeout=5)


	def enviar(self):
		for canal in self.duvidasList.keys():
			picon= filter(lambda p: p.selected,self.duvidasList[canal])
			if len(picon)>0:
				self.gerados[canal]=picon[0]

		self.session.open(ProgressoGeradorScreen,zipFile=self.zipFile,gerados=self.gerados)




	def selecionar(self):
		piconSelecionado = self["list"].l.getCurrentSelection()

		if piconSelecionado is None:
			return
		piconSelecionado = piconSelecionado[0]
		if isinstance(piconSelecionado, Picon):
			check=not piconSelecionado.selected

			for picon in self.getCategory(piconSelecionado.categoria):
				picon.selected=False

			piconSelecionado.selected=check

			self.updateList()


	def updateList(self):

		list = []
		expandableIcon = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/expandable-plugins.png"))
		expandedIcon = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/expanded-plugins.png"))
		verticallineIcon = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/verticalline-plugins.png"))

		listsize = self["list"].instance.size()
		self.listWidth = listsize.width()
		self.listHeight = listsize.height()

		from enigma import eServiceReference, eServiceCenter, iServiceInformation,eDVBDB
		servicehandler = eServiceCenter.getInstance()


		for x in self.duvidasList.keys():

			transponder_info = servicehandler.info(x).getInfoObject(x, iServiceInformation.sTransponderData)
			print transponder_info.keys()
			if transponder_info["tuner_type"]=="DVB-C":
				tp=str(int(transponder_info["frequency"])/1000)
			else:
				tp=str(int(transponder_info["frequency"])/1000)+ "H" if transponder_info["polarization"]==0 else "V"

			hd = False
			if x.type == 25:
				hd = True
			nome = servicehandler.info(x).getName(x).lower()
			if x and nome.endswith("hd"):
				hd = True

			list.append(PluginCategoryComponent(self.getNome(x),expandedIcon,sat=utils.getSatInfo(transponder_info),tp=tp,hd=hd, width=self.listWidth))
			list.extend([PluginDownloadComponent(picon, self.listWidth) for picon in self.duvidasList[x]])

		self.list = list
		self["list"].l.setList(list)

	def prepareList(self,lista={}):
		for canal in lista.keys():
			self.addIntoCategory(canal,[picon for picon in lista[canal]])


	def getNome(self,canal):
		servicehandler = eServiceCenter.getInstance()
		return servicehandler.info(canal).getName(canal)


	def addCategory(self,categoria):
		if not self.duvidasList.has_key(categoria):
			self.duvidasList[categoria]=[]


	def getCategory(self,categoria):
		self.addCategory(categoria)
		return self.duvidasList[categoria]

	def addIntoCategory(self,categoria,item):
		self.getCategory(categoria).extend([Picon(categoria,picon,self.zipFile,duvida=True) for picon in item])


	def right(self):
		selecionado=self.lista.getSelectedIndex()+1
		if selecionado<len(self.list):

			for i in range(selecionado,len(self.list)):
				if isinstance(self.list[i][0],str):
					self.lista.moveToIndex(i)
					break

	def left(self):
		selecionado=self.lista.getSelectedIndex()-1
		if selecionado < 0: pass

		for i in range(selecionado,0,-1):
			if isinstance(self.list[i][0],str):
				self.lista.moveToIndex(i)
				break





language.addCallback(languageChanged)
