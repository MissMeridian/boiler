import requests, os, shutil, logging
from pydub import AudioSegment
import numpy as np
import aubio
import coloredlogs

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
coloredlogs.install(level="DEBUG")

class AudioRequestError(Exception):
    '''This class is called when an issue occurs while requesting audio from the server.'''
    pass
    #log.error(f"AudioRequestError occurred in audioExtractor!")

class AudioFormatError(Exception):
    '''This class is called if the downloaded file does not match the MP3 MIME headers.'''
    #log.error(f"AudioFormatError occurred in audioExtractor!")
    pass

def download_mp3(url:str, path:str):
    '''Downloads the MP3 file at the desired URL with optimal exception handling to prevent unexpected errors.'''
    log.debug(f"Downloading alert audio from {url}")
    try:
        r = requests.get(url=url)
        if r.headers.get("Content-Type") == "audio/mpeg":
            with open(path, "wb") as file:
                file.write(r.content)
                file.close()
            log.debug(f"Audio downloaded successfully.")
        else:
            raise AudioFormatError
    except requests.ConnectionError:
        log.error(f"A connection error occurred while attempting to download MP3 audio file.", exc_info=True)
        raise AudioRequestError
    except requests.RequestException:
        log.error(f"An error occurred making the download request for the MP3 audio file.", exc_info=True)
        raise AudioRequestError
    except AudioFormatError:
        log.error(f"The requested URL did not resolve to a file with MPEG audio headers. ({url})", exc_info=False)
        raise AudioRequestError

def convert_mp3_to_wav(path_mp3:str, path_wav:str):
    '''Take a guess what this does.'''
    log.debug(f"Converting '{path_mp3}' to '{path_wav}'.")
    audio = AudioSegment.from_mp3(path_mp3)
    audio.set_frame_rate(16000)
    audio.export(path_wav, format="wav", parameters=["-ar", "16000"])
    log.debug(f"Conversion successful.")

def convert_wav_to_mp3(path_wav: str, path_mp3: str, bitrate="192k"):
    '''No, seriously, take a guess what it does.'''
    log.debug(f"Converting '{path_wav}' to '{path_mp3}'.")
    audio = AudioSegment.from_wav(path_wav)
    audio.export(path_mp3, format="mp3", bitrate=bitrate)
    log.debug(f"Conversion successful.")

def scan_attn(path_wav:str):
    '''This is really bad, and if you think you can do it better, PLEASE DO!! I AM BEGGING YOU.
    
    This functions "scans" for an 853/960hz attention tone by using the aubio library to gather pitch via MIDI units... In testing, the ATTN tone was always 81 (not in Hz). If you ask me what unit, I have no idea.
    It's consistent. It works. But it's not how it should be done. But it works, so. YOLO!
    
    Returns True if successful, and the cut_point in seconds.'''
    ## Audio analysis is difficult, and for some reason, trying to gather frequencies is seemingly impossible unless you want them on a graph.
    ## So I found some weird code on StackOverflow that doesn't exactly work as intended, but... it could work? So.
    win_s = 4096
    hop_s = 512 
    tone_min_freq = 77
    tone_max_freq = 83
    confirm_threshold = 80000 / hop_s # 5 seconds is 80,000 frames

    samplerate = 16000 # this is permanent with this setup
    s = aubio.source(path_wav, samplerate, hop_s)
    tolerance = 0.8

    pitch_o = aubio.pitch("yin", win_s, hop_s, samplerate)
    pitch_o.set_unit("midi")
    pitch_o.set_tolerance(tolerance)

    pitches = []
    confidences = []

    total_frames = 0
    i = 0
    hit_frames = 0
    last_hit_frame = 0
    confirmed_hit = False
    while True:
        samples, read = s()
        pitch = pitch_o(samples)[0]
        if tone_min_freq < pitch < tone_max_freq:
            hit_frames += 1
            #print(f"hit {hit_frames}")
            if hit_frames > confirm_threshold:
                log.debug(f"Confirmed tone at frame {total_frames}")
                confirmed_hit = True
                last_hit_frame = total_frames
        else:
            if hit_frames > 0:
                hit_frames = 0

        pitches += [pitch]
        confidence = pitch_o.get_confidence()
        confidences += [confidence]
        total_frames += read
        i += 1
        if read < hop_s: break

    duration = total_frames / samplerate
    log.debug(f"Total frames was {total_frames}. Duration: {duration}")
    cut_point = last_hit_frame / samplerate # this will get the point (in seconds) at which we will cut the audio.
    if confirmed_hit:
        log.info(f"Found an attention tone, ending at frame {last_hit_frame} ({cut_point} seconds)!")
    else:
        log.warning(f"Did not detect an attention tone in this audio.")
    return confirmed_hit, cut_point

