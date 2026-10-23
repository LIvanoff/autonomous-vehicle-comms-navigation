# Организация системы связи и навигации беспилотных транспортных средств

Материалы первой части курса РТУ МИРЭА: лекции и практические задания по связи и навигации автономного транспорта.

[Страница курса в СДО МИРЭА](https://online-edu.mirea.ru/course/view.php?id=18660).

## Материалы

Опубликованы практики по работе с облаками точек и RGB-D-одометрии. Лекции будут добавляться отдельно.

| Практика | Тема | Окружение |
| --- | --- | --- |
| [01. Ориентация облака точек](practices/01-ros1-pointclouds/) | ROS-нода, `PointCloud2`, повороты координат, чтение и запись bag | ROS 1 Noetic, Python 3, Docker |
| [02. RGB-D-одометрия](practices/02-ros1-rgbd-odometry/) | Подписчики и publisher, синхронизация RGB-D, оценка движения камеры, визуализация | ROS 1 Noetic, OpenCV, Rerun, Docker |

## Как начать

```sh
git clone --depth 1 https://github.com/LIvanoff/autonomous-vehicle-comms-navigation.git
cd autonomous-vehicle-comms-navigation/practices/01-ros1-pointclouds
```

Далее следуйте [инструкции первой практики](practices/01-ros1-pointclouds/README.md). Индивидуальный `input.bag` для неё выдаётся отдельно.

Для практики по RGB-D перейдите в `practices/02-ros1-rgbd-odometry` и откройте [README](practices/02-ros1-rgbd-odometry/README.md). Учебный бэг TUM (около 75 МБ) [скачивается отдельно](https://github.com/LIvanoff/autonomous-vehicle-comms-navigation/raw/29c96ba7e98efba7c77fafe587646913174e33c1/practices/02-ros1-rgbd-odometry/data/tum_rgbd_12s.bag); сохраните его в `practices/02-ros1-rgbd-odometry/data/tum_rgbd_12s.bag`. Атрибуция и условия использования данных приведены в её `data/README.txt`.

Если Git не установлен, скачайте репозиторий через **Code → Download ZIP** и распакуйте архив. Он содержит код и инструкции; бэг загружается отдельно. Для Git используйте приведённый выше `--depth 1`, чтобы не скачивать старые версии с данными.

Для основной части практики достаточно Docker с Linux-контейнерами. Установка ROS на компьютер, GPU, RViz и X11 не требуются.
