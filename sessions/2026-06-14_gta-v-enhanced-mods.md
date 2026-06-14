# GTA V Enhanced mods — session summary

Дата: 2026-06-14

## Что сделали

- GTA V Enhanced находится в `C:\Download\Grand.Theft.Auto.V.Enhanced-InsaneRamZes\`.
- Версия игры: `GTA5_Enhanced.exe 1.0.1013.34`.
- Пользователь просил single-player моддинг: в первую очередь онлайн-контент в story mode, качественные машины с нормальными повреждениями/handling, оружие, прически, одежду, звуки и immersive-детали; графика и визуал вторым/третьим слоем, без тяжелого RT из-за RTX 3060 Laptop 6 GB VRAM.
- Игра не запускалась Codex; запуск и проверку делал пользователь.

## Поставлено

- ScriptHookV `3788.0/1013.34`.
- Официальный Enhanced ASI loader `xinput1_4.dll`.
- `dinput8.dll`.
- `args.txt` с `-nobattleye -noBE`.
- `NativeTrainer.asi` для теста через `F4`.
- Menyoo 2.0, открывается `F8`.
- Add-On Vehicle Spawner, открывается `F5` или читом `addonspawner`.
- ScriptHookVDotNet Enhanced.
- All MP Vehicles in SP.
- RageOpenV.
- HeapAdjuster Enhanced.
- Packfile Limit Adjuster Enhanced.
- Modkit Limit Adjuster Enhanced.

## Важные фиксы

- Изначально моды не работали, потому что был установлен не полный комплект ScriptHookV: не хватало `args.txt` и официального Enhanced ASI loader из `bin`.
- После фикса скопирован полный комплект из `bin` архива ScriptHookV.
- `GTA5_Enhanced_BE.exe` отключен обратимо: переименован в `GTA5_Enhanced_BE.exe.codex-disabled`, чтобы игра не уходила в BattlEye-ветку.
- Со всей папки игры снят Windows `Zone.Identifier`.
- Финальная проверка без запуска игры лежит в `_codex_modding\verification-final-no-launch.txt`.
- Пользователь подтвердил, что моды работают.

## Графика

- Stable no-RT профиль применен к `%USERPROFILE%\Documents\Rockstar Games\GTAV Enhanced\settings.xml`.
- RT/RTAO выключены, `RefreshRate=200`, `VSync=0`, `MotionBlurStrength=0`.
- Профили:
  - `_codex_modding\settings-profile-stable-no-rt.xml`
  - `_codex_modding\settings-profile-rt-lite-experiment.xml`

## Следующая задача

Предложить список модов для дальнейшей установки согласно запросам пользователя:

- приоритет 1: онлайн/DLC-контент в story mode;
- приоритет 2: качественные машины, желательно Rockstar-native или проверенные add-on, без кривых повреждений;
- приоритет 3: оружие, прически, одежда, MP-персонажи/гардероб в story mode;
- приоритет 4: звуки оружия, транспорта, окружения и мелкие immersive-детали;
- приоритет 5: графика/визуал без тяжелого RT, с учетом RTX 3060 Laptop 6 GB VRAM и 2560x1080 экрана.

Начинать следующий чат с исследования и отбора модов, а не с установки. Важно проверять Enhanced-совместимость и не ставить случайные real-life car packs, если у них плохие повреждения/handling/LOD.
