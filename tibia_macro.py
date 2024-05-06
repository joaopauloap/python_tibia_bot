import ctypes
from ctypes import wintypes 
import psutil
import json
import keyboard
import time
import sys
import os
import win32api
import win32process
import win32con

with open('config.json', 'r') as file:
    config = json.load(file)

process_name = "client.exe"


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

def getAddressValue(address):
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
    start_address = 0x00000000
    end_address = 0x7FFFFFFF
    chunk_size = 4096
    current_address = start_address
    found_addresses = []
    founded_counter = 0
    limit = 40

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

def find_address_minor_value(value_x, addresses, margin=500):
    founded_addresses = []
    for addr in addresses:
        addrValue = getAddressValue(addr)
        if (addrValue < value_x) and ((value_x - addrValue) < margin):
            founded_addresses.append(addr)
    
    return founded_addresses



#Rotina principal    
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

# Obtendo parametros
print("Seu HP e MANA devem estar cheios para continuar.") 
# hp_input = int(input("Digite seu HP: "))
# mana_input = int(input("Digite sua Mana: "))
hp_input = 4850
mana_input = 1525
print("Aguarde...")

listHpAddr1 = scan_addresses(hp_input)
listManaAddr1 = scan_addresses(mana_input)

if (len(listHpAddr1) == 0) or (len(listManaAddr1) == 0):
    print("Erro: Não foi possível localizar os endereços!")
    exit()

print("ATENÇÃO, CALIBRAGEM! Perca um pouco de HP e MANA...")

listHpAddr2 = []
listManaAddr2 = []

while (len(listHpAddr2) <= 0) or (len(listManaAddr2) <= 0):
    if len(listHpAddr2) == 0:
        listHpAddr2 = find_address_minor_value(hp_input, listHpAddr1)
    if len(listManaAddr2) == 0:
        listManaAddr2 = find_address_minor_value(mana_input, listManaAddr1)

os.system('cls')

while True:
    hp = getAddressValue(listHpAddr2[0])
    mana = getAddressValue(listManaAddr2[0])
    print(f"hp:{hp}  |  mana:{mana}", end="\r", flush=True)
    
    #triggers and hotkeys

    for trigger in config["triggers"]:
        if trigger["type"] == "hp":
            if hp < hp_input * (trigger["limit"]/100):
                keyboard.press(trigger["hotkey"])
        elif trigger["type"] == "mana":
            if mana < mana_input * (trigger["limit"]/100):
                keyboard.press(trigger["hotkey"])

    time.sleep(0.2)
    #closes
ctypes.windll.kernel32.CloseHandle(process_handle)