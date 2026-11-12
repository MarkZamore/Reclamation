# Reclamation

Подготовка сборки 2.3.2 для LANMinecraft. [Авторский клиентский выпуск](https://www.curseforge.com/minecraft/modpacks/reclamation-reclaim-the-world/files/8179107)

`tools/upstream-client-lock.json` фиксирует SHA256 и размер оригинального ZIP, ссылки на официальный источник, записи зависимостей и SHA256 файлов внутри авторских overrides. Minecraft и загрузчик взяты из оригинального манифеста. Java в `portable-pack.json` соответствует выбору текущего лаунчера для этой версии Minecraft и проверяется при запуске.

## Восстановление авторского клиента

Закреплённый авторский клиент CurseForge использует project ID 1302972 и file ID 8179107.
Для подготовки текущего кандидата из корня LANMinecraft запустите:

```powershell
python -B tools/PackData/CurseForge/release_overlay.py stage --pack-source LocalSources/Reclamation --output $stage
```

`tools/overlay.json` сохраняет политику открытия мира через Steam. Для нового авторского выпуска снимите отдельную квитанцию через `prepare.py --client-only` и проверьте её командой `release_overlay.py review-update`. При изменении защищённого входа пересмотрите рецепт и закрепите новые точные байты. После нативной проверки сохраните полный `tools/upstream-lock.json` и выполните `release_overlay.py verify` по готовому манифесту.

`tools/curseforge-fallbacks.json` закрепляет два обязательных JAR с пустыми метаданными CurseForge. Страницы выпусков подтверждают имена файлов и их ID. Полные потоки с официального CDN совпали по SHA256 с членами `mods/` официального серверного архива 2.3.2. ZIP-диапазоны также проверены по CRC32. [WATERMeDIA](https://www.curseforge.com/minecraft/mc-mods/watermedia/files/7999277) · [WATERMeDIA Binaries](https://www.curseforge.com/minecraft/mc-mods/watermedia-binaries/files/7436617) · [Серверный архив Reclamation 2.3.2](https://www.curseforge.com/minecraft/modpacks/reclamation-reclaim-the-world/files/8197450)

| Project ID / file ID | JAR | Байты | CRC32 |
|---|---|---:|---|
| 869524 / 7999277 | `watermedia-3.0.0.16.jar` | 1512980 | `dcdf3be4` |
| 1029438 / 7436617 | `wm_binaries-3.0.0-rc.1.jar` | 179378119 | `b177b638` |

## Публикация

У сборки MIT. В манифесте закреплён FTB Quests, CF 289412/8078538. У FTB отдельные условия для перепубликации. [Условия](https://feed-the-beast.com/raw/docs/mod-license)

Пользователь подтвердил наличие разрешения на перезалив. Публикация следует после проверки полного состава и нативной приёмки.
