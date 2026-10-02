# Организация системы связи и навигации беспилотных транспортных средств

Материалы первой части курса РТУ МИРЭА: лекции и практические задания по связи и навигации автономного транспорта.

[Страница курса в СДО МИРЭА](https://online-edu.mirea.ru/course/view.php?id=18660).

## Материалы

Сейчас опубликована только первая практика. Лекции будут добавляться отдельно.

| Практика | Тема | Окружение |
| --- | --- | --- |
| [01. Ориентация облака точек](practices/01-ros1-pointclouds/) | ROS-нода, `PointCloud2`, повороты координат, чтение и запись bag | ROS 1 Noetic, Python 3, Docker |

## Как начать

```sh
git clone https://github.com/LIvanoff/autonomous-vehicle-comms-navigation.git
cd autonomous-vehicle-comms-navigation/practices/01-ros1-pointclouds
```

Далее следуйте [инструкции практики](practices/01-ros1-pointclouds/README.md).
Индивидуальный `input.bag` выдаёт преподаватель отдельно; в репозитории записей нет.

Для основной части практики достаточно Docker с Linux-контейнерами. Установка ROS на компьютер, GPU, RViz и X11 не требуются.
