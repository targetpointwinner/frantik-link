# Аналитика frantik.by

Сайт пишет события (клики, виджеты, избранное, календарь, отзывы) в Firebase Realtime Database, а `admin.html` их показывает.

## 1. Создать базу (Firebase, бесплатно, ~3 мин)
1. https://console.firebase.google.com → **Add project** (можно без Google Analytics).
2. Слева **Build → Realtime Database → Create Database** → регион Europe → **Start in locked mode**.
3. Скопируй **URL базы** сверху, вид: `https://ИМЯ-default-rtdb.europe-west1.firebasedatabase.app` (или `...firebaseio.com`).

## 2. Вставить URL в 2 файла
В `index.html` и `admin.html` найди строку и подставь свой URL:
```js
const FB_URL="https://ИМЯ-default-rtdb.firebaseio.com";
```

## 3. Правила базы
Вкладка **Rules** → вставь и **Publish**:
```json
{
  "rules": {
    "analytics": {
      "events": {
        ".read": true,
        ".write": true,
        "$id": { ".validate": "newData.hasChildren(['t','e','v'])" }
      }
    }
  }
}
```
Данные обезличенные (визитор = случайный id устройства, без имён/телефонов), поэтому публичный доступ к `/analytics` некритичен. Сама админка закрыта секретным ключом.

## 4. Открыть админку
Ссылка (секрет задаётся в `admin.html`, переменная `SECRET`, по умолчанию `fr-9x2k7m`):
```
https://ТВОЙ-САЙТ/admin.html?key=fr-9x2k7m
```
Смени `SECRET` на свой, чтобы ссылку не подобрали.

## Что видно в админке
- KPI: визиты, уникальные, события, сохранения ♥, добавления в календарь, запросы в Telegram
- График по дням, разбивка по всем типам событий
- Клики по каждому магазину (карта/звонок)
- Топ сохранённых карточек (с превью)
- Лента по каждому посетителю (что делал, «горячие» действия подсвечены)
- Фильтр: сегодня / 7 / 30 дней / всё
- **«Скопировать сводку»** — готовый текст, чтобы прислать разработчику для доработок

## Отслеживаемые события
visit, cta_catalog, store_map, store_call, widget_finder, finder_geo, finder_search, finder_result,
calendar_add, fav_add, fav_remove, fav_show, fav_prompt, fav_send, catalog_tab, catalog_more,
photo_view, story_view, tg_subscribe.
