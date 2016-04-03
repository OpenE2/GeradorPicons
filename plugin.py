from Plugins.Plugin import PluginDescriptor

import utils
from geradorpicons import PrincipalScreen


# Function main
def main(session, **kwargs):
    session.open(PrincipalScreen)


# Plugin descriptor, name, icon, etc.
def Plugins(**kwargs):
    return [
        PluginDescriptor(where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main, icon="plugin.png", name=utils._pluginNome, description="Gere picons a partir dos seus canais"),
        PluginDescriptor(where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main, icon="plugin.png", name=utils._pluginNome, description="Gere picons a partir dos seus canais")

      ]