import ctypes
from ctypes import wintypes 
import psutil
import json
import keyboard
import time
import os
import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog

with open('config.json', 'r') as file:
    config = json.load(file)

process_name = "client.exe"

mana_addr = 0
mana_total_addr = 0
hp_addr = 0
hp_total_addr = 0
running = True

def get_key_code(key_name):
    try:
        key_code = keyboard.key_to_scan_codes(key_name)[0]
        return hex(key_code)
    except:
        return None

def get_pid_by_name(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            return proc.info['pid']
    return None

def get_value_addr(address):
    buffer = ctypes.c_int()
    try:
        ctypes.windll.kernel32.ReadProcessMemory(process_handle, address, ctypes.byref(buffer), ctypes.sizeof(buffer), None)
        return buffer.value
    except:
        print(f"Erro ao tentar ler o endereço {hex(address)}")
        return None

def read_memory(process_handle, address, size):
    """ Lê a memória de um processo no endereço especificado. """
    data = ctypes.create_string_buffer(size)
    bytes_read = wintypes.DWORD(0)
    success = ctypes.windll.kernel32.ReadProcessMemory(process_handle, ctypes.c_void_p(address), ctypes.byref(data), size, ctypes.byref(bytes_read))
    if success:
        return data.raw
    else:
        return None

def scan_addresses(target_value):
    start_address = 0x0A000000
    end_address = 0x0FFFFFFF
    chunk_size = 4096
    current_address = start_address
    found_addresses = []
    founded_counter = 0
    limit = 200

    while current_address < end_address:
        data = read_memory(process_handle, current_address, chunk_size)
        if data:
            for i in range(0, len(data), 4):  # Assumindo que estamos lendo valores inteiros de 4 bytes
                value = int.from_bytes(data[i:i+4], byteorder='little', signed=False)
                if value == target_value:
                    #print(f"{hex(current_address + i)}")
                    found_addresses.append((current_address + i))
                    founded_counter+=1
        current_address += chunk_size
        if(founded_counter>=limit):
            break

    if not found_addresses:
        print("Valor não encontrado.")
        return None

    return found_addresses

def scan_address_inputed(mana_input):
    list_addr = scan_addresses(mana_input)
    if len(list_addr) > 0:
        return list_addr
    else:
        print("Erro: Não foi possível localizar o endereço da MANA. Sua MANA estava cheia?")
        exit()

def scan_address_mana(list_addr, mana_input):
    global mana_addr
    #Obter da lista o endereço com o valor menor que o input
    while(mana_addr == 0):
        for addr in list_addr:
            value_addr = get_value_addr(addr)
            if (value_addr < mana_input):
                mana_addr = addr
                mana_total_addr = mana_addr + 8
                #teste pra verificar se pegou o addr correto da mana 
                if(get_value_addr(mana_total_addr) != mana_input):    
                    list_addr.remove(addr)
                    mana_addr = 0 #mantem o while e repete
                else:
                    return mana_addr
def clear_bars():
    label_hp['text'] = "HP\n-"
    label_mana['text'] = "MANA\n-"
    bar_hp['value'] = 0
    bar_mana['value'] = 0
    root.update()  # Atualiza a GUI

def pause_bot():
    global running
    running = False
    button_start.config(text="Iniciar BOT", command=play_bot)
    button_start.grid(row=2, column=0, columnspan=2, pady=20)
    clear_bars()

def play_bot():
    global mana_total_addr
    global hp_addr
    global hp_total_addr
    global mana_addr
    global running

    running = True
    button_start.config(text="Parar BOT", command=pause_bot)
    button_start.grid(row=2, column=0, columnspan=2, pady=20)

    while running:
        hp = get_value_addr(hp_addr)
        hp_total = get_value_addr(hp_total_addr)
        mana = get_value_addr(mana_addr)
        mana_total = get_value_addr(mana_total_addr)
        #print(f"HP:{hp}/{hp_total}   |   MANA:{mana}/{mana_total}", end="\r", flush=True)
        label_hp['text'] = f"HP\n{hp}/{hp_total}"
        label_mana['text'] = f"MANA\n{mana}/{mana_total}"
        bar_hp['value'] = (hp*100)/hp_total
        bar_mana['value'] = (mana*100)/mana_total
        root.update()  # Atualiza a GUI
        
        #triggers and hotkeys
        for trigger in config["triggers"]:
            if trigger["type"] == "hp":
                if hp < hp_total * (trigger["limit"]/100):
                    keyboard.press(trigger["hotkey"])
            elif trigger["type"] == "mana":
                if mana < mana_total * (trigger["limit"]/100):
                    keyboard.press(trigger["hotkey"])

def init_bot():
    global mana_addr
    global mana_total_addr
    global hp_addr
    global hp_total_addr
    mana_input = int(simpledialog.askstring("MANA", "ATENÇÃO: Sua MANA deve estar cheia para a macro funcionar.\nDigite sua MANA total:"))

    # Obtendo parametros
    # mana_input = int(input("ATENÇÃO: Sua MANA deve estar cheia para a macro funcionar.\nDigite sua Mana total: "))
    # if not mana_input:
    #     init_bot()

    button_start.grid_remove()
    label_msg.grid(row=2, column=0, columnspan=2, pady=20)
    label_msg['text'] = "Aguarde..."
    root.update()  # Atualiza a GUI

    #print("Aguarde...")
    list_addr = scan_address_inputed(mana_input)

    label_msg['text'] = "ATENÇÃO, Gaste um pouco de MANA."
    root.update()  # Atualiza a GUI
    #print("ATENÇÃO, Gaste um pouco de MANA.")
    mana_addr = scan_address_mana(list_addr, mana_input)
    if(mana_addr <= 0):
        print("Erro ao tentar obter o endereço da MANA.")
        exit()

    #os.system('cls')

    mana_total_addr = mana_addr + 8
    hp_addr = mana_addr - 1312 #Localiza endereço do hp apartir do da mana
    hp_total_addr = hp_addr + 8 

    label_msg.grid_remove()
    play_bot()





#ROTINA PRINCIPAL
pid = get_pid_by_name(process_name)

if pid is None:
    print(f"Processo '{process_name}' não encontrado.")
    exit()

#print(f"PID do processo '{process_name}': {pid}")

process_handle = ctypes.windll.kernel32.OpenProcess(0x0010, False, pid) #read only permission

if not process_handle:
    print("Falha ao abrir o processo.")
    exit()
#print(f"Processo {pid} aberto com sucesso.")


#init_bot()


#GUI
root = tk.Tk()
root.geometry("250x100")  # Define o tamanho da janela
root.title("Tibia BOT")

style = ttk.Style()
style.theme_use('default') 

style.configure('Green.Horizontal.TProgressbar', troughcolor='grey', background='green')
style.configure('Blue.Horizontal.TProgressbar', troughcolor='grey', background='blue')

label_hp = tk.Label(root, text="HP\n-")
label_hp.grid(row=0, column=0, padx=10, pady=1)
bar_hp = ttk.Progressbar(root, style='Green.Horizontal.TProgressbar', orient='horizontal', length=100, mode='determinate')
bar_hp.grid(row=1, column=0, padx=10, pady=1)

label_mana = tk.Label(root, text="MANA\n-")
label_mana.grid(row=0, column=1, padx=10, pady=1)
bar_mana = ttk.Progressbar(root, style='Blue.Horizontal.TProgressbar', orient='horizontal', length=100, mode='determinate')
bar_mana.grid(row=1, column=1, padx=10, pady=1)

button_start = tk.Button(root, text="Iniciar BOT", command=init_bot)
button_start.grid(row=2, column=0, columnspan=2, pady=20)

button_config = tk.Button(root, text="⚙", command=config)
button_config.grid(row=0, column=3, columnspan=2, pady=0)

label_msg = tk.Label(root, text="")

root.mainloop()
ctypes.windll.kernel32.CloseHandle(process_handle)