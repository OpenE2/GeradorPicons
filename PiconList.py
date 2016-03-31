from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
from Tools.LoadPixmap import LoadPixmap
from enigma import eListboxPythonMultiContent, gFont,BT_SCALE,BT_KEEP_ASPECT_RATIO

selectionpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/selectioncross.png"))

def PluginCategoryComponent(name, png, width=440):
	return [
		name,
		MultiContentEntryText(pos=(5, 5), size=(width-80, 25), font=0, text=name)
		# MultiContentEntryPixmapAlphaTest(pos=(10, 0), size=(60, 50), png = png)
	]

def PluginDownloadComponent(picon, width=440):

	# png = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/plugin.png"))
	# png = LoadPixmap(picon.path)
	res= [
		picon,
		MultiContentEntryPixmapAlphaTest(pos=(80, 0), size=(140, 100), png = picon.png, flags = BT_SCALE | BT_KEEP_ASPECT_RATIO)
	]

	if picon.selected:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 0, 0, 30, 30, selectionpng))

	return res
	

class PluginList(MenuList):
	def __init__(self, list, enableWrapAround=False):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setFont(1, gFont("Regular", 14))
		self.l.setItemHeight(100)