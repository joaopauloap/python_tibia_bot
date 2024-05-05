import ctypes
import psutil
import time

process_name = "client.exe"

hotkey_hp = 0x71    #f2
hotkey_mana = 0x73  #f4

limit_hp = 75 
limit_mana = 50


address_hp_total = 0x0A1FDBD8 #verificar
address_hp_current = 0x0A1FDBD0
address_mana_total = 0x08E67320 #verificar
address_mana_current = 0x0A1FE0F0

def get_pid_by_name(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            return proc.info['pid']
    return None

def pressKey(key):
    ctypes.windll.user32.keybd_event(key, 0, 0, 0)  # Pressiona a tecla
    ctypes.windll.user32.keybd_event(key, 0, 2, 0)  # Libera a tecla
    return None

def getAddressValue(address):
    buffer = ctypes.c_int()
    if ctypes.windll.kernel32.ReadProcessMemory(process_handle, address, ctypes.byref(buffer), ctypes.sizeof(buffer), None):
        return buffer.value
    else:
        print(f"Erro ao tentar ler o endereço {hex(address)}")
    return buffer.value

pid = get_pid_by_name(process_name)

if pid is None:
    print(f"Processo '{process_name}' não encontrado.")
else:
    print(f"PID do processo '{process_name}': {pid}")

    process_handle = ctypes.windll.kernel32.OpenProcess(0x0010, False, pid) #read only permission

    if not process_handle:
        print("Falha ao abrir o processo")
    else:
        print(f"Processo {pid} aberto com sucesso: handle {process_handle}")

        while True:
            hp_total = getAddressValue(address_hp_total)
            hp_current = getAddressValue(address_hp_current)
            mana_total = getAddressValue(address_mana_total)
            mana_current = getAddressValue(address_mana_current)
            
            if hp_current < hp_total * (limit_hp/100):
                print("enviando hotkey_hp...")
                pressKey(hotkey_hp)
            
            if mana_current < mana_total * (limit_mana/100):
                print("enviando hotkey_mana...")
                pressKey(hotkey_mana)

            print(f"hp:{hp_current}")
            print(f"mana:{mana_current}\n")
            time.sleep(1)
        #closes
        ctypes.windll.kernel32.CloseHandle(process_handle)