def get_length(path_wav:str):
    '''Feed it a path to a WAV file and you get the duration in seconds.'''
    audio = AudioSegment.from_wav(path_wav)
    length = len(audio) / 1000
    log.debug(f"Got length of {path_wav}, it's {length} seconds.")
    return length

def cut_tail(path_wav:str, path_new_wav:str, cut_point):
    '''Trims off the trailing portion (in seconds) from the audio file.
    
    cut_point must be in seconds.'''
    log.debug(f"Trimming tail of WAV file ({path_wav}) at {cut_point} seconds.")    
    audio = AudioSegment.from_wav(path_wav)
    trimmed_audio = audio[:cut_point * 1000]
    trimmed_audio.export(path_new_wav, format="wav")
    log.debug(f"Exported as {path_new_wav}.")

def cut_lead(path_wav:str, path_new_wav:str, cut_point):
    '''Trims off the leading portion (in seconds) from the audio file.
    
    cut_point must be in seconds.'''
    log.debug(f"Trimming lead of WAV file ({path_wav}) at {cut_point} seconds.")
    audio = AudioSegment.from_wav(path_wav)
    trimmed_audio = audio[cut_point * 1000:]
    trimmed_audio.export(path_new_wav, format="wav")
    log.debug(f"Exported as {path_new_wav}.")

def trim_headers(directory:str, target_file:str):
    '''Complicated and kind of annoying logic to attempt to remove the attention tone and EOMs from an EAS_NET audio source. 
    
    directory should be the path leading to the folder with the audio file, and target_file needs to be the path leading to the audio file, including the directory.'''
    ## OH BOY!!!!
    
    ## First, we'll convert the received MP3 audio file to a WAV so that we can analyze it with scipy.
    path_temp_wav = os.path.join(directory, f"audio-temp.wav")
    convert_mp3_to_wav(target_file, path_temp_wav) # Saves audio.mp3 to audio-temp.wav
    scanned_ATTN, scanned_ATTN_cut = scan_attn(path_wav=path_temp_wav)
    trimmed_target_file = path_temp_wav
    if scanned_ATTN:
        trimmed_target_file = path_temp_wav
        cut_lead(path_wav=path_temp_wav,path_new_wav=trimmed_target_file,cut_point=scanned_ATTN_cut)
    #scanned_EOM = scan_EOM(path_wav=path_temp_wav) # I'll do this later, if necessary. For now I'm just going to cut off the last 4 seconds of audio.
    scanned_EOM = True
    if scanned_EOM:
        trimmed_target_file = path_temp_wav
        audio_length = get_length(path_temp_wav)
        cut_EOM_point = audio_length - 4 # subtract four seconds.
        cut_tail(path_wav=path_temp_wav, path_new_wav=trimmed_target_file,cut_point=cut_EOM_point)
    path_final_mp3 = os.path.join(directory, f"eas-audio.mp3")
    convert_wav_to_mp3(path_wav=trimmed_target_file,path_mp3=path_final_mp3)
    log.debug(f"Cleaning up temporary WAV file.")
    os.remove(path=path_temp_wav)



if __name__ == "__main__":
    #scan_attn(path_wav="alerts/86240/audio-temp.wav")
    trim_headers(directory="alerts\\86240", target_file="alerts\\86240\\audio.mp3")