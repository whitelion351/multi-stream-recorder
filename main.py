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
        self.update_delay = 0.5
        self.canvas = tk.Canvas(self, width=720, height=555, bg="#555555")
        self.canvas.pack()
        self.resizable(width=False, height=False)
        self.chunk_size = 4096

        self.control_window = ControlWindow(self)
        self.control_window.frame.place(x=10, y=10)

        self.deckA = PlayerWindow(root=self, player_id="A")
        self.deckB = PlayerWindow(root=self, player_id="B")
        self.deckC = PlayerWindow(root=self, player_id="C")
        self.deckD = PlayerWindow(root=self, player_id="D")
        y_pos = 120
        spacer = 110
        self.deckA.player_frame.place(x=10, y=y_pos)
        y_pos += spacer
        self.deckB.player_frame.place(x=10, y=y_pos)
        y_pos += spacer
        self.deckC.player_frame.place(x=10, y=y_pos)
        y_pos += spacer
        self.deckD.player_frame.place(x=10, y=y_pos)


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
        self.start_time = time()
        self.active_encoders = 0
        self.ui_update_thread = Thread(target=self.ui_update_func, daemon=True)
        self.ui_update_thread.start()

    def start_all(self):
        players = [self.root.deckA, self.root.deckB, self.root.deckC, self.root.deckD]
        started_encoders = 0
        active_encoders = 0
        for player in players:
            if player.enabled:
                if player.encoder.status in ["stopped", "connect_failed", "connect refused"]:
                    player.encoder.start()
                    started_encoders += 1
                else:
                    print(f"encoder{player.p_id} abort start. status = {player.encoder.status}")
                    if player.encoder.status in ["recording", "starting"]:
                        active_encoders += 1
        print(f"started {started_encoders} encoder{'s' if started_encoders != 1 else ''}")
        if started_encoders > 0 and active_encoders == 0:
            self.start_time = time()
        self.active_encoders = active_encoders

    def stop_all(self):
        players = [self.root.deckA, self.root.deckB, self.root.deckC, self.root.deckD]
        active_encoders = 0
        for player in players:
            if player.encoder.status != "stopped":
                active_encoders += 1
                player.encoder.stop()
        print(f"stopped {active_encoders} encoder{'s' if active_encoders != 1 else ''}")
        self.active_encoders = active_encoders

    def ui_update_func(self):
        while True:
            sleep(self.root.update_delay)
            actives = 0
            for player in [self.root.deckA, self.root.deckB, self.root.deckC, self.root.deckD]:
                player.set_status(text=player.encoder.status)
                if player.encoder.status != "stopped":
                    actives += 1
            if actives > 0:
                self.record_time_label_var.set(self.get_elapsed_time_string())

    def get_elapsed_time_string(self):
        elapsed = int(time() - self.start_time)
        elapsed_hrs = (elapsed // 60) // 60
        elapsed_min = (elapsed // 60) % 60
        elapsed_sec = elapsed % 60
        elapsed_hrs = "0" + str(elapsed_hrs) if elapsed_hrs <= 9 else str(elapsed_hrs)
        elapsed_min = "0" + str(elapsed_min) if elapsed_min <= 9 else str(elapsed_min)
        elapsed_sec = "0" + str(elapsed_sec) if elapsed_sec <= 9 else str(elapsed_sec)
        return elapsed_hrs+":"+elapsed_min+":"+elapsed_sec


class PlayerWindow:
    def __init__(self, root=None, width=700, height=100, bd=10, relief="ridge", player_id="no_id"):
        self.root = root
        self.font = ("helvetica", 10)
        self.txt_width = 50
        self.encoder = Encoder(self, player_id)
        self.enabled = self.encoder.encoder_config["enabled"]

        self.p_id = player_id
        self.player_frame = tk.Frame(root, width=width, height=height, bd=bd, relief=relief)

        self.input_text_var = tk.StringVar()
        self.input_text_var.set(self.encoder.encoder_config["input_url"])
        self.input_text_label = tk.Entry(self.player_frame, font=self.font, width=self.txt_width,
                                         textvariable=self.input_text_var)
        self.input_text_label.place(x=10, y=5)

        self.output_text_var = tk.StringVar()
        self.output_text_var.set(self.encoder.encoder_config["output_filename"])
        self.output_text_label = tk.Entry(self.player_frame, font=self.font, width=self.txt_width,
                                          textvariable=self.output_text_var)
        self.output_text_label.place(x=10, y=30)

        self.metadata_label_var = tk.StringVar()
        self.metadata_label = tk.Label(self.player_frame, font=self.font, width=43, bg="#FFFFFF",
                                       textvariable=self.metadata_label_var)
        self.metadata_label.place(x=10, y=55)

        self.save_config_button = tk.Button(self.player_frame, font=self.font, text="SAVE", command=self.save_config)
        self.save_config_button.place(x=370, y=6, width=40, height=20)

        self.enable_button_var = tk.BooleanVar()
        self.enable_button_var.set(self.encoder.encoder_config["enabled"])
        self.enable_button = tk.Checkbutton(self.player_frame, font=self.font,
                                            text="ENABLED", variable=self.enable_button_var, command=self.set_enable)
        self.enable_button.place(x=420, y=4)

        self.status_label_var = tk.StringVar()
        self.status_label_var.set("STATUS")
        self.status_label = tk.Label(self.player_frame, width=11, height=1,
                                     textvariable=self.status_label_var, bg="#FF0000")
        self.status_label.place(x=370, y=35)

    def set_enable(self):
        self.enabled = self.enable_button_var.get()
        self.save_config()

    def save_config(self):
        url = self.input_text_var.get()
        filename = self.output_text_var.get()
        en = self.enabled
        self.encoder.encoder_config = {"input_url": url, "output_filename": filename, "enabled": en}
        self.encoder.save_encoder()

    def set_status(self, text=None, fg=None, bg=None):
        if text is not None:
            self.status_label_var.set(text)
        if fg is not None:
            self.status_label.configure(fg=fg)
        if bg is not None:
            self.status_label.configure(bg=bg)
        elif text == "stopped":
            self.status_label.configure(bg="#FF0000")
        elif text == "stopping" or text == "starting":
            self.status_label.configure(bg="#FFFF00")
        elif text == "recording":
            self.status_label.configure(bg="#00FF00")
        else:
            self.status_label.configure(bg="#8888FF")


class Encoder:
    def __init__(self, player_window, p_id, input_url=None, output_filename=None):
        self.p_id = p_id
        self.player_window = player_window
        self.input_url = input_url
        self.output_filename = output_filename
        self.encoder_config = None
        self.get_encoder_config(p_id, input_url, output_filename)
        self.encoder_thread = None
        self.status = "stopped"
        self.stream_input_chunk_size = 1024  # 2048 default
        self.bit_rate = "64"

    def get_encoder_config(self, p_id, url, filename):
        try:
            config = pickle.load(open(p_id, "rb"))
        except (FileNotFoundError, TypeError) as e:
            print(f"output file {self.output_filename} error\n{e}")
            config = {"input_url": url, "output_filename": filename, "enabled": False}
            self.save_encoder(config)
        self.encoder_config = config

    def save_encoder(self, config=None):
        if config is not None:
            self.encoder_config = config
        pickle.dump(self.encoder_config, open(self.p_id, "wb"))

    def start(self):
        self.encoder_thread = Thread(target=self.play_stream, daemon=True)
        self.encoder_thread.start()

    def stop(self):
        condition = self.status
        if condition in ["recording", "starting"]:
            self.status = "stopping"
        else:
            print(f"encoder{self.p_id} was {condition} so not stopped")

    def play_stream(self):
        path = self.encoder_config["input_url"]
        output_file = self.encoder_config["output_filename"]
        self.status = "starting"
        headers = {"user-agent": "LionMultiRecorder1.0", "Icy-MetaData": "1"}
        try:
            resp = requests.get(path, headers=headers, stream=True)
        except requests.exceptions.ConnectionError:
            print("Could not connect to", path)
            self.status = "connect failed"
            return
        if resp.status_code != 200:
            print(f"encoder{self.p_id} server returned response code", resp.status_code)
            resp.close()
            self.status = "connect refused"
            return
        elif "icy-name" in resp.headers.keys():
            self.player_window.metadata_label_var.set(resp.headers["icy-name"])
        metaint_header = "icy-metaint"
        if metaint_header in resp.headers.keys():
            metaint_value = int(resp.headers[metaint_header])
        else:
            metaint_value = 0
        data = resp.iter_content()
        pad_byte = b'\x00'.decode()
        bit_rate_string = self.bit_rate+"k"

        final_filename = str(int(time()))+"_"+output_file
        # final_filename = "test_"+output_file
        ff_proc = subprocess.Popen(["ffmpeg", "-hide_banner", "-i", "pipe:",
                                    "-f", output_file[-3:], "-ab", bit_rate_string, final_filename],
                                   stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        stderr_thread = Thread(target=self.read_stderr, args=[ff_proc.stderr], daemon=True)
        stderr_thread.start()
        stream_output = bytes()

        self.status = "recording"
        connected = True
        while connected is True and self.status == "recording":
            try:
                for _ in range(metaint_value if metaint_value > 0 else self.stream_input_chunk_size):
                    stream_output += next(data)
                    if len(stream_output) >= self.stream_input_chunk_size:
                        ff_proc.stdin.write(stream_output)
                        stream_output = bytes()
                        # if self.p_id == "A":
                        #     print(f"encoder{self.p_id} writing at {int(time())}")
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
                        self.player_window.metadata_label_var.set(song_title[13:].rstrip("\';"))
            except StopIteration:
                connected = False
                print("encoder{} lost connection to {}".format(self.p_id, path))

        # self.player_window.input_text_var.set(self.encoder_config["input_url"])
        self.status = "stopped"
        print(f"encoder{self.p_id} closing stream...")
        ff_proc.kill()
        resp.close()
        # stdout_thread.join()
        stderr_thread.join()
        print(f"encoder{self.p_id} closed")

    def read_stderr(self, err):
        # print(f"encoder{self.p_id} error thread opened")
        while self.status in ["recording", "starting"]:
            err.readline().decode().rstrip("\n")
            # err_output = err.readline().decode().rstrip("\n")
            # if self.p_id == "A":
            #     print(f"encoder{self.p_id} {err_output}")
        # print(f"encoder{self.p_id} error thread closed")


if __name__ == '__main__':
    app_window = MainWindow()
    app_window.mainloop()

# hot 917 fm
# https://stream.zeno.fm/643udufw1ceuv.mp3

# star 106
# http://184.154.43.106:8384/stream

# 100 jamz
# https://ice66.securenetsystems.net/100JAMZ?playSessionID=5F5C483D-CEBC-810A-7E7DBE3C57C03DF2

# guardian radio
# http://tngrgroup.streamcomedia.com:8788/guardianradio
