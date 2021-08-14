import websockets

#TODO
class WS:

    def __init__(self,url):
        self.ws=websockets.connect(url)

    