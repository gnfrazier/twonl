
import scipy.io.wavfile as wv
import pydub
import tinytag

#convert to wav
mp3_audio.export(latest+"unprocessed.wav", format="wav")

#read wav file
rate,audData=wv.read(latest+"unprocessed.wav")

# Calculate track time
track_time = (audData.shape[0] / rate)/60

mp3_audio = pydub.AudioSegment.from_mp3(mp3_file)
