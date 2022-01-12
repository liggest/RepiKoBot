from LSparser import *
from repiko.msg.part import MessagePart,Record,TTS

Command("-test1")
Command("-test2")

@Events.onCmd("test1")
def test1(_):
    return [Record("https://cdn.jsdelivr.net/gh/blacktunes/hiiro-button@master/public/voices/baba.mp3",cache=False)]

@Events.onCmd("test2")
def test2(_):
    return [TTS("聚集的祈愿将成为新生的闪耀之星，化作光芒闪耀的道路吧！\n同调召唤，飞翔吧，星尘龙！")]