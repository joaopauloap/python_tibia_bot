import ctypes
from ctypes import wintypes 
import psutil
import json
import keyboard
import time
import os

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
    start_address = 0x0A000000
    end_address = 0x0FFFFFFF
    chunk_size = 4096
    current_address = start_address
    found_addresses = []
    founded_counter = 0
    limit = 100

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
print("Atenção: Sua MANA deve estar cheia para a macro funcionar.") 
hp_input = int(input("Digite seu HP total: "))
mana_input = int(input("Digite sua Mana total: "))
print("Aguarde...")

listManaAddr1 = scan_addresses(mana_input)
# print(f"listManaAddr1: {listManaAddr1}")
if len(listManaAddr1) == 0:
    print("Erro: Não foi possível localizar os endereços! Sua MANA estava cheia?")
    exit()

print("ATENÇÃO, CALIBRAGEM! Gaste um pouco de MANA...")

mana_addr = 0
listFoundedAddr = []
margin = 500

while(mana_addr == 0):
    for addr in listManaAddr1:
        addrValue = getAddressValue(addr)
        # print(f"addr:{addr} - value: {addrValue}")
        if (addrValue < mana_input): 
            listFoundedAddr.append(addr)
    if(len(listFoundedAddr)>0):
        mana_addr = min(listFoundedAddr)
    time.sleep(0.1)

# print(f"listFoundedAddr: {listFoundedAddr}")
# print(f"mana_addr: {mana_addr}")


hp_addr = mana_addr - 1312 #Teste: Localiza endereço do hp apartir do da mana

os.system('cls')

while True:
    hp = getAddressValue(hp_addr)
    mana = getAddressValue(mana_addr)
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