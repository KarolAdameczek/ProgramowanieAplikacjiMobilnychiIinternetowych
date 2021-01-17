# Czwarty kamień milowy

**Na początek chciałbym zaznaczyć, że zauważyłem, iż ktoś oprócz mnie korzystał z mojej bazy danych, tj. numer 13 w Pańskim Redisie, więc prosiłbym, żeby wykonał Pan FLUSHDB na tej bazie przed rozpoczęciem testowania, aby nie wystąpiły błędy związane ze stosowaniem innego formatu danych przez drugą osobę.**



URL Web Service'u: https://safe-anchorage-72362.herokuapp.com/

URL Klienta Nadawcy: https://gentle-headland-67122.herokuapp.com/

URL Socketu Powiadomień: https://powerful-coast-14541.herokuapp.com/



Dane do logowania w auth0 znajdują się w pliku **pass.txt**.



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



Po uruchomieniu aplikacja prosi o podanie emaila oraz hasła (hasło jest ukrywane). Dane do zalogowania można znaleźć w pliku **pass.txt**.



W aplikacji dostępne są następujące polecenia:

help - lista dostępnych operacji
labels - wyświetla listę wszystkich etykiet
makepackage <id> - tworzy paczkę na podstawie etykiety o danym id
incrementpackagestatus <id> - zmienia status paczki o danym id na następny, tj. z "w drodze" na "dostarczona" lub z "dostarczona" na "odebrana"
setpackagestatus <id> <status> - zmienia status paczki o danym id na wybrany status, dostępne statusy: moving, delivered, receiverd
exit - zamyka program



Każde polecenie oprócz exit wyświetla jakąś treść na ekran gdy kończy działanie.



## Powiadomienia

Powiadomienia wykorzystują flask-socketio. Rozsyłane są co około 5 sekund. Wyświetlane są po zalogowaniu w Kokpicie i informują o stworzeniu paczki lub zmianie statusu paczki powiązanej z posiadanymi etykietami.

Aby przetestować powiadomienia:

1. Zaloguj się w aplikacji klienckiej https://gentle-headland-67122.herokuapp.com/sender/login
   1. jeśli chcesz korzystać z logowania tradycyjnego, należy na początek się zarejestrować tutaj https://gentle-headland-67122.herokuapp.com/sender/register
   2. w przypadku logowania przez auth0, rejestracja nie jest wymagana, wystarczy zalogować się swoim kontem auth0 lub kontem google i konto jest rejestrowane automatycznie
2. Po zalogowaniu zostaniesz przekierowany do kokpitu - wpisz imię i nazwisko przykładowego adresata, wybierz parametry paczki i kliknij przycisk generuj, stworzona zostanie nowa etykieta.
3. Zaloguj się w aplikacji kuriera jw.
4. Poleceniem *makepackage id_etykiety* stwórz paczkę - id etykiety skopiuj z przeglądarki lub wykorzystaj polecenie *labels* i skopiuj id stworzonej etykiety znalezionej na podstawie jej parametrów
5. Jeśli wszystko przebiegnie poprawnie, to w aplikacji kurierskiej wyświetli się odpowiedź "Sukces" i po chwili odpowiednie powiadomienie pojawi się w aplikacji nadawcy
6. Poleceniem incrementpackagestatus id_etykiety/paczki zmień status paczki - wykorzystaj ponownie wcześniejsze id
7. Ponownie, wyświetli się "Sukces" i po chwili wyświetli się odpowiednie powiadomienie



Karol Adameczek 299231



