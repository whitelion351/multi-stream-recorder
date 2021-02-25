import pickle
import requests
from threading import Thread
from time import time, sleep
import tkinter as tk
import subprocess


class MainWindow(tk.Tk):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.title("Lion Multi-Stream Recorder 1.0")
        self.font = ("helvetica", 10)
        self.update_delay = 0.1
        self.canvas = tk.Canvas(self, width=720, height=555, bg="#555555")
        self.canvas.pack()
        self.resizable(width=False, height=False)
        self.chunk_size = 4096

        self.available_decks = []
        self.control_window = ControlWindow(self)
        self.control_window.frame.place(x=10, y=10)
        self.deckA = PlayerWindow(self, player_id="A")
        self.deckB = PlayerWindow(self, player_id="B")
        self.deckC = PlayerWindow(self, player_id="C")
        self.deckD = PlayerWindow(self, player_id="D")
        y_pos = 120
        spacer = 110
        self.deckA.player_frame.place(x=10, y=y_pos)
        y_pos += spacer
        self.deckB.player_frame.place(x=10, y=y_pos)
        y_pos += spacer
        self.deckC.player_frame.place(x=10, y=y_pos)
        y_pos += spacer
        self.deckD.player_frame.place(x=10, y=y_pos)
        # self.master_volume_var = tk.StringVar()
        # self.master_volume_var.set(str(int(self.master_volume*100))+"%")
        # self.volume_down_button = tk.Button(self, font=self.font, text="-", command=self.master_volume_down)
        # self.volume_down_button.place(x=10, y=135, width=20, height=20)
        # self.volume_display_label = tk.Label(self, font=self.font, textvariable=self.master_volume_var)
        # self.volume_display_label.place(x=30, y=135, width=40, height=20)
        # self.volume_up_button = tk.Button(self, font=self.font, text="+", command=self.master_volume_up)
        # self.volume_up_button.place(x=70, y=135, width=20, height=20)
        # self.load_next_button = tk.Button(self, font=self.font, text="load next", command=self.load_next_in_queue)
        # self.load_next_button.place(x=100, y=135, width=70, height=20)
        # self.remove_next_button = tk.Button(self, font=self.font, text="remove next", command=self.remov_nxt_in_queue)
        # self.remove_next_button.place(x=180, y=135, width=90, height=20)
        # self.encoder1_options = self.select_encoder(1)
        # self.encoder1_status_label = tk.Button(self, font=self.font, text="Stream1", command=self.encoder1_options)
        # self.encoder1_status_label.place(x=600, y=135, width=60, height=20)
        # self.encoder1_indicator = tk.Label(self, bg="#000000")
        # self.encoder1_indicator.place(x=665, y=135, width=20, height=20)
        # self.encoder2_options = self.select_encoder(2)
        # self.encoder2_status_label = tk.Button(self, font=self.font, text="Stream2", command=self.encoder2_options)
        # self.encoder2_status_label.place(x=690, y=135, width=60, height=20)
        # self.encoder2_indicator = tk.Label(self, bg="#000000")
        # self.encoder2_indicator.place(x=755, y=135, width=20, height=20)
        # self.encoder_indicators = {"enc1": self.encoder1_indicator, "enc2": self.encoder2_indicator}
        # self.encoder_buffer = {"A": [], "B": []}
        # self.encoder_threads = {}
        # self.log_window = self.LogWindow(self)
        # self.log_window.log_frame.place(x=10, y=390)
        # self.encoder_options_window = self.EncoderWindow(self)
        # self.encoder_options_window.encoder_frame.place(anchor="center", relx=0.5, rely=0.5)
        # self.initialize = True


