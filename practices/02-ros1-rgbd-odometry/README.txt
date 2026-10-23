Практика: RGB-D-одометрия в ROS 1

Полная инструкция: README.md или assignment.html. Код писать только здесь:
catkin_ws/src/rgbd_vo_lab/scripts/student_node.py
Четыре TODO. Готовая математика не требует изменений.

Скачайте бэг отдельно и сохраните как data/tum_rgbd_12s.bag:
https://github.com/LIvanoff/autonomous-vehicle-comms-navigation/raw/29c96ba7e98efba7c77fafe587646913174e33c1/practices/02-ros1-rgbd-odometry/data/tum_rgbd_12s.bag

До занятия: Docker Desktop (Linux containers), готовые образы и bag.
GPU, Git, Python на хосте и X11 не нужны.
Сборка образов из папки с compose.yaml:
  docker compose build

Терминал 1 (компьютер):
  docker compose run --rm lab bash
Далее внутри контейнера:
  source /opt/ros/noetic/setup.bash
  cd /lab/catkin_ws
  catkin_make -j2
  source devel/setup.bash
  cd /lab
После заполнения TODO:
  python3 run_lab.py data/tum_rgbd_12s.bag --out output/attempt01

Терминал 2 (компьютер, папка практики):
  docker compose run --rm --service-ports viewer python viewer/show.py output/attempt01 --serve
  http://localhost:9090/?url=rerun%2Bhttp%3A%2F%2Flocalhost%3A9876%2Fproxy
Ctrl+C останавливает viewer. Перед повторным просмотром остановите предыдущий viewer.

На Windows редактируйте student_node.py в обычном редакторе. Сохранённый файл
сразу доступен контейнеру. Используйте UTF-8. Выход из ROS-контейнера: exit.
Папки попыток не перезаписываются. Для повтора используйте attempt01_retry и т. д.

Это учебная RGB-D-одометрия (ORB + PnP), не полноценный SLAM.
Масштаб даёт измеренная глубина TUM. Эталон алгоритму не передаётся.
Полная исходная последовательность не нужна студентам; готовый учебный bag скачивается отдельно по ссылке выше.

Источник данных: TUM RGB-D, freiburg1_xyz
https://cvg.cit.tum.de/data/datasets/rgbd-dataset
https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats
Лицензия датасета: CC BY 4.0 (см. data/README.txt).
