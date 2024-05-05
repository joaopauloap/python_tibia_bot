import ctypes
import psutil
import json
import keyboard
import time

with open('config.json', 'r') as file:
    data = json.load(file)

hotkey_hp = data['hotkeys']['hp']
hotkey_mana = data['hotkeys']['mana']
limit_hp = data['limits']['hp'] 
limit_mana = data['limits']['mana']
total_mana = data['total']['mana']
total_hp = data['total']['hp']

process_name = "client.exe"

address_hp_current = 0x0A00DBD0     
address_mana_current = 0x0A00E0F0


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


    #procurando address_hp_current    
    for xbyte in range(256):
        addrHP = (address_hp_current & 0xFF00FFFF) | (xbyte << 16)        
        if getAddressValue(addrHP) == total_hp:
            print(f"address_hp_current: {hex(addrHP)}")
            address_hp_current = addrHP
            break

    #procurando address_mana_current    
    for xbyte in range(256):
        addrMana = (address_mana_current & 0xFF00FFFF) | (xbyte << 16)        
        if getAddressValue(addrMana) == total_mana:
            print(f"address_mana_current: {hex(addrMana)}")
            address_mana_current = addrMana
            break


    while True:
        hp = getAddressValue(address_hp_current)
        mana = getAddressValue(address_mana_current)

        print(f"hp:{hp}  |  mana:{mana}", end="\r", flush=True)
        
        if hp < total_hp * (limit_hp/100):
            #print("enviando hotkey_hp...")
            keyboard.press(hotkey_hp)
        
        if mana < total_mana * (limit_mana/100):
            #print("enviando hotkey_mana...")
            keyboard.press(hotkey_mana)

        #closes
    ctypes.windll.kernel32.CloseHandle(process_handle)