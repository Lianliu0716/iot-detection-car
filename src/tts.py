from gtts import gTTS
import os

tts = gTTS(text='左轉彎', lang='zh-TW')
tts.save('leftturn.mp3')
os.system('omxplayer -o local -p leftturn.mp3 > /dev/null 2>&1')

tts = gTTS(text='右轉彎', lang='zh-TW')
tts.save('rightturn.mp3')
os.system('omxplayer -o local -p leftturn.mp3 > /dev/null 2>&1')

tts = gTTS(text='抵達終點', lang='zh-TW')
tts.save('end.mp3')
os.system('omxplayer -o local -p leftturn.mp3 > /dev/null 2>&1')