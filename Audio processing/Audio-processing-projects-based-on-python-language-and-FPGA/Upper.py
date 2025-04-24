import socket
import pyaudio
import threading
import tkinter as tk
from tkinter import messagebox

# Audio stream parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
UDP_IP = "192.168.1.11"  # FPGA's IP address
UDP_PORT_SEND = 8080
UDP_PORT_RECEIVE = 8081
END_SIGNAL = b'__END__'

class AudioStreamer:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_receive = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_receive.bind(("0.0.0.0", UDP_PORT_RECEIVE))
        self.running = False
        self.output_file = None
        self.receiving = False

    def start_stream(self):
        self.stream = self.audio.open(format=FORMAT, channels=CHANNELS,
                                      rate=RATE, input=True, output=True,
                                      frames_per_buffer=CHUNK)
        self.running = True
        self.output_file = open("received_audio.wav", "wb")  # Open the file to save received audio data
        self.send_thread = threading.Thread(target=self.send_audio)
        self.send_thread.start()

    def stop_stream(self):
        self.running = False
        self.send_thread.join()
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        self.sock_send.sendto(END_SIGNAL, (UDP_IP, UDP_PORT_SEND))  # Send end signal to FPGA
        self.sock_send.close()

        # Start receiving the audio data back from FPGA
        self.receiving = True
        self.receive_thread = threading.Thread(target=self.receive_audio)
        self.receive_thread.start()
        self.receive_thread.join()
        self.output_file.close()  # Close the output file
        self.sock_receive.close()

    def send_audio(self):
        while self.running:
            data = self.stream.read(CHUNK)
            self.sock_send.sendto(data, (UDP_IP, UDP_PORT_SEND))

    def receive_audio(self):
        while self.receiving:
            data, addr = self.sock_receive.recvfrom(CHUNK * 2)
            if data == END_SIGNAL:
                break
            self.stream.write(data)
            self.output_file.write(data)  # Save received audio data to file
        self.receiving = False

class App:
    def __init__(self, root):
        self.streamer = AudioStreamer()
        self.root = root
        self.root.title("Audio Streamer")
        
        self.start_button = tk.Button(root, text="Start", command=self.start_stream)
        self.start_button.pack(pady=20)
        
        self.stop_button = tk.Button(root, text="Stop", command=self.stop_stream)
        self.stop_button.pack(pady=20)
        self.stop_button["state"] = "disabled"

    def start_stream(self):
        self.streamer.start_stream()
        self.start_button["state"] = "disabled"
        self.stop_button["state"] = "normal"

    def stop_stream(self):
        self.streamer.stop_stream()
        self.start_button["state"] = "normal"
        self.stop_button["state"] = "disabled"
        messagebox.showinfo("Info", "Audio saved to received_audio.wav")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()