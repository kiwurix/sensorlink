import tkinter as tk
from tkinter import ttk, scrolledtext
from messages import DataMessage
from tester.device import Device
from tester.info import devices_list
from threading import Thread
from helpers import parse_parameters, calculate_checksum
from tester.info import devices, generate_info
from datetime import datetime
from enum import Enum


class Options(Enum):
    CUSTOM_DATA = "auto send"
    CHECKSUM_ERROR = "checksum error"
    ACTIVITY_MECHANISM_CHECK = "activity check"


class TestWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Test program")
        self.root.geometry("600x320")

        self.devices: dict[str, Device] = {device_type : Device(device_type, self.log) for device_type in devices_list}
        self.devices_configuration = ("127.0.0.1", 50000)

        # tabs
        tabs = ttk.Notebook(self.root)
        tabs.grid(row=0, column=0, sticky="nsew")

        self.test_frame = ttk.Frame(tabs)
        tabs.add(self.test_frame, text="Test program")

        self.log_frame = ttk.Frame(tabs)
        tabs.add(self.log_frame, text="Logs")


        #test program buttons
        #configure
        configure_button = tk.Button(self.test_frame, text="Configure devices",
                                       command=self.configure)
        configure_button.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        #auto send button
        self.auto_send_var = tk.BooleanVar()
        auto_send_box = tk.Checkbutton(self.test_frame, text="Auto send", variable=self.auto_send_var,
                                       command=self.toggle_autosend)
        auto_send_box.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        # custom send button
        custom_send_button = tk.Button(self.test_frame, text="Send custom message",
                                       command=lambda: self.choose_device(Options.CUSTOM_DATA))
        custom_send_button.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        #checksum error button
        checksum_error_button = tk.Button(self.test_frame, text="Checksum error",
                                       command=lambda: self.choose_device(Options.CHECKSUM_ERROR))
        checksum_error_button.grid(row=3, column=0, padx=10, pady=5, sticky="w")

        activity_mechanism_check_button = tk.Button(self.test_frame, text="Sensor activity mechanism check",
                                       command=lambda: self.choose_device(Options.ACTIVITY_MECHANISM_CHECK))
        activity_mechanism_check_button.grid(row=4, column=0, padx=10, pady=5, sticky="w")

        # logs
        self.log_area = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, width=70, height=15)
        self.log_area.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.log_scroll = tk.BooleanVar()
        self.log_scroll.set(1)
        log_scroll_box = tk.Checkbutton(self.log_frame, text="Auto scroll down", variable=self.log_scroll)
        log_scroll_box.grid(row=4, column=0, padx=10, pady=5, sticky="w")



    def show(self):
        self.root.mainloop()

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        if self.log_scroll.get():
            self.log_area.see(tk.END)

    def configure(self):
        win = tk.Toplevel(self.root)
        win.title("Devices configuration")
        win.geometry("300x100")

        tk.Label(win, text="IP:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ip_entry = tk.Entry(win)
        ip_entry.insert(0, self.devices_configuration[0])
        ip_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        tk.Label(win, text="Port:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        port_entry = tk.Entry(win)
        port_entry.insert(0, self.devices_configuration[1])
        port_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        def apply_configuration():
            try:
                end_point = (ip_entry.get(), int(port_entry.get()))
                if end_point[0].count(".") != 3:
                    raise ValueError
                else:
                    for octet in end_point[0].split("."):
                        int(octet)
            except ValueError:
                error_win = tk.Toplevel(win)
                error_win.title(f"INFO")
                error_win.geometry("200x100")

                tk.Label(error_win, text="Configuration error").grid(row=0, column=0, padx=10, pady=5, sticky="w")

                return

            self.devices_configuration = end_point

            for _, device in self.devices.items():
                device.configure(*end_point)

            win.destroy()


        tk.Button(win, text="Apply", command=apply_configuration).grid(row=3, column=1, padx=10, pady=5, sticky="w")

    def toggle_autosend(self):
        if not self.check_configuration():
            return

        if self.auto_send_var.get():

            for _, device in self.devices.items():
                device.start_auto_sending()
        else:
            for _, device in self.devices.items():
                device.stop_auto_sending()


    def choose_device(self, option: Options):
        if not self.check_configuration():
            return

        win = tk.Toplevel(self.root)
        win.title("Choose device")


        tk.Label(win, text="Choose Device:").grid(row=0, column=0, padx=10, pady=5, sticky="w")

        device_var = tk.StringVar()
        device_selecting_box = ttk.Combobox(win, values=devices_list, textvariable=device_var, state="readonly")
        device_selecting_box.current(1)
        device_selecting_box.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        if option == Options.CUSTOM_DATA:
            (tk.Button(win, text="Next", command= lambda: (win.destroy(), self.custom_message_window(device_var.get())))
             .grid(row=3, columnspan= 2, padx=10, pady=5))
        elif option == Options.CHECKSUM_ERROR:
            (tk.Button(win, text="Next", command=lambda: (win.destroy(), self.make_checksum_error(device_var.get())))
             .grid(row=3, columnspan= 2, padx=10, pady=5))
        else:
            (tk.Button(win, text="Next", command=lambda: (win.destroy(), self.activity_mechanism_check(device_var.get())))
             .grid(row=3, columnspan= 2, padx=10, pady=5))



    def custom_message_window(self, device_var: str):
        win = tk.Toplevel(self.root)
        win.title("Send Custom Data")

        tk.Label(win, text="Enter data:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        data_entry = tk.Entry(win, width= 60)
        data_entry.insert(0, generate_info(device_var))
        data_entry.grid(row=1, column= 0, padx=10, pady=5, sticky="w")

        low_battery_var = tk.BooleanVar()
        low_battery_box = tk.Checkbutton(win, text="Low battery", variable=low_battery_var)
        low_battery_box.grid(row=2, column=0, padx=10, pady=5, sticky="w")



        def send_data():
            entered_text = data_entry.get()
            entered_parameters = parse_parameters(entered_text)
            low_battery = low_battery_var.get()

            device = self.devices[device_var]
            device_type = device.device_type

            required_params = devices[device_type]
            
            for param in required_params.keys():
                if param not in entered_parameters:
                    info_win = tk.Toplevel(self.root)
                    info_win.title(f"Parameter '{param}' not entered")
                    info_win.geometry("400x100")

                    tk.Label(info_win, text=f"Valid range: {required_params[param]['min']} - {required_params[param]['max']} {required_params[param]['unit']}").grid(row=0, column=0, padx=10, pady=5, sticky="w")

                    return

            data_msg = DataMessage(device_type, datetime.now().timestamp(), low_battery, self.devices[device_type].token, entered_text, calculate_checksum(entered_text))
            device.last_data_message = data_msg
            device.send_data_message()

            win.destroy()

        tk.Button(win, text="Send", command=send_data).grid(row=3, columnspan= 2, padx=10, pady=5)

    def make_checksum_error(self, device_type: str):
        device = self.devices[device_type]

        device.make_checksum_error()

    def activity_mechanism_check(self, device_type: str):
        device = self.devices[device_type]

        Thread(target= device.activity_mechanism_check, daemon= True).start()


    def check_configuration(self):
        if None in (device.sock for _ ,device in self.devices.items()):
            win = tk.Toplevel(self.root)
            win.title(f"INFO")
            win.geometry("200x100")

            tk.Label(win, text="Devices are not configured").grid(row=0, column=0, padx=10, pady=5, sticky="w")

            self.auto_send_var.set(0)
            return False

        return True


if __name__ == "__main__":
    window = TestWindow()
    window.show()