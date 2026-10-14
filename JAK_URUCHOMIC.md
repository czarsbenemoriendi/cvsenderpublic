# Jak uruchomić panel CVSender

Panel działa jako lokalny serwer Python (bez zależności zewnętrznych) i jest
dostępny pod adresem: **http://127.0.0.1:8765**

## Sprawdź, czy już działa

```bash
lsof -i :8765
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/
```

- Jeśli `lsof` nic nie pokazuje → serwer nie działa, uruchom go (patrz niżej).
- Jeśli `lsof` coś pokazuje, ale `curl` nie zwraca `200` → proces jest
  "zawieszony" (zombie, port zajęty ale nie odpowiada). Ubij go po PID z
  `lsof` (`kill <PID>`, a jeśli nie reaguje: `kill -9 <PID>`) i uruchom
  ponownie.

## Uruchomienie

Z katalogu głównego repo (tam gdzie leży ten plik):

```bash
cd frontend
nohup python3 server.py > /tmp/cvsender_server.log 2>&1 &
disown
```

Potem otwórz w przeglądarce: http://127.0.0.1:8765

## Zatrzymanie

```bash
lsof -i :8765          # znajdź PID
kill <PID>
```

## Uwaga

To zwykły `python3 server.py` uruchomiony w tle — nie ma menedżera procesów
(np. `launchd`/`systemd`), więc po restarcie komputera trzeba go uruchomić
ręcznie tym samym poleceniem co wyżej.
