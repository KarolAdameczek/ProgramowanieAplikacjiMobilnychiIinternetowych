# Trzeci kamień milowy

**Na początek chciałbym zaznaczyć, że zauważyłem, iż ktoś oprócz mnie korzystał z mojej bazy danych, tj. numer 13 w Pańskim Redisie, więc prosiłbym, żeby wykonał Pan FLUSHDB na tej bazie przed rozpoczęciem testowania, aby nie wystąpiły błędy związane ze stosowaniem innego formatu danych przez drugą osobę.**



URL Web Service'u: https://salty-chamber-75999.herokuapp.com

URL Klienta Nadawcy: https://thawing-badlands-56407.herokuapp.com



## Sposób korzystania z klienta dla kuriera:

Aby aplikacja zadziałała poprawnie, przed rozpoczęciem pracy z nią należy doinstalować biblioteki dotenv oraz requests za pomocą (uruchomione w folderze courier):

```
python3 -m pip install -r requirements.txt
```

lub bezpośrednio

```
python3 -m pip install python-dotenv requests
```



Następnie aplikację uruchamia się za pomocą:

```
python3 kurier.py
```



W aplikacji dostępne są następujące polecenia:

help - lista dostępnych operacji
labels - wyświetla listę wszystkich etykiet
makepackage <id> - tworzy paczkę na podstawie etykiety o danym id
incrementpackagestatus <id> - zmienia status paczki o danym id na następny, tj. z "w drodze" na "dostarczona" lub z "dostarczona" na "odebrana"
setpackagestatus <id> <status> - zmienia status paczki o danym id na wybrany status, dostępne statusy: moving, delivered, receiverd
exit - zamyka program



Każde polecenie oprócz exit wyświetla jakąś treść na ekran gdy kończy działanie.



Karol Adameczek 299231