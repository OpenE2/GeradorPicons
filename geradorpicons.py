# -*- coding: utf-8 -*-

import os

from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.FileList import FileList
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.config import *
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from enigma import eConsoleAppContainer

import utils
from ProcessarCompativeis import ProcessarCompativeisScreen

config.plugins.Channel = ConfigSubsection()
config.plugins.Channel.tipo = ConfigSelection(default="", choices=[])

config.plugins.Channel.pasta = ConfigDirectory(default="/usr/share/enigma2/picon", visible_width=500)


# Class EasyBouquetScreen
class PrincipalScreen(ConfigListScreen, Screen):

	skin="""
		<screen name="PrincipalScreen" position="center,center" size="723,500" title="">
		    <widget name="config" position="30,51" size="657,207" scrollbarMode="showOnDemand" backgroundColor="header" transparent="1" />
		    <ePixmap pixmap="skin_default/buttons/red.png" position="131,460" size="26,26" alphatest="on" />
		    <widget source="key_red" render="Label" position="166,460" size="220,28" backgroundColor="darkgrey" zPosition="2" transparent="1" foregroundColor="grey" font="Regular;24" halign="left" />

		    <ePixmap pixmap="skin_default/buttons/green.png" position="415,460" size="26,26" alphatest="on" />
		    <widget source="key_green" render="Label" position="450,460" size="220,28" backgroundColor="darkgrey" zPosition="2" transparent="1" foregroundColor="grey" font="Regular;24" halign="left" />
		</screen>
	"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)

		# from Components.NimManager import nimmanager
		#
		# print "tem dvb-c ? %s" %( nimmanager.hasNimType("DVB-C"))
		# print "tem dvb-s ? %s" %( nimmanager.hasNimType("DVB-S"))


		# self.skin=PrincipalScreen.skin.replace("$PLUGINDIR$", utils._plugindir)
		self.skin=PrincipalScreen.skin
		# self.skinName = ["Setup"]
		self["Title"].text = utils._title
		self.onFirstExecBegin.append(self.verificarVersao)
		self.list = []
		self["config"] = ConfigList(self.list)
		self.onChangedEntry = []
		# listaDiretorios=[(os.path.join(utils._plugindir,o),o) for o in os.listdir(utils._plugindir) if os.path.isdir(os.path.join(utils._plugindir,o))]
		try:
			self.configuracoes = utils.getConfiguracoes()
			listaDiretorios = self.configuracoes["items"]
		except:
			self.session.open(MessageBox, text="É necessário conexão com a internet para executar este plugin!!!",
			                  type=MessageBox.TYPE_WARNING, close_on_any_key=True, timeout=5)
			self.close()

		config.plugins.Channel.tipo.setChoices(listaDiretorios)

		ConfigListScreen.__init__(self, self.list, session=self.session)

		self["key_red"] = StaticText(_("Cancelar"))
		self["key_green"] = StaticText(_("Gerar"))

		self["actions"] = ActionMap(["OkCancelActions", "InputActions", "ColorActions", "setupActions"],
		                            {
			                            "green": self.confirma,
			                            "red": self.cancel,
			                            "cancel": self.cancel,
			                            "ok": self.selecionarDiretorio,
			                            "yellow":self.getPicons
		                            }, -2)

		self.changedEntry()
		utils.addScreen(self)

	def verificarVersao(self):
		if float(self.configuracoes["versao"]) > float(utils._version):
			self.session.openWithCallback(self.atualizarVersao, MessageBox,
			                              _("Existe uma nova versão disponível!\nDeseja atualizar?"),
			                              MessageBox.TYPE_YESNO)

	def atualizarVersao(self, answer):
		if answer:
			self.container = eConsoleAppContainer()
			import urllib
			try:
				testfile = urllib.URLopener()
				testfile.retrieve(utils._urlVersao, "/tmp/geradorPicon.ipk")

				if os.path.isfile('/usr/bin/opkg'):
					self.ipkg = '/usr/bin/opkg'
					self.ipkg_install = self.ipkg + ' install'
					self.ipkg_remove = self.ipkg + ' remove --autoremove'
				else:
					self.ipkg = 'ipkg'
					self.ipkg_install = 'ipkg install -force-defaults'
					self.ipkg_remove = self.ipkg + ' remove'

				self.container.execute(self.ipkg + " /tmp/geradorPicon.ipk")

				self.session.openWithCallback(self.reiniciar, MessageBox, _("É necessário reiniciar a interface para que a atualização seja efetivada?\nConfirma?"), MessageBox.TYPE_YESNO)

			except:
				self.session.open(MessageBox,
				                  text="Não foi possível baixar a nova versão!\nTente mais tarde, quem sabe já esteja funcionando...",
				                  type=MessageBox.TYPE_WARNING, close_on_any_key=True, timeout=10)

	def reiniciar(self,answer):
		if answer:
			from Screens.Standby import TryQuitMainloop
			self.session.open(TryQuitMainloop, 3)


	def loading(self):
		self.session.open(ProcessarCompativeisScreen)

	def changedEntry(self):

		for x in self.onChangedEntry:
			x()

		self.list = []
		self.list.append(getConfigListEntry(_("Diretório dos Picons"), config.plugins.Channel.pasta))
		self.list.append(getConfigListEntry("Modelo dos Picons", config.plugins.Channel.tipo))

		self["config"].list = self.list
		self["config"].setList(self.list)

	def cancel(self):
		for i in self["config"].list:
			i[1].cancel()
		self.close(False)

	def confirma(self):

		if config.plugins.Channel.pasta.value == "":
			self.session.open(MessageBox, "Por favor escolha o caminho dos picons", MessageBox.TYPE_WARNING,
			                  close_on_any_key=True, timeout=5)
		else:
			self.loading()
			# self.session.openWithCallback(self.loading, MessageBox, _("Confirmar a criação dos picons"), MessageBox.TYPE_YESNO)

	def selecionarDiretorio(self):
		currentItem = self["config"].getCurrent()[1]
		if currentItem == config.plugins.Channel.pasta:
			self.session.openWithCallback(self.selecaoCallback,SelectDirectoryWindow,currentItem.value)

	def selecaoCallback(self,caminho):
		if caminho is None or caminho.strip() == '':
			return
		config.plugins.Channel.pasta.value=caminho

	def getPicons(self):
		from Components.Sources.ServiceList import ServiceList
		from enigma import eServiceReference, eServiceCenter, iServiceInformation
		import shutil

		currentServiceRef = self.session.nav.getCurrentlyPlayingServiceReference()
		servicelist = ServiceList("")
		servicelist.setRoot(currentServiceRef)
		canais = servicelist.getServicesAsList()

		servicehandler = eServiceCenter.getInstance()

		try:
			os.makedirs("/tmp/piconsTmp")
		except OSError as exception:
			pass

		piconsDir=config.plugins.Channel.pasta.value

		for item in canais:
		    canal = eServiceReference(item[0])
		    if canal:
			    nome = servicehandler.info(canal).getName(canal)
			    picon=canal.toString()[:-1].replace(":","_")+".png"
			    try:
			        shutil.copy(piconsDir+"/"+picon,"/tmp/piconsTmp/"+nome+".png")
			    except:
			        pass




class SelectDirectoryWindow(Screen):
	skin = """
		<screen name="SelectDirectoryWindow" position="center,center" size="560,320" title="Selecione o diretório">
		<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
		<widget name="currentDir" position="10,60" size="530,22" valign="center" font="Regular;22" />
		<widget name="filelist" position="0,100" zPosition="1" size="560,220" scrollbarMode="showOnDemand"/>
		<widget render="Label" source="key_red" position="0,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;20" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget render="Label" source="key_green" position="140,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;20" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>
		"""

	def __init__(self, session, currentDir):

		Screen.__init__(self, session)
		inhibitDirs = []
		self["filelist"] = FileList(currentDir, showDirectories=True, showFiles=False, inhibitMounts=[],
	                            inhibitDirs=inhibitDirs)
		self["actions"]=ActionMap(["WizardActions","DirectionActions","ColorActions","EPGSelectActions"],{
			"back":self.cancel,
			"left":self.left,
			"right":self.right,
			"up":self.up,
			"down":self.down,
			"ok":self.ok,
			"green":self.green,
			"red":self.cancel
		},-1)

		self["currentDir"] = Label()
		self["key_green"] = StaticText(_("OK"))
		self["key_red"] = StaticText(_("Cancel"))

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):

		self.updateCurrentDirectory()

	def cancel(self):

		self.close(None)

	def green(self):

		self.close(self["filelist"].getSelection()[0])

	def up(self):
		self["filelist"].up()
		self.updateCurrentDirectory()

	def down(self):
		self["filelist"].down()
		self.updateCurrentDirectory()

	def left(self):
		self["filelist"].pageUp()
		self.updateCurrentDirectory()

	def right(self):
		self["filelist"].pageDown()
		self.updateCurrentDirectory()

	def ok(self):
		if self["filelist"].canDescent():
			self["filelist"].descent()
			self.updateCurrentDirectory()

	def updateCurrentDirectory(self):
		currentDir = self["filelist"].getSelection()[0]
		if currentDir is None or currentDir.strip() == '':
			currentDir = "Invalid Location"
		self["currentDir"].setText(currentDir)