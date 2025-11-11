# Video-Sent

### Uruchmienie aplikacji w dockerze

> docker-compose up --build -d

- Następnie należy wejść w kontener za pomocą aplikacji docker desktop lub za pomocą komendy:
> docker exec -it video_sent_backend bash

- Zrobić migracje i wygenerować seeda wewnątrz kontenera:
> python manage.py migrate
> 
> python manage.py seeda

- Następnie wchodzimy na http://localhost:5671 i wszystko powinno działać.
