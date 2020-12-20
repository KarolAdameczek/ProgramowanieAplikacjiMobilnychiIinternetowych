import requests
from requests import Timeout
from sys import exit
from dotenv import load_dotenv
from os import getenv

load_dotenv()

TOKEN = getenv("TOKEN")
WS_URL = getenv("WS_URL")

_package_statuses = [
    "moving",
    "delivered",
    "received"
]

def requestGet(url):
    headers = {"Authorization" : "Bearer " + TOKEN}
    try:
        res = requests.get(url, headers=headers)
    except Timeout:
        print("Nie można połączyć się z serwerem, spróbuj ponownie później")
        exit()

    if res.status_code == 500:
        print("Aplikacja jest obecnie niedostępna, spróbuj ponownie później")
        exit()
    
    if res.status_code == 401:
        print("Należy odnowić autentykację")
        exit()

    return res.json(), res.status_code

def requestPost(url, data):
    headers = {"Authorization" : "Bearer " + TOKEN}
    try:
        res = requests.post(url, json=data, headers=headers)
    except Timeout:
        print("Nie można połączyć się z serwerem, spróbuj ponownie później")
        exit()

    if res.status_code == 500:
        print("Aplikacja jest obecnie niedostępna, spróbuj ponownie później")
        exit()
    
    if res.status_code == 401:
        print("Należy odnowić autentykację")
        exit()

    return res.json(), res.status_code

def requestPut(url, data):
    headers = {"Authorization" : "Bearer " + TOKEN}
    try:
        res = requests.put(url, json=data, headers=headers)
    except Timeout:
        print("Nie można połączyć się z serwerem, spróbuj ponownie później")
        exit()

    if res.status_code == 500:
        print("Aplikacja jest obecnie niedostępna, spróbuj ponownie później")
        exit()
    
    if res.status_code == 401:
        print("Należy odnowić autentykację")
        exit()
    return res.json(), res.status_code

def requestDelete(url):
    headers = {"Authorization" : "Bearer " + TOKEN}
    try:
        res = requests.delete(url, headers=headers)
    except Timeout:
        print("Nie można połączyć się z serwerem, spróbuj ponownie później")
        exit()

    if res.status_code == 500:
        print("Aplikacja jest obecnie niedostępna, spróbuj ponownie później")
        exit()
    
    if res.status_code == 401:
        print("Należy odnowić autentykację")
        exit()

    return res.status_code

def getURL(link_list: list):
    url = WS_URL
    headers = {"Authorization" : "Bearer " + TOKEN}
    try:
        json = requests.get(WS_URL, headers=headers).json()
        for link in link_list[:-1]:
            url = WS_URL + json["_links"][link]["href"]
            json = requests.get(url, headers=headers).json()
        return WS_URL + json["_links"][link_list[-1]]["href"]
    except Exception:
        print("Błąd komunikacji z serwerem, skontaktuj się z administratorem lub spróbuj ponownie później")
        exit()
    

def processInput(args: str):
    args = args.split()
    operation = _operations.get(args[0], onIncorrectOperation)
    operation(args)

def printHelp(args):
    print("""
    help - lista dostępnych operacji
    labels - wyświetla listę wszystkich etykiet
    makepackage <id> - tworzy paczkę na podstawie etykiety o danym id
    incrementpackagestatus <id> - zmienia status paczki o danym id na następny, tj. z "w drodze" na "dostarczona" lub z "dostarczona" na "odebrana" 
    setpackagestatus <id> <status> - zmienia status paczki o danym id na wybrany status, dostępne statusy: moving, delivered, receiverd
    exit - zamyka program
    """)

def printLabels(args):
    url = getURL(["labels"])
    data, code = requestGet(url)

    if code >= 400 and code < 500:
        print("Aplikacja napodkała problem, skontaktuj się z administratorem i opisz problem")
        exit()

    for item in data["items"]:
        if "id" in item and "person" in item and "destination" in item and "size" in item and "state" in item:
            print("ID:", item["id"])
            print("\tOdbiorca:", item["person"])
            print("\tMiejsce docelowe:", item["destination"] )
            print("\tRozmiar:", item["size"] )
            print("\tStatus:", item["state"] )

    return

def makePackage(args):
    if len(args) != 2:
        print("Podano nieodpowiednią liczbę argumentów, sprawdź polecenie help")
        return

    url = getURL(["packages"])
    
    data, code = requestPost(url, data= {"id" : args[1]})
    if code == 400:
        print(data["error"])
        return

    if code == 200:
        print("Sukces")
        return

def incrementPackageStatus(args):
    if len(args) != 2:
        print("Podano nieodpowiednią liczbę argumentów, sprawdź polecenie help")
        return

    url = getURL(["packages", "package:info"])
    url = url.format(id= args[1])
    
    data, code = requestGet(url)

    if code == 400:
        print("Nie ma paczki o takim id")
        return
    elif code != 200:
        print("Niespodziewany błąd, skontaktuj się z administratorem")
        exit()
    
    try:
        i = _package_statuses.index(data["item"]["status"])
    except Exception as e:
        print(e)
        print("Niespodziewany błąd, skontaktuj się z administratorem")
        exit()

    if i == len(_package_statuses) - 1:
        print("Status ten paczki nie może być zmieniony, ponieważ paczka została odebrana. Użyj polecenia setpackagestatus, żeby zmienić status na dowolny.")
        return

    data, code = requestPut(WS_URL + data["_links"]["package:update"]["href"], data={"status" : _package_statuses[i + 1]})

    if code != 200:
        print("Niespodziewany błąd, skontaktuj się z administratorem")
        exit()
    
    print("Sukces")
    return

def setPackageStatus(args):
    if len(args) != 3:
        print("Podano nieodpowiednią liczbę argumentów, sprawdź polecenie help")
        return
    
    if args[2] not in _package_statuses:
        print("Niepoprawny status:", args[2])
        return

    url = getURL(["packages", "package:info"])
    url = url.format(id= args[1])

    data, code = requestGet(url)
    if code == 400:
        print("Nie ma paczki o takim id")
        return
    elif code != 200:
        print("Niespodziewany błąd, skontaktuj się z administratorem")
        exit()

    data, code = requestPut(WS_URL + data["_links"]["package:update"]["href"], data= {"status" : args[2]})

    if code != 200:
        print("Niespodziewany błąd, skontaktuj się z administratorem")
        exit()
    
    print("Sukces")
    return

def onIncorrectOperation(args):
    print("""
    Nie znaleziono takiej operacji
    """)

def main():
    while True:
        args = input()
        if args == "exit":
            break
        processInput(args)


_operations = {
    "help" : printHelp,
    "labels" : printLabels,
    "makepackage" : makePackage,
    "incrementpackagestatus" : incrementPackageStatus,
    "setpackagestatus" : setPackageStatus
}

if __name__ == "__main__":
    main()
