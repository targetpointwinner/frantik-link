# frantik.by — Telegram-бот подписки и рассылки

Собирает подписчиков (кто нажал «Подписаться в Telegram» на сайте) и позволяет делать по ним рассылку: поступления школьной формы, новинки, «приехал нужный размер».

## 1. Создать бота
1. Открой в Telegram **@BotFather** → `/newbot` → задай имя и username (например `frantikby_bot`).
2. BotFather пришлёт **токен** вида `123456:AA...` — сохрани.
3. Узнай **свой user id**: напиши боту **@userinfobot**, он пришлёт число (это `ADMIN_ID`).

## 2. Вставить ссылку на сайт
В `index.html` найди кнопку `id="tgBtn"` и подставь username бота:
```
href="https://t.me/ВАШ_БОТ?start=site"
```
(например `https://t.me/frantikby_bot?start=site`).

## 3. Задеплоить (Railway)
1. На railway.app → New Project → Deploy from GitHub → выбери репозиторий, **Root Directory = `bot`**.
2. Variables:
   - `BOT_TOKEN` = токен из BotFather
   - `ADMIN_ID` = твой user id
   - `SITE_URL` = адрес сайта (например `https://frantik.netlify.app`)
   - `DB_PATH` = `/data/subscribers.json`
3. Добавь **Volume** и смонтируй на `/data` — иначе список подписчиков сбросится при передеплое.
4. Deploy. В логах должно быть `frantik bot started`.

Локально для теста:
```
cd bot && pip install -r requirements.txt
BOT_TOKEN=xxx ADMIN_ID=123 python bot.py
```

## 4. Как рассылать
Пиши эти команды **самому боту** (ты как ADMIN):
- **`/send Привет! Завезли новую школьную форму — ждём в Тивали 🎒`** — текстовая рассылка всем.
- **Фото/видео с подписью, начинающейся со слова `рассылка`** — разошлёт медиа всем. Пример подписи: `рассылка Новинки уже в магазинах!`
- **`/stats`** — сколько сейчас подписчиков.

Пользователи подписываются сами: нажимают кнопку на сайте → бот открывается → жмут Start.
Отписка — команда `/stop`.