class ControlWindow:
    def __init__(self, root, width=700, height=65, bd=10, relief="ridge"):
        self.root = root
        self.font = ("helvetica", 10)
        self.frame = tk.Frame(root, width=width, height=height, bd=bd, relief=relief)
        self.record_start_button = tk.Button(self.frame, width=10, height=1, text="START ALL", command=self.start_all)
        self.record_start_button.place(x=10, y=10)
        self.record_stop_button = tk.Button(self.frame, width=10, height=1, text="STOP ALL", command=self.stop_all)
        self.record_stop_button.place(x=100, y=10)
        self.record_time_label_title = tk.Label(self.frame, width=10, height=1, text="ELAPSED")
        self.record_time_label_title.place(x=200, y=12)
        self.record_time_label_var = tk.StringVar()
        self.record_time_label_var.set("00:00:00")
        self.record_time_label = tk.Label(self.frame, width=7, height=1, textvariable=self.record_time_label_var)
        self.record_time_label.place(x=265, y=12)
        self.is_recording = False
        self.record_thread = None

    def start_all(self):
        if not self.is_recording:
            self.is_recording = True
            self.record_thread = Thread(name="recording_thread", target=self.recording_thread, daemon=True)
            self.record_thread.start()
        else:
            print("already recording")

    def stop_all(self):
        if self.is_recording is True:
            self.is_recording = False
        else:
            print("nothing to stop but i didn't check very good")

    def recording_thread(self):
        start_time = time()
        interval = 1
        players = [self.root.deckA, self.root.deckB, self.root.deckC, self.root.deckD]
        active_encoders = 0
        for player in players:
            if player.encoder.encoder_config["enabled"] is True:
                player.encoder.start()
                active_encoders += 1
        print(f"started {active_encoders} encoder{'s' if active_encoders != 1 else ''}")
        while self.is_recording:
            elapsed = int(time() - start_time)
            elapsed_hrs = (elapsed // 60) // 60
            elapsed_min = (elapsed // 60) % 60
            elapsed_sec = elapsed % 60
            elapsed_hrs = "0"+str(elapsed_hrs) if elapsed_hrs < 9 else str(elapsed_hrs)
            elapsed_min = "0"+str(elapsed_min) if elapsed_min < 9 else str(elapsed_min)
            elapsed_sec = "0"+str(elapsed_sec) if elapsed_sec < 9 else str(elapsed_sec)
            self.record_time_label_var.set(elapsed_hrs+":"+elapsed_min+":"+elapsed_sec)
            sleep(interval)
        active_encoders = 0
        for player in players:
            if player.encoder.encoder_thread is not None:
                player.encoder.stop()
                active_encoders += 1
        print(f"stopped {active_encoders} encoder{'s' if active_encoders != 1 else ''}")


class PlayerWindow:
    def __init__(self, root=None, width=700, height=100, bd=10, relief="ridge", player_id="no_id"):
        self.root = root
        self.font = ("helvetica", 10)
        self.txt_width = 50
        # self.height = height
        # self.bd = bd
        # self.relief = relief

        self.encoder = Encoder(self, player_id)

        self.player_id = player_id
        self.player_frame = tk.Frame(root, width=width, height=height, bd=bd, relief=relief)

        self.input_text_var = tk.StringVar()
        self.input_text_var.set(self.encoder.encoder_config["input_url"])
        self.input_text_label = tk.Entry(self.player_frame, width=self.txt_width, textvariable=self.input_text_var)
        self.input_text_label.place(x=10, y=10)
        self.set_input_button = tk.Button(self.player_frame, font=self.font, text="SET", command=self.set_input)
        self.set_input_button.place(x=320, y=10, width=40, height=20)

        self.output_text_var = tk.StringVar()
        self.output_text_var.set(self.encoder.encoder_config["output_filename"])
        self.output_text_label = tk.Entry(self.player_frame, width=self.txt_width, textvariable=self.output_text_var)
        self.output_text_label.place(x=10, y=35)
        self.set_output_button = tk.Button(self.player_frame, font=self.font, text="SET", command=self.set_output)
        self.set_output_button.place(x=320, y=35, width=40, height=20)

        self.enable_button_var = tk.BooleanVar()
        self.enable_button_var.set(self.encoder.encoder_config["enabled"])
        self.enable_button = tk.Checkbutton(self.player_frame, font=self.font,
                                            text="ENABLED", variable=self.enable_button_var, command=self.set_enable)
        self.enable_button.place(x=365, y=10)

        self.status_label_var = tk.StringVar()
        self.status_label_var.set("STATUS")
        self.status_label = tk.Label(self.player_frame, width=11, height=1,
                                     textvariable=self.status_label_var, bg="#FF0000")
        self.status_label.place(x=370, y=35)

    def set_input(self):
        self.encoder.encoder_config["input_url"] = self.input_text_var.get()
        self.encoder.save_encoder()

    def set_output(self):
        self.encoder.encoder_config["output_filename"] = self.output_text_var.get()
        self.encoder.save_encoder()

    def set_enable(self):
        self.encoder.encoder_config["enabled"] = self.enable_button_var.get()
        self.encoder.save_encoder()

    def set_status(self, text=None, fg=None, bg=None):
        if text is not None:
            self.status_label_var.set(text)
        if fg is not None:
            self.status_label.configure(fg=fg)
        if bg is not None:
            self.status_label.configure(bg=bg)


class Encoder:
    def __init__(self, player_window, p_id, input_url=None, output_filename=None):
        self.p_id = p_id
        self.player_window = player_window
        self.input_url = input_url
        self.output_filename = output_filename
        self.encoder_config = self.get_encoder_config(p_id, input_url, output_filename)
        self.encoder_thread = None
        self.stream_input_chunk_size = 4096  # 2048 default
        self.bit_rate = "64"

    def get_encoder_config(self, p_id, url, filename):
        try:
            config = pickle.load(open(p_id, "rb"))
        except (FileNotFoundError, TypeError) as e:
            print(f"output file {self.output_filename} error\n{e}")
            config = {"input_url": url, "output_filename": filename, "enabled": False}
            self.save_encoder(config)
        return config

    def set_encoder_config(self, url, filename):
        self.encoder_config = {"input_url": url, "output_filename": filename}

    def save_encoder(self, config=None):
        if config is None:
            config = self.encoder_config
        pickle.dump(config, open(self.p_id, "wb"))
        # print(f"encoder {self.p_id} saved")

    def start(self):
        self.encoder_thread = Thread(target=self.play_stream, daemon=True)
        self.encoder_thread.start()
        # print(f"encoder{self.p_id} started")

    def stop(self):
        conditions = ["stopped", "connect failed", "connect refused"]
        if self.player_window.status_label_var.get() not in conditions:
            self.player_window.set_status(text="stopping", fg="#000000", bg="#FFFF00")
            # print(f"encoder{self.p_id} stopping")
        else:
            pass
            # print(f"encoder{self.p_id} was already stopped")

    def play_stream(self):
        path = self.encoder_config["input_url"]
        output_file = self.encoder_config["output_filename"]
        self.player_window.set_status(text="starting", fg="#000000", bg="#FFFF00")

        headers = {"user-agent": "LionMultiRecorder1.0", "Icy-MetaData": "1"}
        try:
            resp = requests.get(path, headers=headers, stream=True)
        except requests.exceptions.ConnectionError:
            print("Could not connect to", path)
            self.player_window.set_status(text="connect failed", fg="#FFFFFF", bg="#FF0000")
            return
        if resp.status_code != 200:
            print(f"encoder{self.p_id} server returned response code", resp.status_code)
            resp.close()
            self.player_window.set_status(text="connect refused", fg="#FFFFFF", bg="#FF0000")
            return
        elif "icy-name" in resp.headers.keys():
            self.player_window.input_text_var.set(resp.headers["icy-name"])
        metaint_header = "icy-metaint"
        if metaint_header in resp.headers.keys():
            metaint_value = int(resp.headers[metaint_header])
        else:
            metaint_value = 0
        connected = True
        data = resp.iter_content()
        pad_byte = b'\x00'.decode()
        ext_index = str(output_file).find(".")
        bit_rate_string = self.bit_rate+"k"
        final_filename = str(int(time()))+"_"+output_file
        ff_proc = subprocess.Popen(["ffmpeg", "-hide_banner", "-i", "pipe:",
                                    "-f", output_file[-3:], "-ab", bit_rate_string, final_filename],
                                   stdin=subprocess.PIPE, stderr=subprocess.PIPE)

        # stdout_thread = Thread(target=self.read_stdout, args=[ff_proc.stdout], daemon=True)
        stderr_thread = Thread(target=self.read_stderr, args=[ff_proc.stderr], daemon=True)
        # stdout_thread.start()
        stderr_thread.start()
        stream_output = bytes()
        self.player_window.set_status(text="recording", fg="#000000", bg="#00FF00")

        while connected and (self.player_window.status_label_var.get() != "stopping" and
                             self.player_window.status_label_var.get() != "stopped"):
            try:
                for _ in range(metaint_value if metaint_value > 0 else 1):
                    stream_output += next(data)
                    if len(stream_output) == self.stream_input_chunk_size:
                        ff_proc.stdin.write(stream_output)
                        stream_output = bytes()
                        # sleep(0.005)
                if metaint_value > 0:
                    d = next(data)
                    meta_counter_end = int.from_bytes(d, byteorder="little")
                    meta_counter = 0
                    metadata_bytes = bytes()
                    while meta_counter < meta_counter_end * 16:
                        metadata_bytes += next(data)
                        meta_counter += 1
                    decoded = metadata_bytes.decode()
                    decoded = decoded.rstrip(pad_byte)
                    if decoded != "":
                        song_title = decoded
                        self.player_window.input_text_var.set(song_title[13:].rstrip("\';"))
            except StopIteration:
                connected = False
                print("encoder{} lost connection to {}".format(self.p_id, path))
        self.player_window.input_text_var.set(self.encoder_config["input_url"])
        self.player_window.set_status(text="stopped", fg="#000000", bg="#FF0000")
        # print(f"encoder{self.p_id} closing stream...")
        ff_proc.kill()
        resp.close()
        # stdout_thread.join()
        stderr_thread.join()
        print(f"encoder{self.p_id} closed")

    def read_stderr(self, err):
        # print(f"encoder{self.p_id} error thread opened")
        while self.player_window.status_label_var.get() != "stopped":
            err.readline().decode().rstrip("\n")
        # print(f"encoder{self.p_id} error thread closed")


if __name__ == '__main__':
    app_window = MainWindow()
    app_window.mainloop()

# hot917fm
# https://stream.zeno.fm/643udufw1ceuv.mp3

# star106
# http://184.154.43.106:8384/stream

# 100jamz
# https://ice66.securenetsystems.net/100JAMZ?playSessionID=5F5C483D-CEBC-810A-7E7DBE3C57C03DF2

# guardianradio
# http://tngrgroup.streamcomedia.com:8788/guardianradio
