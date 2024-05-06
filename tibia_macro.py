import ctypes
import psutil
import json
import keyboard
import time
import sys
import os
from ctypes import wintypes
import win32api
import win32process
import win32con

with open('config.json', 'r') as file:
    data = json.load(file)

process_name = "client.exe"

hotkey_hp = data['hotkeys']['hp']
hotkey_mana = data['hotkeys']['mana']
limit_hp = data['limits']['hp'] 
limit_mana = data['limits']['mana']


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
    limit = 20

    while current_address < end_address:
        data = read_memory(process_handle, current_address, chunk_size)
        if data:
            for i in range(0, len(data), 4):  # Assumindo que estamos lendo valores inteiros de 4 bytes
                value = int.from_bytes(data[i:i+4], byteorder='little', signed=False)
                if value == target_value:
                    print(f"{hex(current_address + i)}")
                    found_addresses.append((current_address + i))
                    founded_counter+=1
        current_address += chunk_size
        if(founded_counter>=limit):
            break

    if not found_addresses:
        print("Valor não encontrado.")
        return None

    return found_addresses

def enderecos_proximos(valor_x, enderecos, margem=500):
    enderecos_proximos = []
    
    for endereco in enderecos:
        # Lê o valor na memória no endereço especificado
        valor_na_memoria = getAddressValue(endereco)
        # Verifica se o valor está dentro da margem de x
        if (valor_na_memoria != valor_x) and (valor_x - valor_na_memoria < margem):
            enderecos_proximos.append(endereco)
    
    return enderecos_proximos

#Inicio    
pid = get_pid_by_name(process_name)

if pid is None:
    print(f"Processo '{process_name}' não encontrado.")
else:
    print(f"PID do processo '{process_name}': {pid}")

    process_handle = ctypes.windll.kernel32.OpenProcess(0x0010, False, pid) #read only permission

    if not process_handle:
        print("Falha ao abrir o processo.")
        exit()
    print(f"Processo {pid} aberto com sucesso.")

    # Obtendo parametros
    # hp_input = input("Digite seu HP: ")
    # mana_input = input("Digite sua Mana: ")
    hp_input = 4850
    mana_input = 1525
    print("Aguarde...")

    listHpAddr1 = scan_addresses(hp_input)
    listManaAddr1 = scan_addresses(mana_input)

    print("ATENÇÃO, CALIBRAGEM! Perca um pouco de HP e Mana.")
    input("Aperte ENTER quando finalizar a calibragem...")

    os.system('clear')  # Para Linux/macOS

    listHpAddr2 = enderecos_proximos(hp_input, listHpAddr1)
    listManaAddr2 = enderecos_proximos(mana_input, listManaAddr1)

    address_hp = listHpAddr2[0]
    address_mana = listManaAddr2[0]

    while True:
        hp = getAddressValue(address_hp)
        mana = getAddressValue(address_mana)

        print(f"hp:{hp}  |  mana:{mana}", end="\r", flush=True)
        
        # if hp < total_hp * (limit_hp/100):
        #     #print("enviando hotkey_hp...")
        #     keyboard.press(hotkey_hp)
        
        # if mana < total_mana * (limit_mana/100):
        #     #print("enviando hotkey_mana...")
        #     keyboard.press(hotkey_mana)

        time.sleep(0.5)
        #closes
    ctypes.windll.kernel32.CloseHandle(process_handle)