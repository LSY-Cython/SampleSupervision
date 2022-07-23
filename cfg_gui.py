# 采样固有参数配置界面
import tkinter as tk
from tkinter.filedialog import askdirectory
import re
import configparser
global ip_entry, port_entry, id_entry, rtsp_entry, save_entry
global ip_label, port_label, id_label, rtsp_label, save_label
[ip_state, port_state, id_state, rtsp_state, save_state] = [0]*5

# tk文件夹路径选择方法
def select_path():
    img_path = askdirectory()
    save_entry.configure(state=tk.NORMAL)
    save_entry.delete(0, tk.END)
    save_entry.insert("insert", img_path)
    save_entry.configure(state=tk.DISABLED)
    return img_path

# 验证参数的合法性
def params_valid():
    global ip_state, port_state, id_state, rtsp_state, save_state
    ip_valid = re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", ip_entry.get())
    if ip_valid is not None:
        ip = ip_valid.group()  # PLC通讯地址
        ip_entry.configure(state=tk.DISABLED)
        ip_state = 1
    else:
        ip_label.configure(fg='red')
        ip_state = 0
    port_valid = re.match(r'^\d+$', port_entry.get())
    if port_valid is not None:
        port = port_valid.group()  # PLC端口
        port_entry.configure(state=tk.DISABLED)
        port_state = 1
    else:
        port_label.configure(fg='red')
        port_state = 0
    id_valid = re.match(r'^\d+$', id_entry.get())
    if id_valid is not None:
        slave_id = id_valid.group()  # modbus从机设备号
        id_entry.configure(state=tk.DISABLED)
        id_state = 1
    else:
        id_label.configure(fg='red')
        id_state = 0
    re_rtsp = re.compile(
        r'^(?:rtsp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)  # 用户名、密码、码流，忽略大小写
    rtsp_valid = re_rtsp.match(rtsp_entry.get())
    if rtsp_valid is not None:
        rtsp = rtsp_valid.group()  # rtsp相机地址
        rtsp_entry.configure(state=tk.DISABLED)
        rtsp_state = 1
    else:
        rtsp_label.configure(fg='red')
        rtsp_state = 0
    if len(save_entry.get()) == 0:  # 图像保存路径
        save_label.configure(fg='red')
        save_state = 0
    else:
        save_entry.configure(state=tk.DISABLED)
        save_state = 1

def reset_params():
    ip_entry.configure(state=tk.NORMAL)
    port_entry.configure(state=tk.NORMAL)
    id_entry.configure(state=tk.NORMAL)
    rtsp_entry.configure(state=tk.NORMAL)
    save_entry.configure(state=tk.NORMAL)
    save_entry.delete(0, tk.END)
    ip_entry.delete(0, tk.END)
    port_entry.delete(0, tk.END)
    id_entry.delete(0, tk.END)
    rtsp_entry.delete(0, tk.END)
    ip_label.configure(fg='black')
    port_label.configure(fg='black')
    id_label.configure(fg='black')
    rtsp_label.configure(fg='black')
    save_label.configure(fg='black')

# 确定完成设置后生成cfg文件并锁住配置
def confirm_params():
    if [ip_state, port_state, id_state, rtsp_state, save_state] == [1]*5:
        cfg_write()
    else:
        warn = tk.Tk()
        warn.title("警告")
        warn.geometry('200x50')
        warn_label = tk.Label(warn, text="未通过参数校验！", fg='red')
        warn_label.place(x=50, y=15)
        warn.mainloop()

# 生成参数配置文件
def cfg_write():
    config = configparser.ConfigParser()
    config.add_section("configuration")
    config.set("configuration", "PLC_IP", ip_entry.get())
    config.set("configuration", "PLC_port", port_entry.get())
    config.set("configuration", "slave_id", id_entry.get())
    config.set("configuration", "rtsp", rtsp_entry.get())
    config.set("configuration", "save_path", save_entry.get())
    config.write(open("cfg.ini", "w"))

# 采样参数配置(需要检验输入参数的合法性)
def cfg_params():
    global ip_entry, port_entry, id_entry, rtsp_entry, save_entry
    global ip_label, port_label, id_label, rtsp_label, save_label
    params = tk.Tk()
    params.title("采样参数配置")
    params.geometry('360x240')
    ip_label = tk.Label(params, text="PLC_IP：")
    ip_label.place(x=30, y=30)
    ip_entry = tk.Entry(params, width=25)
    ip_entry.place(x=120, y=30)
    port_label = tk.Label(params, text="PLC_port：")
    port_label.place(x=30, y=60)
    port_entry = tk.Entry(params, width=25)
    port_entry.place(x=120, y=60)
    id_label = tk.Label(params, text="slave_id：")
    id_label.place(x=30, y=90)
    id_entry = tk.Entry(params, width=25)
    id_entry.place(x=120, y=90)
    rtsp_label = tk.Label(params, text="rtsp相机地址：")
    rtsp_label.place(x=30, y=120)
    rtsp_entry = tk.Entry(params, width=25)
    rtsp_entry.place(x=120, y=120)
    save_label = tk.Label(params, text="图像保存路径：")
    save_label.place(x=30, y=150)
    save_entry = tk.Entry(params, width=25)
    save_entry.place(x=120, y=150)
    save_entry.configure(state=tk.DISABLED)
    save_button = tk.Button(params, width=6, text="路径选择", command=select_path)
    save_button.place(x=305, y=145)
    check_button = tk.Button(params, width=8, text="校验", command=params_valid)
    check_button.place(x=50, y=190)
    reset_button = tk.Button(params, width=8, text="重置", command=reset_params)
    reset_button.place(x=150, y=190)
    confirm_button = tk.Button(params, width=8, text="确定", command=confirm_params)
    confirm_button.place(x=250, y=190)
    params.mainloop()

if __name__ == "__main__":
    cfg_params()
