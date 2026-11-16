# Экран предупреждения при входе в сетевую игру

В Reclamation 2.3.2 используется Minecraft 1.20.1 и Forge 47.4.0.
TitleScreen читает skipMultiplayerWarning в обработчике штатной кнопки
и выбирает SafetyScreen или JoinMultiplayerScreen. Исходная сборка не
включает штатный флаг пропуска.

Клиентский Mixin Reclamation Multiplayer 1.0.0 подставляет значение true
при единственном чтении штатного флага в обработчике этой кнопки. Поле
Options и options.txt не меняются. Проверка доступности кнопки для
аккаунта, экран Realms и отдельные уведомления No Chat Reports остаются
в своих исходных путях. Мод не регистрирует сетевых каналов.

Названия методов закреплены по Forge 47.4.0. При смене Minecraft или
Forge проверьте байткод штатного обработчика, единственную точку внедрения
и поддерживаемую матрицу в mods.toml. Проверьте запуск без options.txt и
запуск поверх существующего профиля, где skipMultiplayerWarning:false.
Кнопка в обоих случаях должна открывать JoinMultiplayerScreen, а значение
параметра в памяти должно остаться false.

Сборка из рабочего репозитория:

    pwsh -File tools/multiplayer-warning/Build.ps1 -Libraries <shared-libraries> -WorkDirectory <isolated-build-directory>

Каталог WorkDirectory должен быть выделен внутри текущего стенда QA.
На выходе получается mods/reclamation-multiplayer-1.0.0.jar. Обновление
включается в манифест при штатной подготовке небольших дополнений через
tools/keybinds/stage_release.py. Проверьте размер, SHA-256 и член архива
по свежему манифесту pack-latest.

Постоянный слой закреплён в policy.json. Полная подготовка через
tools/prepare_release.py переносит его на каждый поддерживаемый авторский
выпуск независимо от наличия или состояния options.txt. Подготовка
проверяет размер и SHA-256 JAR, запись манифеста и байты внутри архива.

Для проверки опубликованного выпуска скачайте фактический архив дополнения
по манифесту и выполните:

    python -B tools/keybinds/stage_release.py <manifest> <asset-directory> --verify-warning
