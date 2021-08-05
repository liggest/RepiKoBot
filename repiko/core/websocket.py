import websockets

#TODO
class WSWrapper:

    def __init__(self,url):
        self.ws=websockets.connect(url)

    