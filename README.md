# Reclamation

Подготовка сборки 2.3.2 для LANMinecraft. [Авторский клиентский выпуск](https://www.curseforge.com/minecraft/modpacks/reclamation-reclaim-the-world/files/8179107)

`tools/upstream-client-lock.json` фиксирует SHA256 и размер оригинального ZIP, ссылки на официальный источник, записи зависимостей и SHA256 файлов внутри авторских overrides. Minecraft и загрузчик взяты из оригинального манифеста. Java в `portable-pack.json` соответствует выбору текущего лаунчера для этой версии Minecraft и проверяется при запуске.

## Восстановление авторского клиента

Из корня LANMinecraft используйте `tools/PackData/CurseForge/prepare.py` с `--project-id 1302972` и `--file-id 8179107`. Укажите этот lock через `--expect` и новый каталог внутри своего стенда через `--output`. Полная подготовка проверяет все заявленные зависимости. Отдельный lock поставки и метаданные карточки готовятся после запуска и проверки фактического состава.

## Публикация

У сборки MIT. В манифесте закреплён FTB Quests, CF 289412/8078538. У FTB отдельные условия для перепубликации. [Условия](https://feed-the-beast.com/raw/docs/mod-license)
