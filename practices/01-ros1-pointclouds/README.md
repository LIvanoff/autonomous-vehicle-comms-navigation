# Практика 1. Верните облаку правильную ориентацию

**ROS 1 Noetic · Python 3 · 90 минут.**

Вам выдан короткий ROS 1 bag с реальными данными лидара Ouster. Во все облака внесён один и тот же неизвестный поворот. Нужно написать ноду, которая получает `PointCloud2`, поворачивает координаты точек и публикует исправленное облако. Углы подбираются по изображениям или RViz.

Полное задание с формулами, порядком поворотов, подсказками и требованиями к результату находится в **[assignment.html](assignment.html)**. После клонирования откройте этот файл в браузере: GitHub показывает HTML как исходный код.

## Что подготовить

- Docker Desktop с Linux-контейнерами и командой `docker compose` либо Docker Engine с Compose на Linux.
- Индивидуальный `input.bag`, полученный от преподавателя. Положите его в эту папку, рядом с `compose.yaml`.
- Редактор Python-кода. ROS устанавливается внутри Docker; GPU, X11 и RViz для основного сценария не нужны.

Все команды ниже запускайте из `practices/01-ros1-pointclouds`. Они подходят для PowerShell и Linux shell. Первую сборку образа выполните **до занятия**: она требует доступа к интернету.

## 1. Соберите окружение и посмотрите исходные данные

```sh
docker compose build
docker compose run --rm lab bash -lc "source /opt/ros/noetic/setup.bash && rosbag info input.bag"
docker compose run --rm lab bash -lc "source /opt/ros/noetic/setup.bash && python3 preview.py input.bag --out output/before"
```

Откройте `output/before/index.html` обычным браузером на своём компьютере. Рядом сохраняются PNG и `animation.gif`. Отрисовка работает без графического экрана контейнера.

## 2. Напишите ноду

Функции `rotation_matrix()` и `correct_points()` в [student_node.py](student_node.py) уже реализованы: они строят матрицу поворота и применяют её к конечным координатам, сохраняя остальные строки массива.

Заполните два `TODO`:

1. Создайте ROS Publisher и Subscriber по контракту сообщений ниже.
2. В callback используйте готовые функции, чтобы прочитать координаты, повернуть их, сформировать и опубликовать исправленное сообщение.

До выполнения `TODO` запуск ноды намеренно выдаёт `NotImplementedError`. Функции чтения и упаковки `PointCloud2` уже даны в `cloud_io.py`.

В [config.yaml](config.yaml) задаются **углы вашей коррекции** в градусах. Они не являются известными углами искажения. Подробное объяснение матриц и подбора углов — в разделах 3–4 [полного задания](assignment.html).

## 3. Проверьте и запустите

Тесты геометрии можно запустить сразу — они проверяют предоставленные функции поворота и должны проходить до выполнения `TODO`:

```sh
docker compose run --rm lab bash -lc "source /opt/ros/noetic/setup.bash && python3 -m unittest test_student -v"
```

Эти тесты не проверяют Publisher, Subscriber и callback. После выполнения двух `TODO` запустите обработку bag:

```sh
docker compose run --rm lab bash -lc "source /opt/ros/noetic/setup.bash && python3 run_lab.py input.bag --out output/attempt01"
```

Скрипт сам поднимет ROS master, запустит вашу ноду, проиграет bag и запишет результат:

```text
input.bag → /points_raw → ваша нода → /points_corrected → corrected.bag → PNG/GIF
```

Откройте `output/attempt01/preview/index.html`. Меняйте углы в `config.yaml` и повторяйте запуск с новой папкой: `output/attempt02`, `output/attempt03` и т. д. Предыдущие попытки сохраняются.

Для быстрого подбора можно записать результат без отрисовки всех кадров, затем построить одну картинку:

```sh
docker compose run --rm lab bash -lc "source /opt/ros/noetic/setup.bash && python3 run_lab.py input.bag --out output/attempt02 --no-preview"
docker compose run --rm lab bash -lc "source /opt/ros/noetic/setup.bash && python3 preview.py output/attempt02/corrected.bag --topic /points_corrected --out output/attempt02/preview --step 20"
```

## Требования к результату

| | Вход | Выход |
| --- | --- | --- |
| Топик | `/points_raw` | `/points_corrected` |
| Тип | `sensor_msgs/PointCloud2` | `sensor_msgs/PointCloud2` |
| Frame | `lidar_corrupted` | `lidar_level` |

- Дорога должна находиться внизу и быть примерно горизонтальной, вертикальные объекты — направлены вверх. Начало координат остаётся в лидаре, поэтому дорога не обязана лежать на `Z=0`.
- Восстановите вертикаль с допуском 3° относительно учебного эталона. Направление вокруг вертикали (`yaw`) без внешнего ориентира не оценивается.
- Сохраните `header.stamp`, количество и порядок точек, `intensity` и остальные поля сообщения.
- Поворачивайте только точки с конечными `x`, `y`, `z`; строки с `NaN`/`Inf` оставьте на месте и без изменения.
- Перенос, масштабирование, отражение, удаление точек и одна лишь смена `frame_id` не выполняют задание.

`run_check.json` проверяет число облаков и временные метки. Успешная проверка доставки сама по себе не означает, что ориентация верна.

## Что сдавать

Номер варианта, `student_node.py`, `config.yaml`, итоговый `corrected.bag`, `run_check.json`, изображения до/после и 5–8 предложений о подборе углов. Покажите две промежуточные попытки. Картинки должны соответствовать итоговой записи.

При ошибке запуска смотрите `student.log`, `recorder.log`, `player.log` и `roscore.log` в папке попытки. Другие подсказки и необязательный запуск RViz описаны в [assignment.html](assignment.html).
