import tkinter as tk
from threading import Thread
from tkinter import ttk, scrolledtext
from server.core import Server
from tester.info import devices_list



class ServerWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Server")
        self.root.geometry("600x400")

        self.server: Server = Server(self.log)
        self.server_configuration = ("127.0.0.1", 50000)


        #Server buttons
        do_not_ack = tk.Button(self.root, text="Configure server",
                                       command=self.configure)
        do_not_ack.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.server_state = tk.BooleanVar()
        server_state_box = tk.Checkbutton(self.root, text="Listen", variable=self.server_state,
                                          command=self.toggle_server)
        server_state_box.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        do_not_ack = tk.Button(self.root, text="Do not acknowledge the data message",
                                       command=lambda: self.choose_device())
        do_not_ack.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        # logs
        self.log_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=70, height=15)
        self.log_area.grid(row=3, column=0, padx=10, pady=5, sticky="w")

        self.log_scroll = tk.BooleanVar()
        self.log_scroll.set(1)
        log_scroll_box = tk.Checkbutton(self.root, text="Auto scroll down", variable=self.log_scroll)
        log_scroll_box.grid(row=4, column=0, padx=10, pady=5, sticky="w")

    def show(self):
        self.root.mainloop()

    def log(self, text):
        self.log_area.insert(tk.END, text + "\n")
        if self.log_scroll.get():
            self.log_area.see(tk.END)


    def configure(self):
        win = tk.Toplevel(self.root)
        win.title(f"Server configuration")
        win.geometry("300x100")

        tk.Label(win, text="IP:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ip_entry = tk.Entry(win)
        ip_entry.insert(0, self.server_configuration[0])
        ip_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        tk.Label(win, text="Port:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        port_entry = tk.Entry(win)
        port_entry.insert(0, self.server_configuration[1])
        port_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        def apply_configuration():
            def apply():
                try:
                    end_point = (ip_entry.get(), int(port_entry.get()))
                    self.server.configure(*end_point)
                    self.server_state.set(True)
                    self.server_configuration = end_point
                except Exception:
                    error_win = tk.Toplevel(win)
                    error_win.title(f"INFO")
                    error_win.geometry("200x100")

                    tk.Label(error_win, text="Configuration error").grid(row=0, column=0, padx=10, pady=5, sticky="w")

                    return

                win.destroy()

            Thread(target=apply, daemon=True).start()

        tk.Button(win, text="Apply", command=apply_configuration).grid(row=3, column=1, padx=10, pady=5, sticky="w")

    def toggle_server(self):
        if not self.check_configuration():
            return

        if self.server_state.get():
            self.server.listen()
        else:
            self.server.stop_listening()

    def check_configuration(self):
        if self.server.sock is None:
            win = tk.Toplevel(self.root)
            win.title(f"INFO")
            win.geometry("200x100")

            tk.Label(win, text="Server is not configured").grid(row=0, column=0, padx=10, pady=5, sticky="w")

            self.server_state.set(0)
            return False

        return  True


    def choose_device(self):
        if not self.check_configuration():
            return

        win = tk.Toplevel(self.root)
        win.title("Choose device")

        tk.Label(win, text="Choose Device:").grid(row=0, column=0, padx=10, pady=5, sticky="w")

        device_var = tk.StringVar()
        device_selecting_box = ttk.Combobox(win, values=devices_list, textvariable=device_var, state="readonly")
        device_selecting_box.current(1)
        device_selecting_box.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        (tk.Button(win, text="Next", command= lambda: (win.destroy(), self.stop_ack(device_var.get())))
         .grid(row=3, columnspan= 2, padx=10, pady=5))


    def stop_ack(self, device_type: str):
        if device_type not in self.server.connected_devices.keys():
            win = tk.Toplevel(self.root)
            win.title(f"INFO")
            win.geometry("200x100")

            tk.Label(win, text="This device not registered").grid(row=0, column=0, padx=10, pady=5, sticky="w")
            return

        self.server.stop_ack(device_type)




if __name__ == "__main__":
    window = ServerWindow()
    window.show()